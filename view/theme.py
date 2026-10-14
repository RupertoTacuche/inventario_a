"""Colores y fábricas de controles: fondo azul marino, letras y marcos blancos."""
import flet as ft

from . import compat as c

BG = "#0A1A33"          # azul marino oscuro
PANEL = "#0D2244"
ROW_STRONG = "#1B4DB3"  # azul fuerte
ROW_LIGHT = "#4A8EE8"   # azul claro
HEADER = "#102F63"
WHITE = ft.Colors.WHITE
MUTED = "#B8C7E0"
GREEN = "#16A34A"
RED = "#DC2626"
AMBER = "#D97706"
BLUE = "#2563EB"
ACCENT = "#7DD3FC"


def title(text: str) -> ft.Text:
    return ft.Text(text, size=22, weight=ft.FontWeight.BOLD, color=WHITE,
                   text_align=ft.TextAlign.CENTER)


def label(text: str, **kw) -> ft.Text:
    return ft.Text(text, color=kw.pop("color", WHITE), **kw)


def field(label_text: str, numeric: bool = False, integer: bool = False, **kw) -> ft.TextField:
    if numeric or integer:
        kw.setdefault("keyboard_type", ft.KeyboardType.NUMBER)
    if integer:
        kw.setdefault("input_filter", ft.NumbersOnlyInputFilter())
    return ft.TextField(
        label=label_text, color=WHITE, bgcolor=PANEL, border_color=WHITE,
        focused_border_color=ACCENT, cursor_color=WHITE, dense=True, text_size=14,
        label_style=ft.TextStyle(color=MUTED), content_padding=c.pad_sym(10, 8), **kw)


def card(heading: str, controls: list, **kw) -> ft.Container:
    """Marco blanco con título (como el LabelFrame de las capturas)."""
    return ft.Container(
        border=c.border_all(1, WHITE), border_radius=c.radius(8), padding=c.pad_all(10),
        content=ft.Column([ft.Text(heading, color=WHITE, weight=ft.FontWeight.W_600, size=14),
                           *controls], spacing=8, tight=True), **kw)


def cell(text, width=None, expand=False, align=ft.TextAlign.LEFT, bold=False,
         size=13, color=WHITE) -> ft.Container:
    return ft.Container(
        width=width, expand=expand,
        content=ft.Text(str(text), size=size, color=color, no_wrap=True, text_align=align,
                        overflow=ft.TextOverflow.ELLIPSIS,
                        weight=ft.FontWeight.BOLD if bold else ft.FontWeight.NORMAL))


def stripe(index: int) -> str:
    """Líneas azules fuertes y claras alternadas."""
    return ROW_STRONG if index % 2 == 0 else ROW_LIGHT


def table_row(cells: list, index: int, selected: bool = False, on_click=None,
              data=None) -> ft.Container:
    return ft.Container(
        bgcolor=stripe(index), data=data, on_click=on_click, ink=on_click is not None,
        padding=c.pad_sym(6, 7),
        border=c.border_all(2, AMBER if selected else stripe(index)),
        content=ft.Row(cells, spacing=4, vertical_alignment=ft.CrossAxisAlignment.CENTER))


def header_row(cells: list) -> ft.Container:
    return ft.Container(bgcolor=HEADER, padding=c.pad_sym(6, 8),
                        border=ft.Border(bottom=ft.BorderSide(1, WHITE)),
                        content=ft.Row(cells, spacing=4))


def table_box(header: ft.Control, rows_column: ft.Column, height: int) -> ft.Container:
    """Cuadro con marco blanco: encabezado fijo + filas con scroll."""
    return ft.Container(
        height=height, bgcolor=BG, border=c.border_all(1, WHITE),
        border_radius=c.radius(6), clip_behavior=ft.ClipBehavior.HARD_EDGE,
        content=ft.Column([header, ft.Container(expand=True, content=rows_column)],
                          spacing=0, expand=True))


def solid_button(text, on_click, color, icon=None, **kw):
    return c.button(text, on_click=on_click, bgcolor=color, color=WHITE, icon=icon, **kw)


def outline_box(controls: list) -> ft.Container:
    return ft.Container(border=c.border_all(1, WHITE), border_radius=c.radius(6),
                        padding=c.pad_all(10),
                        content=ft.Column(controls, spacing=4, tight=True))


def money_line(caption: str, value: str, bold=False, size=13) -> ft.Row:
    w = ft.FontWeight.BOLD if bold else ft.FontWeight.NORMAL
    return ft.Row([ft.Text(caption, color=WHITE, size=size, weight=w, expand=True),
                   ft.Text(value, color=WHITE, size=size, weight=w,
                           text_align=ft.TextAlign.RIGHT)])


DARK_TEXT = "#0A1A33"


def light_button(text, on_click, icon=None, **kw):
    """Botón blanco con letras oscuras (Agregar, Cobrar)."""
    return c.button(text, on_click=on_click, bgcolor=WHITE, color=DARK_TEXT, icon=icon, **kw)


def outline_button(text, on_click, icon=None, **kw):
    """Botón transparente con marco blanco (Vaciar, Hoy...)."""
    return c.button(text, on_click=on_click, bgcolor=ft.Colors.TRANSPARENT, color=WHITE,
                    icon=icon, style=ft.ButtonStyle(side=ft.BorderSide(1, WHITE)), **kw)


def line(color: str = ROW_LIGHT) -> ft.Container:
    return ft.Container(height=1, bgcolor=color)
