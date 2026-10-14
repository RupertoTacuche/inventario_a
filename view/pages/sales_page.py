"""Pestaña 2: captura de la venta (diseño: Capturar venta / Pedido del cliente)."""
import flet as ft

from controller.cart import Cart
from controller.money import IVA_PERCENT, format_money

from .. import compat as c
from .. import theme as t
from ..ui_guard import ui_guard


class SalesPage:
    def __init__(self, page: ft.Page, controller):
        self.page = page
        self.ctl = controller
        self.cart = Cart()
        self.discount_pct = ""          # texto del descuento global aplicado ("" = sin descuento)
        self.compact = False

        self.product = c.dropdown([], label="Producto", expand=True, bgcolor=t.PANEL,
                                  color=t.WHITE, border_color=t.WHITE, text_size=15,
                                  label_style=ft.TextStyle(color=t.MUTED), enable_filter=True)
        self.qty = t.field("Cantidad", integer=True, value="1", width=130)
        self.iva_switch = ft.Switch(value=True, active_color=t.GREEN,
                                    on_change=lambda e: self._update_totals())

        self.empty_text = ft.Text("Aún no hay productos en el pedido.", color=t.WHITE)
        self.rows = ft.Column(spacing=0)
        self.order_box = ft.Container(visible=False, bgcolor=t.BG, border=c.border_all(1, t.WHITE),
                                      border_radius=c.radius(6),
                                      clip_behavior=ft.ClipBehavior.HARD_EDGE, content=self.rows)

        self.l_subtotal = ft.Text("$0.00", color=t.WHITE, text_align=ft.TextAlign.RIGHT)
        self.l_discount = ft.Text("-$0.00", color=t.WHITE, text_align=ft.TextAlign.RIGHT)
        self.l_iva_caption = ft.Text(f"IVA ({IVA_PERCENT}%):", color=t.WHITE, expand=True)
        self.l_iva = ft.Text("$0.00", color=t.WHITE, text_align=ft.TextAlign.RIGHT)
        self.l_total = ft.Text("$0.00", color=t.WHITE, size=32, weight=ft.FontWeight.BOLD)
        self.discount_btn = t.solid_button("Descuento Global (-%)", self.on_discount, t.RED,
                                           ft.Icons.PERCENT)

    # ------------------------------------------------------------ construcción
    def build(self) -> ft.Control:
        line = lambda caption, value: ft.Row(  # noqa: E731
            [ft.Text(caption, color=t.WHITE, expand=True), value])
        return ft.Column(
            [ft.Container(
                border=c.border_all(1, t.WHITE), border_radius=c.radius(12),
                padding=c.pad_all(14),
                content=ft.Column([
                    ft.Text("Capturar venta", color=t.WHITE, weight=ft.FontWeight.BOLD, size=15),
                    ft.Row([self.product]),
                    ft.Row([self.qty, t.light_button("Agregar", self.on_add,
                                                     ft.Icons.ADD_SHOPPING_CART, expand=True)],
                           spacing=12)], spacing=12)),
             ft.Text("Pedido del cliente", color=t.WHITE, size=22, weight=ft.FontWeight.BOLD),
             self.empty_text,
             self.order_box,
             ft.Container(
                 border=c.border_all(1, t.WHITE), border_radius=c.radius(12),
                 padding=c.pad_all(14),
                 content=ft.Column([
                     ft.Row([self.iva_switch, ft.Text(f"Cobrar IVA ({IVA_PERCENT}%)",
                                                      color=t.WHITE)], spacing=4),
                     line("Subtotal:", self.l_subtotal),
                     line("Descuento:", self.l_discount),
                     ft.Row([self.l_iva_caption, self.l_iva]),
                     t.line(t.BLUE),
                     ft.Text("Cuenta final a pagar", color=t.WHITE),
                     self.l_total,
                     ft.Row([t.light_button("Cobrar", self.on_checkout, ft.Icons.POINT_OF_SALE),
                             t.outline_button("Vaciar", self.on_clear, ft.Icons.DELETE_SWEEP)],
                            spacing=10, wrap=True),
                     ft.Row([self.discount_btn])], spacing=10))],
            spacing=12, scroll=ft.ScrollMode.AUTO, expand=True)

    def apply_layout(self, width) -> None:
        self.compact = c.is_compact(width)

    # ------------------------------------------------------------ datos
    def refresh(self) -> None:
        with ui_guard(self.page):
            self._reload_products()
            self._render()

    def _reload_products(self) -> None:
        current = self.product.value
        products = self.ctl.sellable_products()
        self.product.options = [
            ft.DropdownOption(key=str(p.id),
                              text=f"{p.name} · {format_money(p.price_cents)} · stock {p.quantity}")
            for p in products]
        if current not in {str(p.id) for p in products}:
            self.product.value = None

    def _render(self) -> None:
        size = 13 if self.compact else 14
        self.rows.controls = [
            t.table_row(
                [t.cell(i + 1, width=24, align=ft.TextAlign.CENTER, size=size),
                 t.cell(line.name, expand=True, size=size),
                 t.cell(f"x{line.quantity}", width=36, align=ft.TextAlign.CENTER, size=size),
                 t.cell(format_money(line.subtotal_cents), width=76, align=ft.TextAlign.RIGHT,
                        size=size, bold=True),
                 ft.IconButton(ft.Icons.CLOSE, icon_color=t.WHITE, icon_size=18, width=34,
                               on_click=lambda e, idx=i: self.on_remove(idx))], index=i)
            for i, line in enumerate(self.cart.lines)]
        self.order_box.visible = bool(self.cart.lines)
        self.empty_text.visible = not self.cart.lines
        label = f"Descuento Global (-{self.discount_pct}%)" if self.discount_pct else \
            "Descuento Global (-%)"
        self.discount_btn.content = label
        self._update_totals(update=False)

    def _update_totals(self, update: bool = True) -> None:
        totals = self.ctl.preview(self.cart, self.discount_pct, self.iva_switch.value)
        self.l_subtotal.value = format_money(totals.subtotal_cents)
        self.l_discount.value = "-" + format_money(totals.discount_cents)
        self.l_iva.value = format_money(totals.iva_cents)
        self.l_total.value = format_money(totals.total_cents)
        if update:
            self.page.update()

    # ------------------------------------------------------------ acciones
    def on_add(self, e) -> None:
        with ui_guard(self.page):
            self.ctl.add_to_cart(self.cart, self.product.value, self.qty.value)
            self.qty.value = "1"
            self._render()

    def on_remove(self, index: int) -> None:
        with ui_guard(self.page):
            self.cart.remove(index)
            self._render()

    def on_clear(self, e) -> None:
        with ui_guard(self.page):
            self.cart.clear()
            self.discount_pct = ""
            self._render()

    def on_discount(self, e) -> None:
        box = t.field("Descuento (%)", numeric=True, value=self.discount_pct, autofocus=True)

        def apply(ev, value=None):
            with ui_guard(self.page):
                text = box.value if value is None else value
                self.ctl.preview(self.cart, text, True)       # valida (0 a 100)
                self.discount_pct = (text or "").strip().replace("%", "")
                if self.discount_pct in ("0", "0.0"):
                    self.discount_pct = ""
                c.close_dialog(self.page, dlg)
                self._render()

        dlg = ft.AlertDialog(
            modal=True, bgcolor=t.PANEL, title=ft.Text("Descuento global", color=t.WHITE),
            content=box,
            actions=[ft.TextButton("Cancelar", on_click=lambda ev: c.close_dialog(self.page, dlg)),
                     ft.TextButton("Quitar", on_click=lambda ev: apply(ev, "")),
                     ft.TextButton("Aplicar", on_click=apply)])
        c.show_dialog(self.page, dlg)

    def on_checkout(self, e) -> None:
        with ui_guard(self.page):
            charge_iva = self.iva_switch.value
            total = self.ctl.preview(self.cart, self.discount_pct, charge_iva).total_cents
            result = self.ctl.checkout(self.cart, self.discount_pct, charge_iva)
            self.discount_pct = ""
            self._reload_products()
            self._render()
            msg = f"Venta #{result.sale_id} registrada · Cobrar {format_money(total)}"
            if result.low_stock:
                msg += "\n⚠ Stock bajo: " + ", ".join(
                    f"{p.name} ({p.quantity}/{p.min_stock})" for p in result.low_stock)
            c.show_snack(self.page, msg, warning=bool(result.low_stock))
