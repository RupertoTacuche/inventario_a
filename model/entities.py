"""Datos puros (sin lógica de UI ni de SQL)."""
from dataclasses import dataclass, field


@dataclass(frozen=True)
class Product:
    id: int
    name: str
    cost_cents: int
    price_cents: int
    quantity: int
    min_stock: int

    @property
    def is_low(self) -> bool:
        """Alerta: la cantidad bajó del stock mínimo."""
        return self.quantity < self.min_stock


@dataclass(frozen=True)
class CartLine:
    product_id: int
    name: str
    quantity: int
    unit_price_cents: int
    unit_cost_cents: int

    @property
    def subtotal_cents(self) -> int:
        return self.quantity * self.unit_price_cents


@dataclass(frozen=True)
class Totals:
    subtotal_cents: int = 0
    discount_cents: int = 0
    iva_cents: int = 0
    total_cents: int = 0
    cost_cents: int = 0

    @property
    def profit_cents(self) -> int:
        """Ganancia de la venta = venta neta (sin IVA) - costo."""
        return self.subtotal_cents - self.discount_cents - self.cost_cents


@dataclass(frozen=True)
class InventoryTotals:
    products: int
    units: int
    value_cents: int  # suma de costo * cantidad


@dataclass(frozen=True)
class ProductSales:
    name: str
    quantity: int
    revenue_cents: int
    profit_cents: int


@dataclass
class DailyReport:
    day: str
    transactions: int = 0
    subtotal_cents: int = 0
    discount_cents: int = 0
    iva_cents: int = 0
    total_cents: int = 0
    cost_cents: int = 0
    closed: bool = False
    products: list[ProductSales] = field(default_factory=list)

    @property
    def units_sold(self) -> int:
        return sum(p.quantity for p in self.products)

    @property
    def gross_profit_cents(self) -> int:
        """Ganancia bruta = ventas - costo."""
        return self.subtotal_cents - self.cost_cents

    @property
    def net_profit_cents(self) -> int:
        """Total neto ganado = ganancia bruta - descuentos (el IVA no es ganancia)."""
        return self.gross_profit_cents - self.discount_cents
