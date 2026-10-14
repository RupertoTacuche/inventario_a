"""Captura de ventas. Valida y lanza AppError; NO captura excepciones."""
from dataclasses import dataclass
from datetime import datetime
from typing import Callable

from model.entities import Product, Totals
from model.errors import ValidationError
from model.repositories import ProductRepository, SaleRepository

from .cart import Cart, calculate_totals
from .money import parse_int, parse_percent


@dataclass
class SaleResult:
    sale_id: int
    totals: Totals
    low_stock: list[Product]  # productos que quedaron bajo el mínimo tras vender


class SalesController:
    def __init__(self, products: ProductRepository, sales: SaleRepository,
                 clock: Callable[[], datetime] = datetime.now):
        self.products = products
        self.sales = sales
        self.clock = clock

    def sellable_products(self) -> list[Product]:
        return [p for p in self.products.list() if p.quantity > 0]

    def add_to_cart(self, cart: Cart, product_id: str | None, quantity_text: str) -> None:
        if not product_id:
            raise ValidationError("Elige un producto.")
        quantity = parse_int(quantity_text, "la cantidad", minimum=1)
        cart.add(self.products.get(int(product_id)), quantity)

    def preview(self, cart: Cart, discount_text: str = "", charge_iva: bool = True) -> Totals:
        return calculate_totals(cart.lines, parse_percent(discount_text), charge_iva)

    def checkout(self, cart: Cart, discount_text: str = "", charge_iva: bool = True) -> SaleResult:
        if cart.is_empty:
            raise ValidationError("Agrega al menos un producto a la venta.")
        totals = calculate_totals(cart.lines, parse_percent(discount_text), charge_iva)
        now = self.clock()
        sale_id = self.sales.register_sale(now.date().isoformat(),
                                           now.isoformat(timespec="seconds"),
                                           list(cart.lines), totals)
        low = [p for p in (self.products.get(l.product_id) for l in cart.lines) if p.is_low]
        cart.clear()
        return SaleResult(sale_id, totals, low)
