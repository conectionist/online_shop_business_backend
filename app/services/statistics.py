"""Aggregations for the admin statistics page.

Conventions shared by every function here:
- Periods are expressed as a set of lists (delivery rounds). A list belongs to a
  period by its delivery date (``liste.data``), so a list is never split.
- Only non-deleted lists that received at least one order take part.
- Revenue is product revenue only: sum(pret_produs * cantitate_produs), whole RON.
- stoc_produs is an availability flag, not a stock count: the admin's toggle stores 0
  for "unavailable" and null for available, and nothing counts it down. A product
  marked unavailable after it had orders in a list sold out there; one marked
  unavailable without orders was never on sale in that list.
- A customer is identified by phone number (last 9 digits) and falls back to the
  normalized name; orders without a phone inherit the phone last used with the
  same name.

Shop volume is small, so per-order rows are loaded once and rolled up in Python.
"""

from collections import defaultdict
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta, timezone
import re
from typing import Dict, Iterable, List, Optional, Set, Tuple

from fastapi import HTTPException, status
from sqlalchemy import and_, func, or_
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.models.category import Category
from app.models.delivery_type import DeliveryType
from app.models.list import List as ListModel
from app.models.list_product_ordered import ListProductOrdered
from app.models.modalitati_plata import ModalitatiPlata
from app.models.order import Order as OrderModel
from app.models.order_item import OrderItem as OrderItemModel
from app.models.product import Product
from app.models.unitati import Unitati
from app.schemas.statistics import (
    BreakdownSlice,
    CategoryStat,
    CurrentListInfo,
    CurrentListStats,
    CustomerStat,
    CustomerStatsResponse,
    HeatmapCell,
    ListStatsPoint,
    PreviousListInfo,
    ProductSellOut,
    ProductStat,
    ProductStatsResponse,
    SoldOutProduct,
    StatsOverview,
    StatsPeriod,
    StatsSummary,
    UnsoldProduct,
)
from app.utils.text_matching import normalize_name_for_matching


# ---------------------------------------------------------------------------
# Time zone helpers
# ---------------------------------------------------------------------------

def _last_sunday(year: int, month: int) -> date:
    # Last day of month, then step back to Sunday (weekday 6)
    next_month = date(year + (month // 12), month % 12 + 1, 1)
    last_day = next_month - timedelta(days=1)
    return last_day - timedelta(days=(last_day.weekday() - 6) % 7)


def _utc_to_romania(dt: datetime) -> datetime:
    """Convert a naive UTC datetime (as stored for data_plasarii) to Romanian local time.

    Uses the EU rule (EET/EEST, switching at 01:00 UTC on the last Sunday of March
    and October) so it does not depend on tzdata being installed in the image.
    """
    if dt.tzinfo is not None:
        dt = dt.astimezone(timezone.utc).replace(tzinfo=None)
    dst_start = datetime.combine(_last_sunday(dt.year, 3), datetime.min.time()) + timedelta(hours=1)
    dst_end = datetime.combine(_last_sunday(dt.year, 10), datetime.min.time()) + timedelta(hours=1)
    offset = 3 if dst_start <= dt < dst_end else 2
    return dt + timedelta(hours=offset)


# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------

@dataclass
class _OrderRow:
    id: int
    liste_id: int
    list_date: date
    placed_at: datetime
    delivery_type_id: int
    payment_method_id: int
    nume_client: str
    phone_number: Optional[str]
    revenue: int
    items: int


@dataclass
class _ListRef:
    id: int
    data: date
    rank: int  # chronological position among lists with orders


@dataclass
class _Period:
    lists: List[_ListRef]
    previous_lists: Optional[List[_ListRef]]
    all_lists: List[_ListRef]
    info: StatsPeriod


def _load_orders(db: Session, list_ids: Optional[Iterable[int]] = None) -> List[_OrderRow]:
    totals = (
        db.query(
            OrderItemModel.comenzi_id.label("order_id"),
            func.sum(OrderItemModel.pret_produs * OrderItemModel.cantitate_produs).label("revenue"),
            func.sum(OrderItemModel.cantitate_produs).label("item_count"),
        )
        .group_by(OrderItemModel.comenzi_id)
        .subquery()
    )
    query = (
        db.query(
            OrderModel.id,
            OrderModel.liste_id,
            ListModel.data,
            OrderModel.data_plasarii,
            OrderModel.delivery_type_id,
            OrderModel.payment_method_id,
            OrderModel.nume_client,
            OrderModel.phone_number,
            func.coalesce(totals.c.revenue, 0),
            func.coalesce(totals.c.item_count, 0),
        )
        .join(ListModel, ListModel.id == OrderModel.liste_id)
        .outerjoin(totals, totals.c.order_id == OrderModel.id)
        .filter(OrderModel.is_deleted == 0, ListModel.is_deleted == 0)
    )
    if list_ids is not None:
        query = query.filter(OrderModel.liste_id.in_(list(list_ids)))
    return [
        _OrderRow(
            id=r[0],
            liste_id=r[1],
            list_date=r[2],
            placed_at=r[3],
            delivery_type_id=r[4],
            payment_method_id=r[5],
            nume_client=r[6] or "",
            phone_number=r[7],
            revenue=int(r[8] or 0),
            items=int(r[9] or 0),
        )
        for r in query.all()
    ]


def _lists_with_orders(db: Session) -> List[_ListRef]:
    """Non-deleted lists that received at least one order, oldest first.

    Soft-deleted orders count here so that a list whose orders were all cancelled
    still shows up (with its cancellations); lists nobody ordered from are skipped.
    """
    rows = (
        db.query(ListModel.id, ListModel.data)
        .join(OrderModel, OrderModel.liste_id == ListModel.id)
        .filter(ListModel.is_deleted == 0)
        .group_by(ListModel.id, ListModel.data)
        .order_by(ListModel.data.asc(), ListModel.id.asc())
        .all()
    )
    return [_ListRef(id=r[0], data=r[1], rank=i) for i, r in enumerate(rows)]


def _resolve_period(
    db: Session,
    start_date: Optional[date],
    end_date: Optional[date],
) -> _Period:
    if start_date and end_date and start_date > end_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="start_date must be before end_date",
        )

    all_lists = _lists_with_orders(db)
    current = [
        lst for lst in all_lists
        if (start_date is None or lst.data >= start_date)
        and (end_date is None or lst.data <= end_date)
    ]
    # Report the delivery dates of the lists actually included
    start, end = (current[0].data, current[-1].data) if current else (start_date, end_date)

    # The comparison period is the same number of lists right before the first one.
    # Deliveries are not spread evenly over the calendar, so a window of equal length
    # can hold a different number of lists and skew every total. Its dates may span a
    # few more or fewer days instead. Without that many earlier lists (always the case
    # for "all time") there is no comparison, since a partial one would skew it too.
    previous: Optional[List[_ListRef]] = None
    if current and current[0].rank >= len(current):
        first = current[0].rank
        previous = all_lists[first - len(current):first]

    info = StatsPeriod(
        start_date=start,
        end_date=end,
        list_count=len(current),
        previous_start_date=previous[0].data if previous else None,
        previous_end_date=previous[-1].data if previous else None,
        previous_list_count=len(previous) if previous else 0,
    )
    return _Period(lists=current, previous_lists=previous, all_lists=all_lists, info=info)


# ---------------------------------------------------------------------------
# Customer identity
# ---------------------------------------------------------------------------

def _phone_key(phone: Optional[str]) -> Optional[str]:
    if not phone:
        return None
    digits = re.sub(r"\D", "", phone)
    if len(digits) < 7:
        return None
    return "p:" + digits[-9:]


def _customer_keys(rows: List[_OrderRow]) -> Dict[int, str]:
    """Map order id -> customer key."""
    name_to_phone: Dict[str, str] = {}
    for row in sorted(rows, key=lambda r: r.placed_at or datetime.min):
        key = _phone_key(row.phone_number)
        if key:
            name_to_phone[normalize_name_for_matching(row.nume_client)] = key
    keys: Dict[int, str] = {}
    for row in rows:
        name = normalize_name_for_matching(row.nume_client)
        keys[row.id] = _phone_key(row.phone_number) or name_to_phone.get(name) or "n:" + name
    return keys


def _first_rank_by_customer(
    rows: List[_OrderRow], keys: Dict[int, str], rank_by_list: Dict[int, int]
) -> Dict[str, int]:
    first: Dict[str, int] = {}
    for row in rows:
        rank = rank_by_list.get(row.liste_id)
        if rank is None:
            continue
        key = keys[row.id]
        if key not in first or rank < first[key]:
            first[key] = rank
    return first


# ---------------------------------------------------------------------------
# Overview
# ---------------------------------------------------------------------------

def _cancelled_count(db: Session, list_ids: List[int]) -> int:
    if not list_ids:
        return 0
    return (
        db.query(func.count(OrderModel.id))
        .filter(OrderModel.is_deleted != 0, OrderModel.liste_id.in_(list_ids))
        .scalar()
        or 0
    )


def _summarize(
    db: Session,
    lists: List[_ListRef],
    rows: List[_OrderRow],
    keys: Dict[int, str],
    first_rank: Dict[str, int],
) -> StatsSummary:
    list_ids = {lst.id for lst in lists}
    rank_by_list = {lst.id: lst.rank for lst in lists}
    period_rows = [r for r in rows if r.liste_id in list_ids]

    revenue = sum(r.revenue for r in period_rows)
    orders = len(period_rows)
    last_rank: Dict[str, int] = {}
    for r in period_rows:
        key = keys[r.id]
        last_rank[key] = max(last_rank.get(key, -1), rank_by_list[r.liste_id])
    returning = sum(1 for key, rank in last_rank.items() if first_rank.get(key, rank) < rank)
    unique = len(last_rank)
    cancelled = _cancelled_count(db, list(list_ids))

    return StatsSummary(
        revenue=revenue,
        orders=orders,
        average_order_value=round(revenue / orders, 2) if orders else 0.0,
        items_sold=sum(r.items for r in period_rows),
        unique_customers=unique,
        returning_customers=returning,
        repeat_customer_rate=round(returning / unique, 4) if unique else 0.0,
        cancelled_orders=cancelled,
        cancelled_rate=round(cancelled / (orders + cancelled), 4) if (orders + cancelled) else 0.0,
    )


def _breakdown(
    rows: List[_OrderRow], attr: str, names: Dict[int, str]
) -> List[BreakdownSlice]:
    orders: Dict[int, int] = defaultdict(int)
    revenue: Dict[int, int] = defaultdict(int)
    for r in rows:
        ident = getattr(r, attr)
        orders[ident] += 1
        revenue[ident] += r.revenue
    slices = [
        BreakdownSlice(id=ident, name=names.get(ident, f"#{ident}"), orders=orders[ident], revenue=revenue[ident])
        for ident in orders
    ]
    return sorted(slices, key=lambda s: s.orders, reverse=True)


def get_overview(
    db: Session,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
) -> StatsOverview:
    try:
        period = _resolve_period(db, start_date, end_date)
        all_rows = _load_orders(db)
        keys = _customer_keys(all_rows)
        first_rank = _first_rank_by_customer(all_rows, keys, {lst.id: lst.rank for lst in period.all_lists})

        summary = _summarize(db, period.lists, all_rows, keys, first_rank)
        previous_summary = (
            _summarize(db, period.previous_lists, all_rows, keys, first_rank)
            if period.previous_lists
            else None
        )

        period_ids = {lst.id for lst in period.lists}
        period_rows = [r for r in all_rows if r.liste_id in period_ids]

        rows_by_list: Dict[int, List[_OrderRow]] = defaultdict(list)
        for r in period_rows:
            rows_by_list[r.liste_id].append(r)
        list_points: List[ListStatsPoint] = []
        for lst in period.lists:
            lrows = rows_by_list.get(lst.id, [])
            revenue = sum(r.revenue for r in lrows)
            customers = {keys[r.id] for r in lrows}
            new = sum(1 for c in customers if first_rank.get(c) == lst.rank)
            list_points.append(
                ListStatsPoint(
                    list_id=lst.id,
                    data=lst.data,
                    orders=len(lrows),
                    revenue=revenue,
                    average_order_value=round(revenue / len(lrows), 2) if lrows else 0.0,
                    customers=len(customers),
                    new_customers=new,
                    returning_customers=len(customers) - new,
                )
            )

        delivery_names = {d.id: d.denumire for d in db.query(DeliveryType).all()}
        payment_names = {p.id: p.name for p in db.query(ModalitatiPlata).all()}

        heat: Dict[Tuple[int, int], int] = defaultdict(int)
        for r in period_rows:
            if r.placed_at is None:
                continue
            local = _utc_to_romania(r.placed_at)
            heat[(local.weekday(), local.hour)] += 1
        heatmap = [
            HeatmapCell(weekday=wd, hour=h, orders=heat.get((wd, h), 0))
            for wd in range(7)
            for h in range(24)
        ]

        return StatsOverview(
            period=period.info,
            summary=summary,
            previous_summary=previous_summary,
            lists=list_points,
            delivery_types=_breakdown(period_rows, "delivery_type_id", delivery_names),
            payment_methods=_breakdown(period_rows, "payment_method_id", payment_names),
            heatmap=heatmap,
        )
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Database error: {str(e)}")


# ---------------------------------------------------------------------------
# Products
# ---------------------------------------------------------------------------

def get_product_stats(
    db: Session,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    limit: int = 10,
) -> ProductStatsResponse:
    try:
        period = _resolve_period(db, start_date, end_date)
        list_ids = [lst.id for lst in period.lists]
        empty = ProductStatsResponse(
            period=period.info,
            top_by_quantity=[],
            top_by_revenue=[],
            categories=[],
            unsold_products=[],
            sell_outs=[],
        )
        if not list_ids:
            return empty

        # Sales per product and per category it was listed under in each list, so past
        # periods keep their category figures when a product later moves to another one.
        # An order belongs to one list, where a product has one category, so per-category
        # order counts add up to the product's.
        sales = (
            db.query(
                OrderItemModel.produse_id,
                ListProductOrdered.category_id,
                func.sum(OrderItemModel.cantitate_produs),
                func.sum(OrderItemModel.pret_produs * OrderItemModel.cantitate_produs),
                func.count(func.distinct(OrderItemModel.comenzi_id)),
            )
            .join(OrderModel, OrderModel.id == OrderItemModel.comenzi_id)
            .outerjoin(
                ListProductOrdered,
                and_(
                    ListProductOrdered.liste_id == OrderModel.liste_id,
                    ListProductOrdered.produse_id == OrderItemModel.produse_id,
                ),
            )
            .filter(OrderModel.is_deleted == 0, OrderModel.liste_id.in_(list_ids))
            .group_by(OrderItemModel.produse_id, ListProductOrdered.category_id)
            .all()
        )
        # Where each product was on sale and where it sold out (see stoc_produs in the
        # module docstring)
        listings = (
            db.query(ListProductOrdered.liste_id, ListProductOrdered.produse_id, ListProductOrdered.stoc_produs)
            .filter(ListProductOrdered.liste_id.in_(list_ids))
            .all()
        )
        ordered_in_list = {
            (liste_id, produse_id)
            for liste_id, produse_id in (
                db.query(OrderModel.liste_id, OrderItemModel.produse_id)
                .join(OrderItemModel, OrderItemModel.comenzi_id == OrderModel.id)
                .filter(OrderModel.is_deleted == 0, OrderModel.liste_id.in_(list_ids))
                .distinct()
                .all()
            )
        }
        offered: Dict[int, int] = defaultdict(int)
        sold_out: Dict[int, int] = defaultdict(int)
        for liste_id, produse_id, stoc in listings:
            had_orders = (liste_id, produse_id) in ordered_in_list
            if stoc == 0 and not had_orders:
                continue
            offered[produse_id] += 1
            if stoc == 0:
                sold_out[produse_id] += 1

        product_ids = {r[0] for r in sales} | set(offered)
        products = {
            p.id: p for p in db.query(Product).filter(Product.id.in_(product_ids)).all()
        } if product_ids else {}
        category_names = {c.id: c.name for c in db.query(Category).all()}
        unit_names = {u.id: u.denumire for u in db.query(Unitati).all()}

        product_totals: Dict[int, List[int]] = {}  # quantity, revenue, orders
        categories: Dict[int, CategoryStat] = {}
        for produse_id, listed_category_id, qty, revenue, order_count in sales:
            product = products.get(produse_id)
            qty, revenue, order_count = int(qty or 0), int(revenue or 0), int(order_count or 0)
            totals = product_totals.setdefault(produse_id, [0, 0, 0])
            totals[0] += qty
            totals[1] += revenue
            totals[2] += order_count
            # Products since removed from the list fall back to their current category
            category_id = listed_category_id or (product.category_id if product else None)
            if category_id is not None:
                cat = categories.setdefault(
                    category_id,
                    CategoryStat(
                        category_id=category_id,
                        name=category_names.get(category_id, f"#{category_id}"),
                        quantity=0,
                        revenue=0,
                    ),
                )
                cat.quantity += qty
                cat.revenue += revenue

        # Product rows are labelled with the product's current category
        stats: List[ProductStat] = []
        for produse_id, (qty, revenue, order_count) in product_totals.items():
            product = products.get(produse_id)
            category_id = product.category_id if product else None
            stats.append(
                ProductStat(
                    product_id=produse_id,
                    name=product.nume if product else f"Produs #{produse_id}",
                    category_name=category_names.get(category_id) if category_id else None,
                    unit=unit_names.get(product.unitati_id) if product else None,
                    quantity=qty,
                    revenue=revenue,
                    orders=order_count,
                )
            )

        # Deleted products are left out: there is nothing left to act on
        def is_active(produse_id: int) -> bool:
            return produse_id in products and not products[produse_id].is_deleted

        unsold = [
            UnsoldProduct(
                product_id=produse_id,
                name=products[produse_id].nume,
                category_name=category_names.get(products[produse_id].category_id),
                times_offered=count,
            )
            for produse_id, count in offered.items()
            if produse_id not in product_totals and is_active(produse_id)
        ]
        sell_outs = [
            ProductSellOut(
                product_id=produse_id,
                name=products[produse_id].nume,
                category_name=category_names.get(products[produse_id].category_id),
                sold_out=count,
                offered=offered[produse_id],
            )
            for produse_id, count in sold_out.items()
            if is_active(produse_id)
        ]

        return ProductStatsResponse(
            period=period.info,
            top_by_quantity=sorted(stats, key=lambda s: (s.quantity, s.revenue), reverse=True)[:limit],
            top_by_revenue=sorted(stats, key=lambda s: (s.revenue, s.quantity), reverse=True)[:limit],
            categories=sorted(categories.values(), key=lambda c: c.revenue, reverse=True),
            unsold_products=sorted(unsold, key=lambda u: (-u.times_offered, u.name)),
            sell_outs=sorted(sell_outs, key=lambda o: (-o.sold_out, -o.sold_out / o.offered, o.name)),
        )
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Database error: {str(e)}")


# ---------------------------------------------------------------------------
# Customers
# ---------------------------------------------------------------------------

@dataclass
class _CustomerAgg:
    name: str = ""
    phone: Optional[str] = None
    last_seen: datetime = datetime.min
    orders: int = 0
    revenue: int = 0
    lists: Set[int] = field(default_factory=set)

    def add(self, row: _OrderRow) -> None:
        self.orders += 1
        self.revenue += row.revenue
        self.lists.add(row.liste_id)
        placed = row.placed_at or datetime.min
        if placed >= self.last_seen:
            self.last_seen = placed
            self.name = row.nume_client.strip()
            if row.phone_number:
                self.phone = row.phone_number
        elif not self.phone and row.phone_number:
            self.phone = row.phone_number


def _as_utc(value: datetime) -> datetime:
    """data_plasarii is stored as naive UTC; tag it so clients convert it correctly."""
    return value.replace(tzinfo=timezone.utc) if value.tzinfo is None else value


def _customer_stat(c: _CustomerAgg) -> CustomerStat:
    return CustomerStat(
        name=c.name,
        phone_number=c.phone,
        orders=c.orders,
        lists=len(c.lists),
        revenue=c.revenue,
        last_order_date=_as_utc(c.last_seen),
    )


def _aggregate_customers(rows: List[_OrderRow], keys: Dict[int, str]) -> Dict[str, _CustomerAgg]:
    customers: Dict[str, _CustomerAgg] = defaultdict(_CustomerAgg)
    for row in rows:
        customers[keys[row.id]].add(row)
    return customers


def get_customer_stats(
    db: Session,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    limit: int = 10,
) -> CustomerStatsResponse:
    """Top customers for the period, by revenue and by number of orders.

    Orders from the whole history are loaded so that customer identity (phone, falling
    back to name) is resolved the same way as on the other endpoints.
    """
    try:
        period = _resolve_period(db, start_date, end_date)
        all_rows = _load_orders(db)
        keys = _customer_keys(all_rows)

        period_ids = {lst.id for lst in period.lists}
        period_customers = _aggregate_customers([r for r in all_rows if r.liste_id in period_ids], keys)
        top_customers = [
            _customer_stat(c)
            for c in sorted(period_customers.values(), key=lambda c: (c.revenue, c.orders), reverse=True)[:limit]
        ]
        top_customers_by_orders = [
            _customer_stat(c)
            for c in sorted(period_customers.values(), key=lambda c: (c.orders, c.revenue), reverse=True)[:limit]
        ]

        return CustomerStatsResponse(
            period=period.info,
            top_customers=top_customers,
            top_customers_by_orders=top_customers_by_orders,
        )
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Database error: {str(e)}")


# ---------------------------------------------------------------------------
# Current list
# ---------------------------------------------------------------------------

def _find_current_list(db: Session) -> Optional[ListModel]:
    base = db.query(ListModel).filter(ListModel.is_deleted == 0)
    order = (ListModel.data.desc(), ListModel.id.desc())
    return (
        base.filter(ListModel.is_published == 1).order_by(*order).first()
        or base.filter(ListModel.is_current == 1).order_by(*order).first()
        or base.order_by(*order).first()
    )


def get_current_list_stats(db: Session) -> CurrentListStats:
    try:
        current = _find_current_list(db)
        if current is None:
            return CurrentListStats()

        rows = _load_orders(db, [current.id])
        keys = _customer_keys(rows)

        # The last earlier list with active orders: one whose orders were all cancelled
        # has nothing to compare with
        previous_ref = (
            db.query(ListModel.id, ListModel.data)
            .join(OrderModel, OrderModel.liste_id == ListModel.id)
            .filter(
                ListModel.is_deleted == 0,
                OrderModel.is_deleted == 0,
                or_(
                    ListModel.data < current.data,
                    and_(ListModel.data == current.data, ListModel.id < current.id),
                ),
            )
            .order_by(ListModel.data.desc(), ListModel.id.desc())
            .first()
        )
        previous = None
        if previous_ref is not None:
            prev_rows = _load_orders(db, [previous_ref.id])
            previous = PreviousListInfo(
                id=previous_ref.id,
                data=previous_ref.data,
                orders=len(prev_rows),
                revenue=sum(r.revenue for r in prev_rows),
            )

        ordered_by_product = dict(
            db.query(OrderItemModel.produse_id, func.sum(OrderItemModel.cantitate_produs))
            .join(OrderModel, OrderModel.id == OrderItemModel.comenzi_id)
            .filter(OrderModel.is_deleted == 0, OrderModel.liste_id == current.id)
            .group_by(OrderItemModel.produse_id)
            .all()
        )
        # Products marked unavailable once they had orders (see stoc_produs in the
        # module docstring)
        marked_unavailable = (
            db.query(ListProductOrdered.produse_id, Product.nume, Unitati.denumire)
            .join(Product, Product.id == ListProductOrdered.produse_id)
            .outerjoin(Unitati, Unitati.id == Product.unitati_id)
            .filter(ListProductOrdered.liste_id == current.id, ListProductOrdered.stoc_produs == 0)
            .all()
        )
        sold_out = sorted(
            (
                SoldOutProduct(product_id=produse_id, name=name, unit=unit, ordered=int(ordered_by_product[produse_id]))
                for produse_id, name, unit in marked_unavailable
                if ordered_by_product.get(produse_id)
            ),
            key=lambda p: (-p.ordered, p.name),
        )

        return CurrentListStats(
            list=CurrentListInfo(
                id=current.id,
                data=current.data,
                expiration_date=current.expiration_date,
                is_published=bool(current.is_published),
            ),
            orders=len(rows),
            revenue=sum(r.revenue for r in rows),
            customers=len(set(keys.values())),
            items_sold=sum(r.items for r in rows),
            previous=previous,
            sold_out=sold_out,
        )
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Database error: {str(e)}")
