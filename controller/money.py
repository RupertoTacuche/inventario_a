"""Conversión de texto <-> centavos. Todas las validaciones numéricas viven aquí."""
from decimal import ROUND_HALF_UP, Decimal, InvalidOperation

from model.errors import ValidationError

IVA_PERCENT = Decimal("16")


def parse_money(text: str, field: str) -> int:
    """'12', '12.5', '12,50', '$1,200.00' -> centavos."""
    raw = (text or "").replace("$", "").replace(" ", "").strip()
    if not raw:
        raise ValidationError(f"Escribe {field}.")
    if "," in raw and "." not in raw:
        raw = raw.replace(",", ".")
    else:
        raw = raw.replace(",", "")
    try:
        value = Decimal(raw)
    except InvalidOperation:
        raise ValidationError(f"{field.capitalize()} no es un número válido.") from None
    if not value.is_finite() or value < 0:
        raise ValidationError(f"{field.capitalize()} no puede ser negativo.")
    return int((value * 100).quantize(Decimal(1), rounding=ROUND_HALF_UP))


def parse_int(text: str, field: str, minimum: int = 0) -> int:
    raw = (text or "").strip()
    if not raw:
        raise ValidationError(f"Escribe {field}.")
    try:
        value = int(raw)
    except ValueError:
        raise ValidationError(f"{field.capitalize()} debe ser un número entero.") from None
    if value < minimum:
        raise ValidationError(f"{field.capitalize()} debe ser al menos {minimum}.")
    return value


def parse_percent(text: str, field: str = "el descuento") -> Decimal:
    raw = (text or "").strip().replace("%", "").replace(",", ".")
    if not raw:
        return Decimal(0)
    try:
        value = Decimal(raw)
    except InvalidOperation:
        raise ValidationError(f"{field.capitalize()} no es un número válido.") from None
    if not value.is_finite() or not (Decimal(0) <= value <= Decimal(100)):
        raise ValidationError(f"{field.capitalize()} debe estar entre 0 y 100 %.")
    return value


def percent_of(cents: int, percent: Decimal) -> int:
    """Porcentaje de una cantidad en centavos, redondeo comercial (mitad hacia arriba)."""
    return int((Decimal(cents) * percent / 100).quantize(Decimal(1), rounding=ROUND_HALF_UP))


def format_money(cents: int) -> str:
    sign = "-" if cents < 0 else ""
    cents = abs(cents)
    return f"{sign}${cents // 100:,}.{cents % 100:02d}"
