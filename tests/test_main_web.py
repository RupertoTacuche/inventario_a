import os
import pytest

pytest.importorskip("flet")


def test_db_path_priority(monkeypatch, tmp_path):
    from view import compat as c
    for k in ("INVENTARIO_DATA_DIR", "RAILWAY_VOLUME_MOUNT_PATH", "FLET_APP_STORAGE_DATA"):
        monkeypatch.delenv(k, raising=False)
    assert c.db_path().endswith(os.path.join("data", "inventario.db"))
    monkeypatch.setenv("FLET_APP_STORAGE_DATA", str(tmp_path / "phone"))
    assert c.db_path().startswith(str(tmp_path / "phone"))
    monkeypatch.setenv("RAILWAY_VOLUME_MOUNT_PATH", str(tmp_path / "vol"))
    assert c.db_path().startswith(str(tmp_path / "vol"))
    monkeypatch.setenv("INVENTARIO_DATA_DIR", str(tmp_path / "manual"))
    assert c.db_path().startswith(str(tmp_path / "manual"))


def test_two_browser_sessions_share_one_database(monkeypatch, tmp_path):
    monkeypatch.setenv("INVENTARIO_DATA_DIR", str(tmp_path))
    import main
    from tests.test_view_smoke import FakePage
    monkeypatch.setattr(main, "_db", None)
    p1, p2 = FakePage(), FakePage()
    main.main(p1)
    main.main(p2)
    assert len(p1.added) == 1 and len(p2.added) == 1
    assert (tmp_path / "inventario.db").exists()
    main._db.close()


def test_run_app_uses_port_env(monkeypatch):
    import flet as ft
    from view import compat as c
    calls = {}
    monkeypatch.setattr(ft, "run", lambda main, **kw: calls.update(kw))
    monkeypatch.setenv("PORT", "8123")
    c.run_app(lambda page: None)
    assert calls["host"] == "0.0.0.0" and calls["port"] == 8123
