"""Carrito de la venta en curso y cálculo de totales (lógica pura, fácil de probar)."""
from decimal import Decimal

from model.entities import CartLine, Product, Totals
from model.errors import InsufficientStockError, ValidationError

from .money import IVA_PERCENT, percent_of


def calculate_totals(lines: list[CartLine], discount_percent: Decimal = Decimal(0),
                     charge_iva: bool = True) -> Totals:
    subtotal = sum(l.subtotal_cents for l in lines)
    cost = sum(l.quantity * l.unit_cost_cents for l in lines)
    discount = percent_of(subtotal, discount_percent)
    iva = percent_of(subtotal - discount, IVA_PERCENT) if charge_iva else 0
    return Totals(subtotal, discount, iva, subtotal - discount + iva, cost)


class Cart:
    def __init__(self):
        self.lines: list[CartLine] = []

    def add(self, product: Product, quantity: int) -> None:
        if quantity <= 0:
            raise ValidationError("La cantidad debe ser al menos 1.")
        already = next((l for l in self.lines if l.product_id == product.id), None)
        wanted = quantity + (already.quantity if already else 0)
        if wanted > product.quantity:
            raise InsufficientStockError(
                f"Solo hay {product.quantity} de «{product.name}» en inventario.")
        new = CartLine(product.id, product.name, wanted,
                       product.price_cents, product.cost_cents)
        if already:
            self.lines[self.lines.index(already)] = new
        else:
            self.lines.append(new)

    def remove(self, index: int) -> None:
        if 0 <= index < len(self.lines):
            del self.lines[index]

    def clear(self) -> None:
        self.lines.clear()

    @property
    def is_empty(self) -> bool:
        return not self.lines
