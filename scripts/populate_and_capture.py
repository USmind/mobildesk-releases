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

con = get_connection()
cursor = con.cursor()

# Set current BCV exchange rate
cursor.execute("DELETE FROM exchange_rates")
cursor.execute("INSERT INTO exchange_rates (valor, fecha) VALUES (?, datetime('now'))", (900.0,))

# Ensure default category exists and commit
cursor.execute("INSERT OR REPLACE INTO categories (id, nombre, activo) VALUES (1, 'Víveres y Abarrotes', 1)")
con.commit()

# Insert Products
products_data = [
    ("7591058001000", "Harina PAN 1kg", "7591058001000", "Unidad", 0.95, 1.20, 10.0),
    ("7591058002001", "Arroz Primor 1kg", "7591058002001", "Unidad", 0.85, 1.10, 8.0),
    ("7591058003002", "Aceite Vegetal Vatel 1L", "7591058003002", "Unidad", 1.90, 2.40, 5.0),
    ("7591058004003", "Pasta Primor 1kg", "7591058004003", "Unidad", 0.95, 1.30, 10.0),
    ("7591058005004", "Café Fama de América 250g", "7591058005004", "Unidad", 2.20, 2.80, 5.0),
    ("7591058006005", "Azúcar Montalbán 1kg", "7591058006005", "Unidad", 0.90, 1.15, 6.0),
    ("7591058007006", "Mantequilla Mavesa 500g", "7591058007006", "Unidad", 1.70, 2.20, 4.0),
    ("7591058008007", "Leche en Polvo 1kg", "7591058008007", "Unidad", 7.00, 8.50, 3.0),
    ("7591058009008", "Queso Blanco Duro 1kg", "7591058009008", "Kg", 4.20, 5.50, 2.0),
    ("7591058010009", "Refresco Coca-Cola 2L", "7591058010009", "Unidad", 1.80, 2.30, 6.0),
]

for p in products_data:
    cursor.execute("""
        INSERT OR REPLACE INTO products 
        (codigo, nombre, codigo_barras, unidad, costo_usd, precio_usd, stock_minimo, activo, categoria_id)
        VALUES (?, ?, ?, ?, ?, ?, ?, 1, 1)
    """, p)

# Insert initial inventory stock movements
cursor.execute("DELETE FROM inventory_movements")
for row in cursor.execute("SELECT id FROM products").fetchall():
    cursor.execute("""
        INSERT INTO inventory_movements 
        (producto_id, tipo, cantidad, motivo, usuario_id)
        VALUES (?, 'ENTRADA', 30.0, 'Inventario Inicial', 1)
    """, (row[0],))

# Insert Credit Clients (Fiados)
cursor.execute("""
    CREATE TABLE IF NOT EXISTS credit_clients (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre TEXT NOT NULL,
        telefono TEXT,
        limite_credito REAL DEFAULT 0.0,
        saldo_actual REAL DEFAULT 0.0,
        creado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
""")

cursor.execute("DELETE FROM credit_clients")
clients_data = [
    ("Carlos Mendoza", "0414-1234567", 50.0, 14.50),
    ("María Rodríguez", "0424-7654321", 40.0, 8.20),
    ("José González", "0412-9876543", 60.0, 22.00),
    ("Ana Silva", "0416-5554433", 30.0, 5.00),
    ("Pedro Ramírez", "0426-1122334", 45.0, 12.30)
]

for c in clients_data:
    cursor.execute("""
        INSERT INTO credit_clients 
        (nombre, telefono, limite_credito, saldo_actual)
        VALUES (?, ?, ?, ?)
    """, c)

con.commit()
con.close()

from modules.usuarios.session import set_user
user_mock = {"id": 1, "nombre": "Administrador", "username": "admin", "role": "admin"}
set_user(user_mock)

from ui.windows.sales_window import SalesWindow
from ui.windows.inventory_window import UnifiedInventoryWindow
from ui.windows.fiados_window import FiadosWindow

out_cap = Path("outputs/capturas_frescas_hd")
out_cap.mkdir(parents=True, exist_ok=True)

# 1. Sales Window
w_sales = SalesWindow(user_mock)
w_sales.resize(1200, 750)
w_sales.show()
app.processEvents()

# Select products to display in the live sale cart
try:
    from modules.productos.product_service import get_products
    prods = get_products()
    if len(prods) >= 3:
        w_sales.agregar_producto(prods[0])
        w_sales.agregar_producto(prods[2])
        w_sales.agregar_producto(prods[4])
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

print("FRESH_REAL_CAPTURES_SUCCESSFUL_100")
