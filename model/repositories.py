"""SQL de productos y ventas. Ninguna regla de negocio aquí, solo persistencia."""
from __future__ import annotations

from .database import Database
from .entities import CartLine, DailyReport, InventoryTotals, Product, ProductSales, Totals
from .errors import InsufficientStockError, NotFoundError


def _product(row) -> Product:
    return Product(row["id"], row["name"], row["cost_cents"], row["price_cents"],
                   row["quantity"], row["min_stock"])


class ProductRepository:
    def __init__(self, db: Database):
        self.db = db

    def add(self, name: str, cost: int, price: int, quantity: int, min_stock: int) -> int:
        with self.db.transaction() as cur:
            cur.execute(
                "INSERT INTO products (name, cost_cents, price_cents, quantity, min_stock) "
                "VALUES (?, ?, ?, ?, ?)", (name, cost, price, quantity, min_stock))
            return cur.lastrowid

    def update(self, product_id: int, name: str, cost: int, price: int,
               quantity: int, min_stock: int) -> None:
        with self.db.transaction() as cur:
            cur.execute(
                "UPDATE products SET name=?, cost_cents=?, price_cents=?, quantity=?, min_stock=? "
                "WHERE id=?", (name, cost, price, quantity, min_stock, product_id))
            if cur.rowcount == 0:
                raise NotFoundError("El producto ya no existe.")

    def delete(self, product_id: int) -> None:
        with self.db.transaction() as cur:
            cur.execute("DELETE FROM products WHERE id=?", (product_id,))
            if cur.rowcount == 0:
                raise NotFoundError("El producto ya no existe.")

    def get(self, product_id: int) -> Product:
        rows = self.db.query("SELECT * FROM products WHERE id=?", (product_id,))
        if not rows:
            raise NotFoundError("El producto ya no existe.")
        return _product(rows[0])

    def list(self, search: str = "") -> list[Product]:
        like = f"%{search.strip()}%"
        rows = self.db.query(
            "SELECT * FROM products WHERE name LIKE ? ORDER BY id", (like,))
        return [_product(r) for r in rows]

    def totals(self) -> InventoryTotals:
        row = self.db.query(
            "SELECT COUNT(*) n, COALESCE(SUM(quantity),0) u, "
            "COALESCE(SUM(quantity*cost_cents),0) v FROM products")[0]
        return InventoryTotals(row["n"], row["u"], row["v"])

    def low_stock(self) -> list[Product]:
        rows = self.db.query("SELECT * FROM products WHERE quantity < min_stock ORDER BY id")
        return [_product(r) for r in rows]


class SaleRepository:
    def __init__(self, db: Database):
        self.db = db

    def register_sale(self, day: str, created_at: str, lines: list[CartLine],
                      totals: Totals) -> int:
        """Guarda la venta y descuenta stock en UNA sola transacción (todo o nada)."""
        with self.db.transaction() as cur:
            cur.execute(
                "INSERT INTO sales (day, created_at, subtotal_cents, discount_cents, "
                "iva_cents, total_cents) VALUES (?,?,?,?,?,?)",
                (day, created_at, totals.subtotal_cents, totals.discount_cents,
                 totals.iva_cents, totals.total_cents))
            sale_id = cur.lastrowid
            for ln in lines:
                # UPDATE condicional: evita stock negativo aunque dos ventas choquen.
                cur.execute(
                    "UPDATE products SET quantity = quantity - ? WHERE id=? AND quantity >= ?",
                    (ln.quantity, ln.product_id, ln.quantity))
                if cur.rowcount == 0:
                    raise InsufficientStockError(
                        f"No hay suficiente stock de «{ln.name}».")
                cur.execute(
                    "INSERT INTO sale_items (sale_id, product_id, product_name, quantity, "
                    "unit_price_cents, unit_cost_cents) VALUES (?,?,?,?,?,?)",
                    (sale_id, ln.product_id, ln.name, ln.quantity,
                     ln.unit_price_cents, ln.unit_cost_cents))
            # Vender en un día "cerrado" lo vuelve a abrir.
            cur.execute("DELETE FROM day_closures WHERE day=?", (day,))
            return sale_id

    def daily_report(self, day: str) -> DailyReport:
        s = self.db.query(
            "SELECT COUNT(*) n, COALESCE(SUM(subtotal_cents),0) sub, "
            "COALESCE(SUM(discount_cents),0) disc, COALESCE(SUM(iva_cents),0) iva, "
            "COALESCE(SUM(total_cents),0) tot FROM sales WHERE day=?", (day,))[0]
        cost = self.db.query(
            "SELECT COALESCE(SUM(i.quantity*i.unit_cost_cents),0) c FROM sale_items i "
            "JOIN sales s ON s.id=i.sale_id WHERE s.day=?", (day,))[0]["c"]
        prods = self.db.query(
            "SELECT i.product_name n, SUM(i.quantity) q, "
            "SUM(i.quantity*i.unit_price_cents) rev, "
            "SUM(i.quantity*(i.unit_price_cents-i.unit_cost_cents)) prof "
            "FROM sale_items i JOIN sales s ON s.id=i.sale_id WHERE s.day=? "
            "GROUP BY i.product_name ORDER BY rev DESC", (day,))
        closed = bool(self.db.query("SELECT 1 FROM day_closures WHERE day=?", (day,)))
        return DailyReport(
            day=day, transactions=s["n"], subtotal_cents=s["sub"], discount_cents=s["disc"],
            iva_cents=s["iva"], total_cents=s["tot"], cost_cents=cost, closed=closed,
            products=[ProductSales(r["n"], r["q"], r["rev"], r["prof"]) for r in prods])

    def close_day(self, day: str, closed_at: str) -> None:
        with self.db.transaction() as cur:
            cur.execute("INSERT OR REPLACE INTO day_closures (day, closed_at) VALUES (?,?)",
                        (day, closed_at))
