import pytest

from model.errors import DuplicateError, NotFoundError


def test_ids_are_incremental_and_never_reused(app):
    a = app.products.add("A", 100, 200, 5, 1)
    b = app.products.add("B", 100, 200, 5, 1)
    app.products.delete(b)
    c = app.products.add("C", 100, 200, 5, 1)
    assert (a, b, c) == (1, 2, 3)


def test_duplicate_name_is_rejected_case_insensitive(app):
    app.products.add("Pepsi", 100, 200, 5, 1)
    with pytest.raises(DuplicateError):
        app.products.add("pepsi", 100, 200, 5, 1)


def test_update_and_delete_missing_raise(app):
    with pytest.raises(NotFoundError):
        app.products.update(99, "X", 1, 1, 1, 1)
    with pytest.raises(NotFoundError):
        app.products.delete(99)


def test_inventory_total_value_is_cost_times_quantity(app):
    app.products.add("A", 1000, 2000, 3, 1)   # $10 x 3 = $30
    app.products.add("B", 250, 500, 4, 1)     # $2.50 x 4 = $10
    t = app.products.totals()
    assert (t.products, t.units, t.value_cents) == (2, 7, 4000)


def test_search_filters_by_name(app):
    app.products.add("Pepsi 600 ml", 1, 2, 1, 0)
    app.products.add("Sprite", 1, 2, 1, 0)
    assert [p.name for p in app.products.list("pep")] == ["Pepsi 600 ml"]


def test_low_stock_flag(app):
    pid = app.products.add("A", 1, 2, 2, 5)
    assert app.products.get(pid).is_low
    assert [p.id for p in app.products.low_stock()] == [pid]


def test_persistence_on_disk(tmp_path):
    from model.database import Database
    from model.repositories import ProductRepository
    path = str(tmp_path / "x" / "inv.db")
    d1 = Database(path); d1.connect(); ProductRepository(d1).add("A", 1, 2, 3, 1); d1.close()
    d2 = Database(path); d2.connect()
    assert [p.name for p in ProductRepository(d2).list()] == ["A"]
    d2.close()
