"""Punto de entrada. Arma Model -> Controller -> View y abre la base de datos."""
import logging
import sys
import threading

import flet as ft

from controller.inventory_controller import InventoryController
from controller.report_controller import ReportController
from controller.sales_controller import SalesController
from model.database import Database
from model.errors import AppError
from model.repositories import ProductRepository, SaleRepository
from view import compat as c
from view.app_view import build_app

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s",
                    stream=sys.stderr)
log = logging.getLogger("inventario")

_db: Database | None = None
_db_lock = threading.Lock()


def get_database() -> Database:
    """Una sola conexión para todas las sesiones (en web cada pestaña del navegador llama main)."""
    global _db
    with _db_lock:
        if _db is None:
            db = Database(c.db_path())
            db.connect()          # puede lanzar AppError
            _db = db
        return _db


def main(page: ft.Page) -> None:
    try:
        db = get_database()
    except AppError as exc:       # sin base de datos no hay app: mostramos el motivo
        page.add(ft.Text(f"No se pudo iniciar la app: {exc}", color=ft.Colors.RED_300))
        return

    products, sales = ProductRepository(db), SaleRepository(db)
    build_app(page, InventoryController(products), SalesController(products, sales),
              ReportController(sales))


if __name__ == "__main__":
    c.run_app(main)
