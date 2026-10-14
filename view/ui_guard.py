"""try / except / finally de la VISTA, en un solo lugar.

    with ui_guard(page):
        controller.hacer_algo()      # si lanza AppError -> aviso rojo; otro error -> se registra

Los errores esperados (AppError) se muestran tal cual; los inesperados se guardan en el log
y el usuario ve un mensaje genérico. El `finally` siempre refresca la pantalla.
"""
import logging
from contextlib import contextmanager

from model.errors import AppError

from . import compat as c

log = logging.getLogger(__name__)


@contextmanager
def ui_guard(page):
    try:
        yield
    except AppError as exc:
        c.show_snack(page, str(exc), error=True)
    except Exception:
        log.exception("Error inesperado en la interfaz")
        c.show_snack(page, "Ocurrió un error inesperado. Intenta de nuevo.", error=True)
    finally:
        page.update()
