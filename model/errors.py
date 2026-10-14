"""Errores propios de la app.

Regla de oro (dónde va cada try/except/finally):
  * MODEL      -> captura sqlite3.Error, hace rollback y lo convierte en AppError.
  * CONTROLLER -> valida datos y LANZA AppError con mensajes claros. No captura nada.
  * VIEW       -> captura AppError (se muestra al usuario) y Exception (se registra).
"""


class AppError(Exception):
    """Error esperado: su mensaje se puede mostrar tal cual al usuario."""


class ValidationError(AppError):
    """Dato capturado inválido (vacío, negativo, no numérico...)."""


class NotFoundError(AppError):
    """El registro ya no existe."""


class DuplicateError(AppError):
    """Ya existe un registro con ese valor único."""


class InsufficientStockError(AppError):
    """No hay existencias suficientes para la venta."""


class DatabaseError(AppError):
    """Falla de SQLite (disco lleno, archivo dañado, etc.)."""
