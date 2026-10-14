"""Conexión SQLite + esquema. Aquí vive el try / except / finally de la base de datos."""
import logging
import os
import sqlite3
import threading
from contextlib import contextmanager

from .errors import AppError, DatabaseError, DuplicateError

log = logging.getLogger(__name__)

SCHEMA = """
CREATE TABLE IF NOT EXISTS products (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,      -- incremental, nunca se reutiliza
    name         TEXT    NOT NULL UNIQUE COLLATE NOCASE,
    cost_cents   INTEGER NOT NULL CHECK (cost_cents  >= 0),
    price_cents  INTEGER NOT NULL CHECK (price_cents >= 0),
    quantity     INTEGER NOT NULL CHECK (quantity    >= 0),
    min_stock    INTEGER NOT NULL CHECK (min_stock   >= 0)
);

CREATE TABLE IF NOT EXISTS sales (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    day             TEXT    NOT NULL,                    -- YYYY-MM-DD
    created_at      TEXT    NOT NULL,
    subtotal_cents  INTEGER NOT NULL,
    discount_cents  INTEGER NOT NULL,
    iva_cents       INTEGER NOT NULL,
    total_cents     INTEGER NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_sales_day ON sales(day);

CREATE TABLE IF NOT EXISTS sale_items (
    id                INTEGER PRIMARY KEY AUTOINCREMENT,
    sale_id           INTEGER NOT NULL REFERENCES sales(id) ON DELETE CASCADE,
    product_id        INTEGER REFERENCES products(id) ON DELETE SET NULL,
    product_name      TEXT    NOT NULL,                  -- copia: el reporte sobrevive si borras el producto
    quantity          INTEGER NOT NULL CHECK (quantity > 0),
    unit_price_cents  INTEGER NOT NULL,
    unit_cost_cents   INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS day_closures (
    day        TEXT PRIMARY KEY,
    closed_at  TEXT NOT NULL
);
"""

# Dinero en CENTAVOS (enteros) para evitar errores de redondeo con floats.


class Database:
    def __init__(self, path: str = ":memory:"):
        self.path = path
        self._conn: sqlite3.Connection | None = None
        self._lock = threading.RLock()  # Flet puede llamar handlers desde varios hilos

    # ---------- ciclo de vida ----------
    def connect(self) -> None:
        try:
            if self.path != ":memory:":
                folder = os.path.dirname(os.path.abspath(self.path))
                os.makedirs(folder, exist_ok=True)
            self._conn = sqlite3.connect(self.path, check_same_thread=False)
            self._conn.row_factory = sqlite3.Row
            self._conn.execute("PRAGMA foreign_keys = ON")
            self._conn.executescript(SCHEMA)
            self._conn.commit()
        except (sqlite3.Error, OSError) as exc:
            log.exception("No se pudo abrir la base de datos")
            raise DatabaseError("No se pudo abrir la base de datos.") from exc

    def close(self) -> None:
        with self._lock:
            if self._conn is not None:
                self._conn.close()
                self._conn = None

    def _require(self) -> sqlite3.Connection:
        if self._conn is None:
            self.connect()
        return self._conn  # type: ignore[return-value]

    # ---------- escritura: transacción ----------
    @contextmanager
    def transaction(self):
        """with db.transaction() as cur: cur.execute(...)  -> commit o rollback automático."""
        with self._lock:
            conn = self._require()
            cur = conn.cursor()
            try:
                yield cur
                conn.commit()
            except AppError:
                conn.rollback()
                raise
            except sqlite3.IntegrityError as exc:
                conn.rollback()
                if "UNIQUE" in str(exc).upper():
                    raise DuplicateError("Ya existe un producto con ese nombre.") from exc
                log.exception("Violación de integridad")
                raise DatabaseError("Los datos no cumplen las reglas de la base de datos.") from exc
            except sqlite3.Error as exc:
                conn.rollback()
                log.exception("Error de SQLite")
                raise DatabaseError("Error al guardar en la base de datos.") from exc
            except Exception:
                conn.rollback()
                raise
            finally:
                cur.close()  # siempre se libera el cursor

    # ---------- lectura ----------
    def query(self, sql: str, params: tuple = ()) -> list[sqlite3.Row]:
        with self._lock:
            conn = self._require()
            cur = conn.cursor()
            try:
                return cur.execute(sql, params).fetchall()
            except sqlite3.Error as exc:
                log.exception("Error de lectura")
                raise DatabaseError("Error al leer la base de datos.") from exc
            finally:
                cur.close()
