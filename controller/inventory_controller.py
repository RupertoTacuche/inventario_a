"""Reglas del inventario. Valida y lanza AppError; NO captura excepciones."""
from model.entities import InventoryTotals, Product
from model.errors import ValidationError
from model.repositories import ProductRepository

from .money import parse_int, parse_money

MAX_NAME = 60


class InventoryController:
    def __init__(self, products: ProductRepository):
        self.products = products

    def _clean(self, name, cost, price, quantity, min_stock):
        name = " ".join((name or "").split())
        if not name:
            raise ValidationError("Escribe el nombre del producto.")
        if len(name) > MAX_NAME:
            raise ValidationError(f"El nombre admite máximo {MAX_NAME} caracteres.")
        return (name,
                parse_money(cost, "el costo"),
                parse_money(price, "el precio de venta"),
                parse_int(quantity, "la cantidad"),
                parse_int(min_stock, "el stock mínimo"))

    def list_products(self, search: str = "") -> list[Product]:
        return self.products.list(search)

    def totals(self) -> InventoryTotals:
        return self.products.totals()

    def low_stock(self) -> list[Product]:
        return self.products.low_stock()

    def add(self, name, cost, price, quantity, min_stock) -> Product:
        data = self._clean(name, cost, price, quantity, min_stock)
        return self.products.get(self.products.add(*data))

    def update(self, product_id: int, name, cost, price, quantity, min_stock) -> Product:
        data = self._clean(name, cost, price, quantity, min_stock)
        self.products.update(product_id, *data)
        return self.products.get(product_id)

    def delete(self, product_id: int) -> None:
        self.products.delete(product_id)
