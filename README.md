# Inventario (Flet 0.86.5 · SQLite · MVC)

App de inventario para negocios pequeños, pensada para vivir en el celular.

## Estructura
```
main.py                      entrada: arma Model -> Controller -> View
model/                       SQLite (database, repositories, entities, errors)
controller/                  reglas de negocio (inventario, ventas, reporte, dinero, carrito, excel_export)
view/
  compat.py                  TODO lo que depende de la versión de Flet
  theme.py  ui_guard.py      colores / fábricas de controles / try-except de la UI
  app_view.py                tabs + diseño responsivo
  pages/                     inventory_page · sales_page (Venta) · report_page (Día)
tests/                       pytest (modelo, controlador y humo de la vista)
```

## Ejecutar
```
pip install -r requirements.txt
python main.py                 # ventana tipo celular en PC
flet run --web main.py         # en el navegador
flet build apk                 # APK (la base de datos queda en el almacenamiento del teléfono)
```

## Pruebas
```
pip install -r requirements-dev.txt
pytest
```

## Dónde va cada try / except / finally
| Capa | Qué hace |
|---|---|
| Model (`database.py`) | `try/except sqlite3.Error` + `rollback` + `finally: cursor.close()`; lo convierte en `AppError` |
| Controller | Valida y **lanza** `AppError`. No captura nada |
| View (`ui_guard.py`) | `except AppError` -> aviso rojo; `except Exception` -> log + aviso genérico; `finally: page.update()` |

## Reglas de cálculo
- Dinero en centavos (enteros). IVA 16 % sobre (subtotal − descuento).
- Total cobrado = subtotal − descuento + IVA.
- Ganancia bruta = ventas − costo. Total neto ganado = ganancia bruta − descuentos (el IVA no es ganancia).
- Alerta de stock bajo: cantidad < stock mínimo (aviso + franja roja + ⚠ en la lista).

## Exportar a Excel
Pestaña **Día** -> botón *Exportar a Excel*: abre el selector de archivos del sistema (celular o PC) y guarda `reporte_ventas_AAAA-MM-DD.xlsx` con métricas, productos y resumen financiero (valores numéricos con formato de moneda). Usa `openpyxl` (Python puro, entra en el APK).

## Publicar en Railway (versión web)
1. Sube el proyecto a GitHub (el `.gitignore` ya excluye `data/`).
2. Railway -> New Project -> Deploy from GitHub repo. Usa `requirements.txt` y el `Procfile` (`python main.py`).
3. Agrega un **Volume** al servicio con Mount Path `/data` (sin volumen, SQLite se borra en cada deploy).
   La app guarda ahí `inventario.db` (usa `RAILWAY_VOLUME_MOUNT_PATH`, o define `INVENTARIO_DATA_DIR=/data`).
4. Settings -> Networking -> Generate Domain.
5. Deja el servicio en **1 réplica** (SQLite no se comparte entre réplicas).
La app NO tiene login: cualquiera con la URL puede ver y modificar el inventario.
