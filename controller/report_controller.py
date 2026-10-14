"""Reporte diario: consulta, cierre y exportación (CSV / texto)."""
import csv
import io
from datetime import date, datetime, timedelta
from typing import Callable

from model.entities import DailyReport
from model.repositories import SaleRepository

from .money import format_money


class ReportController:
    def __init__(self, sales: SaleRepository, clock: Callable[[], datetime] = datetime.now):
        self.sales = sales
        self.clock = clock

    def today(self) -> date:
        return self.clock().date()

    def report(self, day: date) -> DailyReport:
        return self.sales.daily_report(day.isoformat())

    def close_day(self, day: date) -> DailyReport:
        self.sales.close_day(day.isoformat(), self.clock().isoformat(timespec="seconds"))
        return self.report(day)

    @staticmethod
    def previous_day(day: date) -> date:
        return day - timedelta(days=1)

    @staticmethod
    def next_day(day: date) -> date:
        return day + timedelta(days=1)

    def can_go_next(self, day: date) -> bool:
        return day < self.today()

    @staticmethod
    def to_xlsx(r: DailyReport) -> bytes:
        from .excel_export import build_daily_xlsx
        return build_daily_xlsx(r)

    # ---------- exportación ----------
    @staticmethod
    def to_csv(r: DailyReport) -> str:
        out = io.StringIO()
        w = csv.writer(out, lineterminator="\n")
        w.writerow(["Producto", "Cantidad", "Importe", "Ganancia"])
        for p in r.products:
            w.writerow([p.name, p.quantity, f"{p.revenue_cents / 100:.2f}",
                        f"{p.profit_cents / 100:.2f}"])
        w.writerow([])
        for label, cents in (("Subtotal ventas brutas", r.subtotal_cents),
                             ("IVA 16% colectado", r.iva_cents),
                             ("Descuentos totales", r.discount_cents),
                             ("Ingresos totales", r.total_cents),
                             ("Ganancia bruta", r.gross_profit_cents),
                             ("Total neto ganado", r.net_profit_cents)):
            w.writerow([label, "", f"{cents / 100:.2f}", ""])
        w.writerow(["Transacciones", r.transactions])
        w.writerow(["Fecha", r.day])
        return out.getvalue()

    @staticmethod
    def to_text(r: DailyReport) -> str:
        lines = [f"RESUMEN DE VENTAS DEL DÍA ({r.day})", "=" * 36]
        for i, p in enumerate(r.products, 1):
            lines.append(f"{i}. {p.name} x{p.quantity}  {format_money(p.revenue_cents)}"
                         f"  (gan. {format_money(p.profit_cents)})")
        if not r.products:
            lines.append("Sin ventas registradas.")
        lines += ["-" * 36,
                  f"Subtotal bruto:  {format_money(r.subtotal_cents)}",
                  f"IVA (16%):       {format_money(r.iva_cents)}",
                  f"Descuentos:      {format_money(r.discount_cents)}",
                  f"INGRESOS TOTALES:{format_money(r.total_cents)}",
                  f"Ganancia bruta:  {format_money(r.gross_profit_cents)}",
                  f"TOTAL NETO GANADO: {format_money(r.net_profit_cents)}",
                  f"Transacciones:   {r.transactions}"]
        return "\n".join(lines)
