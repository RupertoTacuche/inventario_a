"""Pestaña 3 «Día»: resumen de ventas del día + exportar a Excel."""
from datetime import date

import flet as ft

from controller.money import IVA_PERCENT, format_money

from .. import compat as c
from .. import theme as t
from ..ui_guard import ui_guard


def _card(heading: str, controls: list) -> ft.Container:
    return ft.Container(
        border=c.border_all(1, t.WHITE), border_radius=c.radius(12), padding=c.pad_all(14),
        content=ft.Column([ft.Text(heading, color=t.WHITE, size=16), *controls], spacing=8))


def _line(caption: str, value: str, bold: bool = False) -> ft.Row:
    w = ft.FontWeight.BOLD if bold else ft.FontWeight.NORMAL
    return ft.Row([ft.Text(caption, color=t.WHITE, size=13, weight=w, expand=True),
                   ft.Text(value, color=t.WHITE, size=13, weight=w,
                           text_align=ft.TextAlign.RIGHT)])


class ReportPage:
    def __init__(self, page: ft.Page, controller):
        self.page = page
        self.ctl = controller
        self.day: date = controller.today()
        self.compact = False
        self.report = None

        self.heading = ft.Text("", color=t.WHITE, size=24, weight=ft.FontWeight.BOLD,
                               text_align=ft.TextAlign.CENTER)
        self.status = ft.Text("", color=t.ACCENT, size=13, weight=ft.FontWeight.W_600,
                              text_align=ft.TextAlign.CENTER)
        self.metrics = ft.Column(spacing=6)
        self.products = ft.Column(spacing=6)
        self.fin = ft.Column(spacing=4)
        self.net = ft.Text("", color=t.WHITE, size=26, weight=ft.FontWeight.BOLD)
        self.next_btn = t.outline_button("Día siguiente", self.on_next, ft.Icons.CHEVRON_RIGHT,
                                         expand=True)
        self.today_btn = t.outline_button("Hoy", self.on_today, ft.Icons.TODAY, expand=True)

    def build(self) -> ft.Control:
        print_btn = t.solid_button("Imprimir informe de ventas", self.on_print, "#1E5F74",
                                   ft.Icons.PRINT, expand=True)
        close_btn = t.solid_button("Cerrar día y finalizar informe", self.on_close_day,
                                   "#0F766E", ft.Icons.LOCK_CLOCK, expand=True)
        prev_btn = c.button("CONSULTAR DÍA ANTERIOR", on_click=self.on_previous,
                            bgcolor="#D9DCE1", color="#1F2937", icon=ft.Icons.CHEVRON_LEFT,
                            expand=True)
        export_btn = t.solid_button("Exportar a Excel", self.on_export, t.GREEN,
                                    ft.Icons.TABLE_CHART, expand=True)
        return ft.Column(
            [self.heading, self.status,
             _card("Métricas Clave del Día", [self.metrics]),
             _card("Productos Vendidos y Ganancia", [self.products]),
             _card("Resumen Financiero Diario",
                   [self.fin, t.line(t.WHITE),
                    ft.Row([ft.Text("TOTAL NETO GANADO:", color=t.WHITE, size=15,
                                    weight=ft.FontWeight.BOLD), self.net], wrap=True,
                           spacing=10)]),
             ft.Row([print_btn]),
             ft.Row([close_btn]),
             ft.Row([prev_btn]),
             ft.Row([self.next_btn, self.today_btn], spacing=10),
             ft.Row([export_btn])],
            spacing=12, scroll=ft.ScrollMode.AUTO, expand=True,
            horizontal_alignment=ft.CrossAxisAlignment.STRETCH)

    def apply_layout(self, width) -> None:
        self.compact = c.is_compact(width)

    # ------------------------------------------------------------ datos
    def refresh(self) -> None:
        with ui_guard(self.page):
            self._render()

    def _render(self) -> None:
        r = self.report = self.ctl.report(self.day)
        self.heading.value = f"RESUMEN DE VENTAS DEL DÍA ({self.day.strftime('%d/%m/%Y')})"
        self.metrics.controls = [
            self._metric("Total Vendido (Ingresos):", format_money(r.total_cents)),
            self._metric("Total Ganancia (Neto):", format_money(r.net_profit_cents)),
            self._metric("Número de Transacciones:", str(r.transactions))]

        rows: list[ft.Control] = []
        for i, p in enumerate(r.products, 1):
            rows.append(ft.Row([
                ft.Column([ft.Text(f"{i}. {p.name}", color=t.WHITE, size=15,
                                   weight=ft.FontWeight.BOLD),
                           ft.Text(f"x{p.quantity} - {format_money(p.revenue_cents)}",
                                   color=t.MUTED, size=12)], spacing=2, expand=True),
                ft.Text(format_money(p.profit_cents), color=t.WHITE, size=16,
                        weight=ft.FontWeight.BOLD)],
                vertical_alignment=ft.CrossAxisAlignment.CENTER))
            rows.append(t.line())
        if not rows:
            rows.append(ft.Text("Sin ventas registradas este día.", color=t.MUTED))
        self.products.controls = rows

        self.fin.controls = [
            _line("Unidades vendidas:", str(r.units_sold)),
            _line("Subtotal de ventas brutas:", format_money(r.subtotal_cents)),
            _line(f"IVA ({IVA_PERCENT}%) colectado:", format_money(r.iva_cents)),
            _line("Descuentos totales:", "-" + format_money(r.discount_cents)),
            _line("INGRESOS TOTALES (ventas + IVA − desc.):", format_money(r.total_cents)),
            _line("Costo de lo vendido:", format_money(r.cost_cents)),
            _line("Ganancia bruta (ventas − costo):", format_money(r.gross_profit_cents))]
        self.net.value = format_money(r.net_profit_cents)
        self.status.value = "DÍA CERRADO ✔" if r.closed else ""
        self.next_btn.disabled = not self.ctl.can_go_next(self.day)
        self.today_btn.disabled = self.day == self.ctl.today()

    @staticmethod
    def _metric(caption: str, value: str) -> ft.Row:
        return ft.Row([ft.Text(caption, color=t.WHITE), ft.Text(value, color=t.WHITE,
                                                                weight=ft.FontWeight.BOLD)],
                      spacing=6, wrap=True)

    # ------------------------------------------------------------ acciones
    def on_previous(self, e) -> None:
        with ui_guard(self.page):
            self.day = self.ctl.previous_day(self.day)
            self._render()

    def on_next(self, e) -> None:
        with ui_guard(self.page):
            if self.ctl.can_go_next(self.day):
                self.day = self.ctl.next_day(self.day)
            self._render()

    def on_today(self, e) -> None:
        with ui_guard(self.page):
            self.day = self.ctl.today()
            self._render()

    def on_close_day(self, e) -> None:
        with ui_guard(self.page):
            self.ctl.close_day(self.day)
            self._render()
            c.show_snack(self.page, "Día cerrado. El informe quedó finalizado.")

    def on_print(self, e) -> None:
        """El celular no imprime directo: mostramos el informe listo para copiar o compartir."""
        with ui_guard(self.page):
            text = self.ctl.to_text(self.ctl.report(self.day))
            dlg = ft.AlertDialog(
                modal=True, bgcolor=t.PANEL, scrollable=True,
                title=ft.Text("Informe de ventas", color=t.WHITE),
                content=ft.Text(text, color=t.WHITE, size=12, selectable=True,
                                font_family="monospace"),
                actions=[ft.TextButton("Copiar", on_click=lambda ev: self._copy_and_close(dlg, text)),
                         ft.TextButton("Cerrar", on_click=lambda ev: c.close_dialog(self.page, dlg))])
            c.show_dialog(self.page, dlg)

    async def _copy_and_close(self, dlg, text: str) -> None:
        ok = await c.copy_text(self.page, text)
        with ui_guard(self.page):
            c.close_dialog(self.page, dlg)
            c.show_snack(self.page, "Informe copiado." if ok else "No se pudo copiar.",
                         error=not ok)

    async def on_export(self, e) -> None:
        with ui_guard(self.page):
            data = self.ctl.to_xlsx(self.ctl.report(self.day))
            path = await c.save_bytes_file(
                self.page, f"reporte_ventas_{self.day.isoformat()}.xlsx", data,
                dialog_title="Guardar reporte en Excel")
            c.show_snack(self.page, "Reporte de Excel guardado." if path
                         else "Exportación cancelada.", warning=not path)
