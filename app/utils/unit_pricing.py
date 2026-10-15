"""Unit pricing (price per kg / per litre) derived from a product's quantity and unit.

EU rules require a unit price for products sold by weight or volume, and Google
Merchant Center checks it through unit_pricing_measure / unit_pricing_base_measure.
The frontend mirrors this logic in src/utils/unitPricing.ts; keep the two in sync.
"""
import re
from typing import Optional, Tuple

_EXACT_UNITS = {
    "g": "g",
    "gr": "g",
    "grame": "g",
    "kg": "kg",
    "ml": "ml",
    "l": "l",
    "litru": "l",
    "litri": "l",
}

# Size embedded in a container unit name, e.g. "Caserola de 250gr", "Borcanul de 800gr"
_EMBEDDED_SIZE = re.compile(r"(\d+(?:[.,]\d+)?)\s*(gr|g|kg|ml|l)\b")

# Factor to the smallest unit of each dimension (g or ml)
_TO_SMALLEST = {"g": 1, "kg": 1000, "ml": 1, "l": 1000}
_BASE_MEASURE = {"g": "1kg", "kg": "1kg", "ml": "1l", "l": "1l"}

# Amounts outside 10 g/ml .. 50 kg/l are treated as bad product data, not published
_MIN_AMOUNT = 10
_MAX_AMOUNT = 50_000


def _format_amount(amount: float) -> str:
    return f"{amount:.3f}".rstrip("0").rstrip(".")


def get_unit_pricing(cantitate: Optional[int], unit_name: Optional[str]) -> Optional[Tuple[str, str]]:
    """Return (unit_pricing_measure, unit_pricing_base_measure), e.g. ("600g", "1kg").

    Returns None for products not sold by weight or volume (e.g. "buc") and for
    quantities that are implausible enough to be data-entry mistakes.
    """
    if not unit_name or not cantitate or cantitate <= 0:
        return None

    name = unit_name.strip().lower()
    amount = float(cantitate)
    unit = _EXACT_UNITS.get(name)
    if unit is None:
        match = _EMBEDDED_SIZE.search(name)
        if match is None:
            return None
        unit = _EXACT_UNITS[match.group(2)]
        amount *= float(match.group(1).replace(",", "."))

    if not _MIN_AMOUNT <= amount * _TO_SMALLEST[unit] <= _MAX_AMOUNT:
        return None

    return f"{_format_amount(amount)}{unit}", _BASE_MEASURE[unit]
