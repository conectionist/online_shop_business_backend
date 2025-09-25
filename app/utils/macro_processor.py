from __future__ import annotations

from datetime import datetime, timedelta
from typing import Callable, Dict


def _compute_next_delivery_date(reference_date: datetime) -> datetime:
    """
    Compute the next delivery date: next Tuesday (2) or Friday (5), whichever comes first.
    We find strictly the next occurrence (delta <= 0 -> +7 days).
    """
    day = reference_date.weekday()  # Monday=0 .. Sunday=6
    targets = [1 + 1, 4 + 1]  # Convert from JS getDay (Tue=2, Fri=5) to Python weekday (Tue=1, Fri=4) then +1 adjustment below
    # Simpler: directly specify Python weekdays: Tuesday=1, Friday=4
    targets = [1, 4]

    deltas = []
    for target in targets:
        delta = target - day
        if delta <= 0:
            delta += 7
        deltas.append(delta)

    min_delta = min(deltas)
    next_date = reference_date + timedelta(days=min_delta)
    return next_date.replace(hour=0, minute=0, second=0, microsecond=0)


def _format_date_ro_long(d: datetime) -> str:
    """
    Format date using Romanian long form: Joi, 25 Septembrie 2025.
    Avoid external dependencies by mapping weekday/month names.
    """
    weekdays = [
        "Luni", "Marți", "Miercuri", "Joi", "Vineri", "Sâmbătă", "Duminică"
    ]
    months = [
        "Ianuarie", "Februarie", "Martie", "Aprilie", "Mai", "Iunie",
        "Iulie", "August", "Septembrie", "Octombrie", "Noiembrie", "Decembrie"
    ]
    weekday = weekdays[d.weekday()]
    month = months[d.month - 1]
    return f"{weekday}, {d.day} {month} {d.year}"


def process_macros(text: str) -> str:
    """
    Replace supported macros in the given text and return the processed string.

    Supported macros:
    - {urmatoarea_zi_de_livrari}: Computes and formats the next delivery day in Romanian long form.
    """
    if not text or "{" not in text:
        return text

    # Dispatch table for macros -> callables
    def macro_next_delivery() -> str:
        dt = _compute_next_delivery_date(datetime.now())
        return _format_date_ro_long(dt)

    macro_handlers: Dict[str, Callable[[], str]] = {
        "{urmatoarea_zi_de_livrari}": macro_next_delivery,
    }

    # Perform simple, non-recursive replacements
    result = text
    for macro, handler in macro_handlers.items():
        if macro in result:
            try:
                result = result.replace(macro, handler())
            except Exception:
                # In case of unexpected errors, leave the macro as-is
                pass

    return result


