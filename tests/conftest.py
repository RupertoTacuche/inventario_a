import os
import sys
from datetime import datetime

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from controller.inventory_controller import InventoryController  # noqa: E402
from controller.report_controller import ReportController  # noqa: E402
from controller.sales_controller import SalesController  # noqa: E402
from model.database import Database  # noqa: E402
from model.repositories import ProductRepository, SaleRepository  # noqa: E402


class FakeClock:
    def __init__(self, now=datetime(2026, 10, 13, 10, 0, 0)):
        self.now = now

    def __call__(self):
        return self.now


@pytest.fixture
def db():
    database = Database(":memory:")
    database.connect()
    yield database
    database.close()


@pytest.fixture
def clock():
    return FakeClock()


@pytest.fixture
def app(db, clock):
    products, sales = ProductRepository(db), SaleRepository(db)
    return type("App", (), dict(
        db=db, products=products, sales=sales, clock=clock,
        inventory=InventoryController(products),
        sales_ctl=SalesController(products, sales, clock),
        report=ReportController(sales, clock)))
