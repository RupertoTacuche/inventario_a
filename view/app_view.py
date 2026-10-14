"""Arma la ventana: tabs, tema oscuro y diseño responsivo (celular primero)."""
import flet as ft

from . import compat as c
from . import theme as t
from .pages.inventory_page import InventoryPage
from .pages.report_page import ReportPage
from .pages.sales_page import SalesPage
from .ui_guard import ui_guard


def build_app(page: ft.Page, inventory_ctl, sales_ctl, report_ctl) -> None:
    page.title = "Inventario"
    page.theme_mode = ft.ThemeMode.DARK
    page.bgcolor = t.BG
    page.padding = 0
    c.set_desktop_window(page)

    pages = [InventoryPage(page, inventory_ctl), SalesPage(page, sales_ctl),
             ReportPage(page, report_ctl)]
    bodies = [p.build() for p in pages]

    def on_tab_change(e):
        with ui_guard(page):
            pages[e.control.selected_index].refresh()

    tabs = ft.Tabs(
        length=3, selected_index=0, expand=True, on_change=on_tab_change,
        content=ft.Column(expand=True, spacing=0, controls=[
            ft.TabBar(scrollable=False, indicator_color=t.WHITE, label_color=t.WHITE,
                      unselected_label_color=t.MUTED, divider_color=t.WHITE,
                      tabs=[ft.Tab(label="Inventario", icon=ft.Icons.INVENTORY_2),
                            ft.Tab(label="Venta", icon=ft.Icons.POINT_OF_SALE),
                            ft.Tab(label="Día", icon=ft.Icons.BAR_CHART)]),
            ft.TabBarView(expand=True, controls=[
                ft.Container(b, padding=c.pad_all(12)) for b in bodies])]))

    frame = ft.Container(content=tabs, width=c.content_width(page.width))

    def apply_layout(width) -> None:
        frame.width = c.content_width(width)
        for p in pages:
            p.apply_layout(width)

    def on_resize(e=None):
        with ui_guard(page):
            apply_layout(page.width)
            pages[tabs.selected_index].refresh()

    page.on_resize = on_resize
    apply_layout(page.width)
    page.add(ft.SafeArea(expand=True, content=ft.Row(
        [frame], alignment=ft.MainAxisAlignment.CENTER,
        vertical_alignment=ft.CrossAxisAlignment.STRETCH, expand=True)))
    pages[0].refresh()
