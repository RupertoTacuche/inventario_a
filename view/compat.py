"""Capa de compatibilidad con Flet.

Objetivo: que el resto de la app NO dependa de detalles que cambian entre versiones de Flet.
Está escrita para Flet 0.86.5 (API estilo 1.0) y mantiene respaldos para la API clásica
(0.28.x). Si Flet cambia algo en el futuro, solo se toca este archivo.
"""
import logging
import os
import sys

import flet as ft

log = logging.getLogger(__name__)

TARGET_FLET = "0.86.5"
MAX_CONTENT_WIDTH = 900   # en pantallas grandes el contenido se centra con este ancho máximo
COMPACT_BELOW = 600       # menos de 600 px de ancho = modo celular


# ----------------------------------------------------------------- arranque
def run_app(main) -> None:
    """ft.run (0.86.x / 1.0) o ft.app (0.28.x).

    Si existe la variable PORT (Railway y otros hostings la definen) se levanta como
    servidor web en 0.0.0.0:PORT; si no, abre la ventana de escritorio.
    """
    port = os.getenv("PORT")
    if hasattr(ft, "run"):
        if port:
            ft.run(main, view=ft.AppView.WEB_BROWSER, host="0.0.0.0", port=int(port))
        else:
            ft.run(main)
    else:  # pragma: no cover
        ft.app(target=main)


def db_path(filename: str = "inventario.db") -> str:
    """Carpeta de datos persistente.

    Orden: INVENTARIO_DATA_DIR (manual) -> RAILWAY_VOLUME_MOUNT_PATH (volumen de Railway)
    -> FLET_APP_STORAGE_DATA (celular) -> carpeta ./data (PC).
    """
    folder = (os.getenv("INVENTARIO_DATA_DIR") or os.getenv("RAILWAY_VOLUME_MOUNT_PATH")
              or os.getenv("FLET_APP_STORAGE_DATA"))
    if not folder:
        folder = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
    return os.path.join(folder, filename)


def is_mobile(page) -> bool:
    try:
        return page.platform in (ft.PagePlatform.ANDROID, ft.PagePlatform.IOS)
    except Exception:
        return False


def set_desktop_window(page, width: int = 460, height: int = 820) -> None:
    """Tamaño tipo celular al probar en PC. En el teléfono no hace nada."""
    if is_mobile(page):
        return
    try:
        page.window.width = width
        page.window.height = height
        page.window.min_width = 340
    except Exception:  # API distinta o plataforma sin ventana
        log.debug("No se pudo ajustar la ventana", exc_info=True)


# ----------------------------------------------------------------- layout
def is_compact(width) -> bool:
    return bool(width) and width < COMPACT_BELOW


def content_width(width):
    """Ancho del contenido: todo el ancho en celular, máximo 900 px en PC."""
    if not width:
        return MAX_CONTENT_WIDTH
    return min(width, MAX_CONTENT_WIDTH)


def border_all(width, color):
    return ft.Border.all(width, color) if hasattr(ft, "Border") else ft.border.all(width, color)


def pad_all(v):
    return ft.Padding.all(v) if hasattr(ft, "Padding") else ft.padding.all(v)


def pad_sym(horizontal=0, vertical=0):
    if hasattr(ft, "Padding"):
        return ft.Padding.symmetric(horizontal=horizontal, vertical=vertical)
    return ft.padding.symmetric(horizontal=horizontal, vertical=vertical)  # pragma: no cover


def radius(v):
    return ft.BorderRadius.all(v) if hasattr(ft, "BorderRadius") else ft.border_radius.all(v)


def top_center():
    return ft.Alignment.TOP_CENTER if hasattr(ft.Alignment, "TOP_CENTER") else ft.alignment.top_center


def center():
    return ft.Alignment.CENTER if hasattr(ft.Alignment, "CENTER") else ft.alignment.center


# ----------------------------------------------------------------- controles
def button(text, on_click=None, **kwargs):
    """ft.Button (0.86+) o ft.ElevatedButton(text=...) (0.28)."""
    if hasattr(ft, "Button"):
        return ft.Button(content=text, on_click=on_click, **kwargs)
    return ft.ElevatedButton(text=text, on_click=on_click, **kwargs)  # pragma: no cover


def dropdown(options, on_select=None, **kwargs):
    """Dropdown cuyo callback se llama on_select (0.86) u on_change (0.28)."""
    dd = ft.Dropdown(options=options, **kwargs)
    if on_select is not None:
        attr = "on_select" if "on_select" in ft.Dropdown.__dataclass_fields__ else "on_change"
        setattr(dd, attr, on_select)
    return dd


# ----------------------------------------------------------------- avisos y diálogos
def show_snack(page, message: str, error: bool = False, warning: bool = False) -> None:
    bg = "#B91C1C" if error else ("#B45309" if warning else "#15803D")
    snack = ft.SnackBar(content=ft.Text(message, color=ft.Colors.WHITE), bgcolor=bg,
                        duration=4000)
    if hasattr(page, "show_dialog"):
        page.show_dialog(snack)
    else:  # pragma: no cover
        page.open(snack)


def show_dialog(page, dialog) -> None:
    if hasattr(page, "show_dialog"):
        page.show_dialog(dialog)
    else:  # pragma: no cover
        page.open(dialog)


def close_dialog(page, dialog=None) -> None:
    if hasattr(page, "pop_dialog"):
        page.pop_dialog()
    else:  # pragma: no cover
        page.close(dialog)


# ----------------------------------------------------------------- portapapeles y archivos
async def copy_text(page, text: str) -> bool:
    """Copia texto al portapapeles. Devuelve False si la plataforma no lo permite."""
    try:
        clipboard = getattr(page, "clipboard", None)
        if clipboard is not None and hasattr(clipboard, "set"):
            result = clipboard.set(text)
            if hasattr(result, "__await__"):
                await result
            return True
        if hasattr(page, "set_clipboard"):  # pragma: no cover  (0.28)
            page.set_clipboard(text)
            return True
    except Exception:
        log.exception("No se pudo copiar al portapapeles")
    return False


async def save_bytes_file(page, filename: str, data: bytes,
                          dialog_title: str = "Guardar archivo") -> str | None:
    """Abre el selector del sistema para guardar un archivo (celular y escritorio).

    Devuelve la ruta elegida, o None si el usuario cancela.
    """
    picker = ft.FilePicker()
    try:
        if hasattr(page, "services"):
            page.services.append(picker)
        path = await picker.save_file(dialog_title=dialog_title, file_name=filename,
                                      src_bytes=data)
        if getattr(page, "web", False):   # en el navegador se descarga el archivo directo
            return path or filename
        # En escritorio algunos sistemas solo devuelven la ruta: escribimos nosotros.
        if path and not is_mobile(page) and not os.path.exists(path):
            with open(path, "wb") as fh:
                fh.write(data)
        return path
    finally:
        if hasattr(page, "services") and picker in page.services:
            page.services.remove(picker)


async def save_text_file(page, filename: str, text: str) -> str | None:
    return await save_bytes_file(page, filename, text.encode("utf-8"), "Guardar CSV")


def python_version() -> str:
    return sys.version.split()[0]
