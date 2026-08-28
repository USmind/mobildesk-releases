import sys
from pathlib import Path

proj_dir = Path("MobilDesk POS").resolve()
sys.path.insert(0, str(proj_dir))

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt

app = QApplication.instance() or QApplication(sys.argv)

from main import APP_STYLE
app.setStyleSheet(APP_STYLE)

from database.connection import get_connection
from modules.productos.product_service import create_product
from modules.usuarios.session import set_user

user_mock = {"id": 1, "nombre": "Administrador", "username": "admin", "role": "admin"}
set_user(user_mock)

# Update BCV exchange rate
con = get_connection()
con.execute("DELETE FROM exchange_rates")
con.execute("INSERT INTO exchange_rates (valor, fecha) VALUES (?, datetime('now'))", (900.0,))
con.commit()
con.close()

# Populate sample products using the official service
items_to_add = [
    ("7591058001000", "Harina PAN 1kg", "Unidad", 1.20, 40.0),
    ("7591058002001", "Arroz Primor 1kg", "Unidad", 1.10, 35.0),
    ("7591058003002", "Aceite Vegetal Vatel 1L", "Unidad", 2.40, 25.0),
    ("7591058004003", "Pasta Primor 1kg", "Unidad", 1.30, 45.0),
    ("7591058005004", "Café Fama de América 250g", "Unidad", 2.80, 20.0),
    ("7591058006005", "Azúcar Montalbán 1kg", "Unidad", 1.15, 30.0),
    ("7591058007006", "Mantequilla Mavesa 500g", "Unidad", 2.20, 18.0),
    ("7591058008007", "Leche en Polvo 1kg", "Unidad", 8.50, 15.0),
    ("7591058009008", "Queso Blanco Duro", "Kg", 5.50, 12.0),
    ("7591058010009", "Refresco Coca-Cola 2L", "Unidad", 2.30, 24.0),
]

for cod, nom, uni, pre, stk in items_to_add:
    try:
        create_product(cod, nom, uni, pre, stk, None, 5, cod)
    except Exception as e:
        pass

# Populate credit clients
con = get_connection()
con.execute("""
    CREATE TABLE IF NOT EXISTS credit_clients (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre TEXT NOT NULL,
        telefono TEXT,
        limite_credito REAL DEFAULT 0.0,
        saldo_actual REAL DEFAULT 0.0,
        creado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
""")
con.execute("DELETE FROM credit_clients")
for c in [
    ("Carlos Mendoza", "0414-1234567", 50.0, 14.50),
    ("María Rodríguez", "0424-7654321", 40.0, 8.20),
    ("José González", "0412-9876543", 60.0, 22.00),
    ("Ana Silva", "0416-5554433", 30.0, 5.00),
    ("Pedro Ramírez", "0426-1122334", 45.0, 12.30)
]:
    con.execute("INSERT INTO credit_clients (nombre, telefono, limite_credito, saldo_actual) VALUES (?, ?, ?, ?)", c)
con.commit()
con.close()

from ui.windows.sales_window import SalesWindow
from ui.windows.inventory_window import UnifiedInventoryWindow
from ui.windows.fiados_window import FiadosWindow

out_cap = Path("outputs/capturas_frescas_hd")
out_cap.mkdir(parents=True, exist_ok=True)

# 1. Sales Window with items added to the cart
w_sales = SalesWindow(user_mock)
w_sales.resize(1200, 750)
w_sales.show()
app.processEvents()

try:
    w_sales.producto.setText("Harina PAN 1kg")
    w_sales.cantidad.setText("2")
    w_sales.agregar_producto()
    
    w_sales.producto.setText("Aceite Vegetal Vatel 1L")
    w_sales.cantidad.setText("1")
    w_sales.agregar_producto()
    
    w_sales.producto.setText("Café Fama de América 250g")
    w_sales.cantidad.setText("1")
    w_sales.agregar_producto()
except Exception as e:
    print("Sales populate error:", e)

app.processEvents()
w_sales.grab().save(str(out_cap / "pos_ventas_real.png"))
w_sales.close()

# 2. Inventory Window (Clean emojis, full populated list)
w_inv = UnifiedInventoryWindow(user_mock)
w_inv.resize(1200, 750)
w_inv.show()
app.processEvents()
w_inv.grab().save(str(out_cap / "pos_inventario_real.png"))
w_inv.close()

# 3. Fiados Window (5 populated debtors)
w_fiados = FiadosWindow()
w_fiados.resize(1200, 750)
w_fiados.show()
app.processEvents()
w_fiados.grab().save(str(out_cap / "pos_fiados_real.png"))
w_fiados.close()

print("ALL_FRESH_REAL_SCREENSHOTS_CAPTURED_SUCCESSFULLY")
