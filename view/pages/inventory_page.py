"""Pestaña 1: inventario (CRUD). Lista con ID, nombre, costo, stock mínimo y cantidad."""
import flet as ft

from controller.money import format_money

from .. import compat as c
from .. import theme as t
from ..ui_guard import ui_guard


def _plain(cents: int) -> str:
    return f"{cents / 100:.2f}"


class InventoryPage:
    def __init__(self, page: ft.Page, controller):
        self.page = page
        self.ctl = controller
        self.selected_id: int | None = None
        self.compact = False

        self.name = t.field("Nombre", col={"xs": 12, "md": 4})
        self.cost = t.field("Costo", numeric=True, col={"xs": 6, "md": 2})
        self.price = t.field("Precio venta", numeric=True, col={"xs": 6, "md": 2})
        self.qty = t.field("Cantidad", integer=True, col={"xs": 6, "md": 2})
        self.min_stock = t.field("Stock mínimo", integer=True, col={"xs": 6, "md": 2})
        self.search = t.field("Buscar producto", on_change=lambda e: self.refresh(),
                              prefix_icon=ft.Icons.SEARCH)

        self.alert_text = ft.Text("", color=t.WHITE, size=13)
        self.alert_box = ft.Container(visible=False, bgcolor=t.RED, border_radius=c.radius(6),
                                      padding=c.pad_all(8),
                                      content=ft.Row([ft.Icon(ft.Icons.WARNING_AMBER, color=t.WHITE),
                                                      ft.Container(self.alert_text, expand=True)]))
        self.summary = ft.Text("", color=t.WHITE, size=13, weight=ft.FontWeight.W_600)
        self.rows = ft.Column(spacing=0, scroll=ft.ScrollMode.AUTO, expand=True)
        self.list_box: ft.Container | None = None

        self.add_btn = t.solid_button("Añadir producto", self.on_add, t.GREEN, ft.Icons.ADD)
        self.update_btn = t.solid_button("Actualizar producto", self.on_update, t.AMBER,
                                         ft.Icons.EDIT, disabled=True)
        self.delete_btn = t.solid_button("Eliminar producto", self.on_delete_click, t.RED,
                                         ft.Icons.DELETE, disabled=True)
        self.clear_btn = c.button("Limpiar", on_click=lambda e: self.clear_form(update=True),
                                  color=t.WHITE, icon=ft.Icons.CLOSE)

    # ------------------------------------------------------------ construcción
    def build(self) -> ft.Control:
        header = t.header_row([
            t.cell("ID", width=34, bold=True, align=ft.TextAlign.CENTER),
            t.cell("Nombre", expand=True, bold=True),
            t.cell("Costo", width=70, bold=True, align=ft.TextAlign.RIGHT),
            t.cell("Mín.", width=38, bold=True, align=ft.TextAlign.CENTER),
            t.cell("Cant.", width=44, bold=True, align=ft.TextAlign.CENTER)])
        self.list_box = t.table_box(header, self.rows, height=340)
        return ft.Column(
            [t.title("Gestión de Inventario"),
             t.card("Nuevo / Editar producto",
                    [ft.ResponsiveRow([self.name, self.cost, self.price, self.qty, self.min_stock],
                                      run_spacing=8, spacing=8),
                     ft.Row([self.add_btn, self.clear_btn], wrap=True, spacing=8)]),
             self.alert_box,
             t.card("Lista de productos",
                    [self.search, self.summary, self.list_box,
                     ft.Row([self.delete_btn, self.update_btn], wrap=True, spacing=8,
                            alignment=ft.MainAxisAlignment.END)]),
             ],
            spacing=10, scroll=ft.ScrollMode.AUTO, expand=True)

    def apply_layout(self, width) -> None:
        self.compact = c.is_compact(width)
        if self.list_box is not None:
            self.list_box.height = 300 if self.compact else 380

    # ------------------------------------------------------------ datos
    def refresh(self) -> None:
        with ui_guard(self.page):
            self._render()

    def _render(self) -> None:
        products = self.ctl.list_products(self.search.value or "")
        size = 12 if self.compact else 14
        self.rows.controls = [
            t.table_row(
                [t.cell(p.id, width=34, align=ft.TextAlign.CENTER, size=size),
                 t.cell(("⚠ " if p.is_low else "") + p.name, expand=True, size=size,
                        bold=p.is_low),
                 t.cell(format_money(p.cost_cents), width=70, align=ft.TextAlign.RIGHT, size=size),
                 t.cell(p.min_stock, width=38, align=ft.TextAlign.CENTER, size=size),
                 t.cell(p.quantity, width=44, align=ft.TextAlign.CENTER, size=size, bold=p.is_low)],
                index=i, selected=(p.id == self.selected_id), data=p.id,
                on_click=lambda e, pid=p.id: self.select(pid))
            for i, p in enumerate(products)]
        tot = self.ctl.totals()
        self.summary.value = (f"Productos: {tot.products} · Unidades: {tot.units} · "
                              f"Valor del inventario: {format_money(tot.value_cents)}")
        low = self.ctl.low_stock()
        self.alert_box.visible = bool(low)
        self.alert_text.value = "Stock bajo: " + ", ".join(
            f"{p.name} ({p.quantity}/{p.min_stock})" for p in low)

    def select(self, product_id: int) -> None:
        with ui_guard(self.page):
            p = next(x for x in self.ctl.list_products() if x.id == product_id)
            self.selected_id = p.id
            self.name.value, self.cost.value = p.name, _plain(p.cost_cents)
            self.price.value, self.qty.value = _plain(p.price_cents), str(p.quantity)
            self.min_stock.value = str(p.min_stock)
            self.update_btn.disabled = self.delete_btn.disabled = False
            self._render()

    def clear_form(self, update: bool = False) -> None:
        self.selected_id = None
        for f in (self.name, self.cost, self.price, self.qty, self.min_stock):
            f.value = ""
        self.update_btn.disabled = self.delete_btn.disabled = True
        if update:
            self.refresh()

    def _alert_if_low(self, p) -> None:
        if p.is_low:
            c.show_snack(self.page, f"⚠ Alerta: «{p.name}» tiene {p.quantity} pieza(s), por "
                                    f"debajo del stock mínimo ({p.min_stock}).", warning=True)

    # ------------------------------------------------------------ acciones
    def on_add(self, e) -> None:
        with ui_guard(self.page):
            p = self.ctl.add(self.name.value, self.cost.value, self.price.value,
                             self.qty.value, self.min_stock.value)
            self.clear_form()
            self._render()
            if p.is_low:
                self._alert_if_low(p)
            else:
                c.show_snack(self.page, f"«{p.name}» agregado (ID {p.id}).")

    def on_update(self, e) -> None:
        with ui_guard(self.page):
            if self.selected_id is None:
                c.show_snack(self.page, "Toca un producto de la lista para editarlo.", error=True)
                return
            p = self.ctl.update(self.selected_id, self.name.value, self.cost.value,
                                self.price.value, self.qty.value, self.min_stock.value)
            self.clear_form()
            self._render()
            if p.is_low:
                self._alert_if_low(p)
            else:
                c.show_snack(self.page, f"«{p.name}» actualizado.")

    def on_delete_click(self, e) -> None:
        if self.selected_id is None:
            return
        dlg = ft.AlertDialog(
            modal=True, bgcolor=t.PANEL,
            title=ft.Text("Eliminar producto", color=t.WHITE),
            content=ft.Text(f"¿Eliminar «{self.name.value}»? Esta acción no se puede deshacer.",
                            color=t.WHITE),
            actions=[ft.TextButton("Cancelar", on_click=lambda ev: c.close_dialog(self.page, dlg)),
                     ft.TextButton("Eliminar", on_click=lambda ev: self._confirm_delete(dlg),
                                   style=ft.ButtonStyle(color=t.RED))])
        c.show_dialog(self.page, dlg)

    def _confirm_delete(self, dlg) -> None:
        with ui_guard(self.page):
            c.close_dialog(self.page, dlg)
            self.ctl.delete(self.selected_id)
            self.clear_form()
            self._render()
            c.show_snack(self.page, "Producto eliminado.")
