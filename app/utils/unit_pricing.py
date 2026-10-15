"""Unit pricing (price per kg / per litre) derived from a product's quantity and unit.

EU rules require a unit price for products sold by weight or volume, and Google
Merchant Center checks it through unit_pricing_measure / unit_pricing_base_measure.
This is the only implementation: the feed renders it, and the storefront's product
JSON-LD reads it from GET /products/{id}/offer.
"""
import re
from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal
from typing import Optional

_UNIT_ALIASES = {
    "g": "g",
    "gr": "g",
    "gram": "g",
    "grame": "g",
    "gramul": "g",
    "kg": "kg",
    "kilogram": "kg",
    "kilograme": "kg",
    "kilogramul": "kg",
    "ml": "ml",
    "mililitru": "ml",
    "mililitri": "ml",
    "l": "l",
    "litru": "l",
    "litri": "l",
    "litrul": "l",
}

# Size embedded in a container unit name, e.g. "Caserola de 250gr", "Pachet 2x400g",
# "Borcan 1/2 kg", "Pachet 500 de grame". \w is Unicode-aware, so "Tava de 12 găluște"
# is not read as 12 g. As in Romanian, a dot grouping three digits is a thousands
# separator ("1.500 g" is 1500 g), while "0.750 l" and "1,5 kg" are decimals.
_EMBEDDED_SIZE = re.compile(
    r"(?<![\w.,/])"
    r"(?:(?P<count>\d+)\s*[x×*]\s*)?"
    r"(?P<amount>(?P<grouped>[1-9]\d{0,2}(?:\.\d{3})+)(?!\d)|\d+(?:[.,]\d+)?)"
    r"(?:\s*/\s*(?P<divisor>\d+))?"
    rf"\s*(?:de\s+)?(?P<unit>{'|'.join(sorted(_UNIT_ALIASES, key=len, reverse=True))})\.?(?!\w)"
)

# Factor to the smallest unit of each dimension (g or ml)
_TO_SMALLEST = {"g": 1, "kg": 1000, "ml": 1, "l": 1000}
_BASE_UNIT = {"g": "kg", "kg": "kg", "ml": "l", "l": "l"}

# Amounts outside 10 g/ml .. 50 kg/l are treated as bad product data, not published
_MIN_AMOUNT = 10
_MAX_AMOUNT = 50_000


@dataclass(frozen=True)
class UnitPricing:
    """How much of a product one item holds, and the base it is priced per."""

    measure_value: Decimal
    measure_unit: str
    base_unit: str
    base_value: int = 1

    def feed_values(self) -> tuple[str, str]:
        """Return (unit_pricing_measure, unit_pricing_base_measure), e.g. ("600g", "1kg")."""
        measure = format(self.measure_value.normalize(), "f")
        return f"{measure}{self.measure_unit}", f"{self.base_value}{self.base_unit}"

    def offer_values(self) -> dict:
        """Return the unit pricing as GET /products/{id}/offer serves it (schemas.product_offer)."""
        return {
            "measure": {"value": self.measure_value, "unit": self.measure_unit},
            "base": {"value": self.base_value, "unit": self.base_unit},
        }


def _parse_unit_name(name: str) -> Optional[tuple[Decimal, str]]:
    """Return (amount per item, unit) for a unit name, or None if it has no weight or volume."""
    unit = _UNIT_ALIASES.get(name.rstrip("."))
    if unit is not None:
        return Decimal(1), unit

    matches = list(_EMBEDDED_SIZE.finditer(name))
    if len(matches) != 1:
        # No size, or several sizes we can't choose between ("Cutie 2x250g + 1kg")
        return None

    match = matches[0]
    divisor = Decimal(match.group("divisor") or 1)
    if divisor == 0:
        return None
    if match.group("grouped"):
        amount_text = match.group("amount").replace(".", "")
    else:
        amount_text = match.group("amount").replace(",", ".")
    amount = Decimal(match.group("count") or 1) * Decimal(amount_text) / divisor
    return amount, _UNIT_ALIASES[match.group("unit")]


def get_unit_pricing(cantitate: Optional[int], unit_name: Optional[str]) -> Optional[UnitPricing]:
    """Return the unit pricing for *cantitate* x *unit_name*, e.g. 600 x "gr" -> 600 g per 1 kg.

    Returns None for products not sold by weight or volume (e.g. "buc") and for
    quantities that are implausible enough to be data-entry mistakes.
    """
    if not unit_name or not cantitate or cantitate <= 0:
        return None

    parsed = _parse_unit_name(unit_name.strip().lower())
    if parsed is None:
        return None
    per_item, unit = parsed

    amount = Decimal(cantitate) * per_item
    if not _MIN_AMOUNT <= amount * _TO_SMALLEST[unit] <= _MAX_AMOUNT:
        return None

    return UnitPricing(
        measure_value=amount.quantize(Decimal("0.001"), rounding=ROUND_HALF_UP),
        measure_unit=unit,
        base_unit=_BASE_UNIT[unit],
    )
