import sys
from pathlib import Path
from PySide6.QtCore import Qt, QRectF, QPointF
from PySide6.QtGui import (
    QImage, QPainter, QFont, QColor, QLinearGradient, QRadialGradient,
    QBrush, QPen
)
from PySide6.QtWidgets import QApplication

app = QApplication.instance() or QApplication(sys.argv)
out_dir = Path("outputs")
out_dir.mkdir(parents=True, exist_ok=True)

cap_dir = Path("outputs/capturas_frescas_hd")
img_sales_real = str(cap_dir / "pos_ventas_real.png")
img_inv_real = str(cap_dir / "pos_inventario_real.png")
img_fiados_real = str(cap_dir / "pos_fiados_real.png")

# Generate Pixel-Perfect Native Mobile App UI
def create_native_mobile_app_image(w=580, h=900):
    img = QImage(w, h, QImage.Format_ARGB32)
    img.fill(QColor("#f8fafc"))
    p = QPainter(img)
    p.setRenderHint(QPainter.Antialiasing)
    p.setRenderHint(QPainter.TextAntialiasing)

    # Top App Bar (Material Navy Blue)
    p.setBrush(QBrush(QColor("#1e3a8a")))
    p.setPen(Qt.NoPen)
    p.drawRect(0, 0, w, 110)

    # App Bar Title
    p.setFont(QFont("Segoe UI", 19, QFont.Bold))
    p.setPen(QColor("#ffffff"))
    p.drawText(QRectF(20, 45, w - 40, 30), Qt.AlignLeft | Qt.AlignVCenter, "📱 MobilDesk App")

    # Rate Badge in App Bar
    p.setFont(QFont("Segoe UI", 13, QFont.Bold))
    p.setPen(QColor("#fbbf24"))
    p.drawText(QRectF(20, 78, w - 40, 24), Qt.AlignLeft, "Tasa BCV: 1 USD = 900.00 Bs")

    # Search Bar
    p.setBrush(QBrush(QColor("#ffffff")))
    p.setPen(QPen(QColor("#cbd5e1"), 1.5))
    p.drawRoundedRect(QRectF(18, 125, w - 36, 44), 10, 10)
    p.setFont(QFont("Segoe UI", 13, QFont.Normal))
    p.setPen(QColor("#64748b"))
    p.drawText(QRectF(34, 125, w - 68, 44), Qt.AlignLeft | Qt.AlignVCenter, "🔍 Buscar producto o escanear...")

    # Product Cards
    products = [
        ("Harina PAN 1kg", "7591058001000", "$1.20 USD", "Bs 1,080.00", "Stock: 40 Uni", "#15803d", "#dcfce7"),
        ("Arroz Primor 1kg", "7591058002001", "$1.10 USD", "Bs 990.00", "Stock: 35 Uni", "#15803d", "#dcfce7"),
        ("Aceite Vegetal Vatel 1L", "7591058003002", "$2.40 USD", "Bs 2,160.00", "Stock: 25 Uni", "#15803d", "#dcfce7"),
        ("Café Fama de América 250g", "7591058005004", "$2.80 USD", "Bs 2,520.00", "Stock: 20 Uni", "#15803d", "#dcfce7"),
        ("Mantequilla Mavesa 500g", "7591058007006", "$2.20 USD", "Bs 1,980.00", "Stock: 18 Uni", "#15803d", "#dcfce7"),
        ("Leche en Polvo 1kg", "7591058008007", "$8.50 USD", "Bs 7,650.00", "Stock: 15 Uni", "#15803d", "#dcfce7"),
    ]

    card_y = 185
    card_h = 100
    for name, code, usd, bs, stock, st_color, st_bg in products:
        p.setBrush(QBrush(QColor("#ffffff")))
        p.setPen(QPen(QColor("#e2e8f0"), 1.5))
        p.drawRoundedRect(QRectF(18, card_y, w - 36, card_h), 12, 12)

        # Name
        p.setFont(QFont("Segoe UI", 15, QFont.Bold))
        p.setPen(QColor("#0f172a"))
        p.drawText(QRectF(32, card_y + 12, w - 160, 24), Qt.AlignLeft, name)

        # Barcode
        p.setFont(QFont("Segoe UI", 11, QFont.Normal))
        p.setPen(QColor("#64748b"))
        p.drawText(QRectF(32, card_y + 38, w - 160, 18), Qt.AlignLeft, f"Cód: {code}")

        # Prices
        p.setFont(QFont("Segoe UI", 15, QFont.Black))
        p.setPen(QColor("#1e3a8a"))
        p.drawText(QRectF(32, card_y + 60, 140, 26), Qt.AlignLeft, usd)

        p.setFont(QFont("Segoe UI", 13, QFont.Bold))
        p.setPen(QColor("#15803d"))
        p.drawText(QRectF(160, card_y + 62, 160, 24), Qt.AlignLeft, bs)

        # Stock Pill Badge
        p.setBrush(QBrush(QColor(st_bg)))
        p.setPen(Qt.NoPen)
        p.drawRoundedRect(QRectF(w - 150, card_y + 30, 118, 32), 16, 16)
        p.setFont(QFont("Segoe UI", 12, QFont.Bold))
        p.setPen(QColor(st_color))
        p.drawText(QRectF(w - 150, card_y + 30, 118, 32), Qt.AlignCenter, stock)

        card_y += 112

    p.end()
    return img

img_mobile_fresh = create_native_mobile_app_image()

W, H = 1080, 1920

def create_base_canvas(width=W, height=H):
    img = QImage(width, height, QImage.Format_ARGB32)
    img.fill(QColor("#020617"))
    p = QPainter(img)
    p.setRenderHint(QPainter.Antialiasing)
    p.setRenderHint(QPainter.TextAntialiasing)
    p.setRenderHint(QPainter.SmoothPixmapTransform)

    # Ambient deep dark background
    g = QLinearGradient(0, 0, 0, height)
    g.setColorAt(0.0, QColor("#020617"))
    g.setColorAt(0.35, QColor("#0b172e"))
    g.setColorAt(0.75, QColor("#060e1d"))
    g.setColorAt(1.0, QColor("#020617"))
    p.fillRect(0, 0, width, height, g)

    # Top Glow
    rad = QRadialGradient(width / 2, 200, 520)
    rad.setColorAt(0.0, QColor(37, 99, 235, 70))
    rad.setColorAt(0.7, QColor(14, 165, 233, 22))
    rad.setColorAt(1.0, QColor(0, 0, 0, 0))
    p.fillRect(0, 0, width, min(750, height), rad)

    return img, p

def draw_top_badge(p, text, color="#38bdf8", y=110, width=W):
    w = 840
    h = 56
    x = (width - w) / 2
    p.setBrush(QBrush(QColor("#0f172a")))
    p.setPen(QPen(QColor(color), 2.5))
    p.drawRoundedRect(QRectF(x, y, w, h), 20, 20)

    p.setFont(QFont("Segoe UI", 21, QFont.Bold))
    p.setPen(QColor(color))
    p.drawText(QRectF(x, y, w, h), Qt.AlignCenter, text)

def draw_header_title(p, title, y=185, h=135, size=46, width=W):
    p.setFont(QFont("Segoe UI", size, QFont.Black))
    p.setPen(QColor("#ffffff"))
    p.drawText(QRectF(60, y, width - 120, h), Qt.AlignCenter | Qt.TextWordWrap, title)

def draw_pc_screen(p, path, x=60, y=360, w=960, h=930, title="💻 MobilDesk POS · Software para PC"):
    p.save()
    p.setBrush(QBrush(QColor(0, 0, 0, 190)))
    p.setPen(Qt.NoPen)
    p.drawRoundedRect(QRectF(x + 10, y + 14, w, h), 24, 24)

    p.setBrush(QBrush(QColor("#0f172a")))
    p.setPen(QPen(QColor("#38bdf8"), 3))
    p.drawRoundedRect(QRectF(x, y, w, h), 24, 24)

    bar_h = 48
    p.setBrush(QBrush(QColor("#172554")))
    p.setPen(Qt.NoPen)
    p.drawRoundedRect(QRectF(x, y, w, bar_h), 24, 24)
    p.drawRect(QRectF(x, y + 24, w, bar_h - 24))

    p.setBrush(QBrush(QColor("#ef4444")))
    p.drawEllipse(QPointF(x + 24, y + 24), 6, 6)
    p.setBrush(QBrush(QColor("#eab308")))
    p.drawEllipse(QPointF(x + 44, y + 24), 6, 6)
    p.setBrush(QBrush(QColor("#22c55e")))
    p.drawEllipse(QPointF(x + 64, y + 24), 6, 6)

    p.setFont(QFont("Segoe UI", 18, QFont.Bold))
    p.setPen(QColor("#93c5fd"))
    p.drawText(QRectF(x + 85, y + 12, w - 100, 26), Qt.AlignLeft, title)

    src = QImage(path)
    if not src.isNull():
        clip = QRectF(x + 3, y + bar_h, w - 6, h - bar_h - 3)
        p.setClipRect(clip)
        p.drawImage(clip, src)

    p.restore()

def draw_smartphone(p, qimg_src, phone_x=230, phone_y=360, phone_w=620, phone_h=930):
    p.save()
    p.setBrush(QBrush(QColor(0, 0, 0, 210)))
    p.setPen(Qt.NoPen)
    p.drawRoundedRect(QRectF(phone_x + 12, phone_y + 16, phone_w, phone_h), 56, 56)

    p.setBrush(QBrush(QColor("#1e293b")))
    p.setPen(QPen(QColor("#38bdf8"), 6))
    p.drawRoundedRect(QRectF(phone_x, phone_y, phone_w, phone_h), 56, 56)

    screen_rect = QRectF(phone_x + 14, phone_y + 14, phone_w - 28, phone_h - 28)
    p.setBrush(QBrush(QColor("#0f172a")))
    p.setPen(Qt.NoPen)
    p.drawRoundedRect(screen_rect, 44, 44)

    p.setClipRect(screen_rect)
    if not qimg_src.isNull():
        p.drawImage(screen_rect, qimg_src)

    p.setClipRect(QRectF(0, 0, W, H))

    notch_w = 170
    notch_h = 24
    notch_x = phone_x + (phone_w - notch_w) / 2
    p.setBrush(QBrush(QColor("#0f172a")))
    p.setPen(Qt.NoPen)
    p.drawRoundedRect(QRectF(notch_x, phone_y + 20, notch_w, notch_h), 12, 12)

    p.setBrush(QBrush(QColor("#1e3a8a")))
    p.drawEllipse(QPointF(notch_x + 35, phone_y + 32), 5, 5)

    bar_w = 180
    bar_h = 6
    bar_x = phone_x + (phone_w - bar_w) / 2
    p.setBrush(QBrush(QColor(255, 255, 255, 180)))
    p.drawRoundedRect(QRectF(bar_x, phone_y + phone_h - 26, bar_w, bar_h), 3, 3)

    p.restore()

def draw_bottom_highlight(p, main_text, sub_text="", y=1330):
    box_w = 960
    box_h = 160
    box_x = (W - box_w) / 2

    p.setBrush(QBrush(QColor("#0d1b38")))
    p.setPen(QPen(QColor("#2563eb"), 2.5))
    p.drawRoundedRect(QRectF(box_x, y, box_w, box_h), 22, 22)

    p.setFont(QFont("Segoe UI", 26, QFont.Bold))
    p.setPen(QColor("#fbbf24"))
    p.drawText(QRectF(box_x + 30, y + 25, box_w - 60, 45), Qt.AlignCenter, main_text)

    if sub_text:
        p.setFont(QFont("Segoe UI", 21, QFont.Medium))
        p.setPen(QColor("#e2e8f0"))
        p.drawText(QRectF(box_x + 30, y + 80, box_w - 60, 55), Qt.AlignCenter | Qt.TextWordWrap, sub_text)

def draw_footer_cta(p, slide_num, total_slides=6, cta_text="👉 Desliza para ver más ➡️"):
    p.setFont(QFont("Segoe UI", 24, QFont.Bold))
    p.setPen(QColor("#38bdf8"))
    p.drawText(QRectF(0, 1530, W, 40), Qt.AlignCenter, cta_text)

    p.setFont(QFont("Segoe UI", 18, QFont.DemiBold))
    p.setPen(QColor("#64748b"))
    p.drawText(QRectF(0, 1580, W, 30), Qt.AlignCenter, f"Slide {slide_num} de {total_slides} · MobilDesk POS")


# ==============================================================================
# 1. FLYER PRINCIPAL DE MARKETING (1080x1920)
# ==============================================================================
img_f, pf = create_base_canvas()
draw_top_badge(pf, "💎 SISTEMA DE VENTAS POS & APP MÓVIL 🇻🇪", "#fbbf24", 100)
draw_header_title(pf, "Digitaliza tu negocio hoy mismo sin pagar mensualidades", 170, 120, 44)

card_y = 305
card_h = 820
pf.setBrush(QBrush(QColor("#0d1b38")))
pf.setPen(QPen(QColor("#fbbf24"), 4.5))
pf.drawRoundedRect(QRectF(70, card_y, 940, card_h), 26, 26)

pf.setFont(QFont("Segoe UI", 24, QFont.Bold))
pf.setPen(QColor("#93c5fd"))
pf.drawText(QRectF(70, card_y + 22, 940, 34), Qt.AlignCenter, "OFERTA ESTRELLA: LICENCIA VITALICIA")

pf.setFont(QFont("Segoe UI", 85, QFont.Black))
pf.setPen(QColor("#fbbf24"))
pf.drawText(QRectF(70, card_y + 58, 940, 95), Qt.AlignCenter, "$15 USD")

pf.setFont(QFont("Segoe UI", 23, QFont.Bold))
pf.setPen(QColor("#ffffff"))
pf.drawText(QRectF(70, card_y + 160, 940, 34), Qt.AlignCenter, "Pago Único Permanente a Tasa BCV · Cero Mensualidades")

pf.setPen(QPen(QColor("#1e3a8a"), 2))
pf.drawLine(130, card_y + 208, 950, card_y + 208)

def draw_offer_line(p, text, y_pos):
    p.setFont(QFont("Segoe UI", 22, QFont.Bold))
    p.setPen(QColor("#4ade80"))
    p.drawText(QRectF(120, y_pos, 35, 30), Qt.AlignLeft, "✔")
    p.setFont(QFont("Segoe UI", 21, QFont.DemiBold))
    p.setPen(QColor("#f8fafc"))
    p.drawText(QRectF(165, y_pos, 790, 30), Qt.AlignLeft | Qt.AlignVCenter, text)

draw_offer_line(pf, "Software Punto de Venta para PC (Windows)", card_y + 235)
draw_offer_line(pf, "App Móvil sincronizada para teléfono Android", card_y + 290)
draw_offer_line(pf, "Control de Inventario, Ventas, Caja y Fiados", card_y + 345)
draw_offer_line(pf, "Conversor Automático de Tasa BCV (USD / Bs)", card_y + 400)
draw_offer_line(pf, "Funciona 100% rápido aunque no tengas internet", card_y + 455)
draw_offer_line(pf, "Instalación en 1 Clic + Video Tutorial incluido", card_y + 510)
draw_offer_line(pf, "Soporte Técnico y Garantía Total de funcionamiento", card_y + 565)
draw_offer_line(pf, "Prueba DEMO Gratis disponible para probarlo hoy", card_y + 620)

plans_y = card_y + 680
pf.setBrush(QBrush(QColor("#081226")))
pf.setPen(QPen(QColor("#38bdf8"), 2))
pf.drawRoundedRect(QRectF(110, plans_y, 860, 110), 16, 16)

pf.setFont(QFont("Segoe UI", 20, QFont.Bold))
pf.setPen(QColor("#38bdf8"))
pf.drawText(QRectF(130, plans_y + 16, 820, 30), Qt.AlignCenter, "💡 Planes Opcionales Disponibles:")

pf.setFont(QFont("Segoe UI", 19, QFont.Medium))
pf.setPen(QColor("#cbd5e1"))
pf.drawText(QRectF(130, plans_y + 55, 820, 35), Qt.AlignCenter, "Plan Anual: $12 / año   •   Plan Mensual: $5 / mes   •   Vitalicio: $15 único")

cta_y = 1155
pf.setBrush(QBrush(QColor("#2563eb")))
pf.setPen(QPen(QColor("#93c5fd"), 3))
pf.drawRoundedRect(QRectF(70, cta_y, 940, 165), 22, 22)

pf.setFont(QFont("Segoe UI", 24, QFont.Bold))
pf.setPen(QColor("#ffffff"))
pf.drawText(QRectF(70, cta_y + 22, 940, 32), Qt.AlignCenter, "📩 ESCRÍBENOS PARA PEDIR TU DEMO GRATIS:")

pf.setFont(QFont("Segoe UI", 40, QFont.Black))
pf.setPen(QColor("#fbbf24"))
pf.drawText(QRectF(70, cta_y + 68, 940, 52), Qt.AlignCenter, "mobildeskpos@gmail.com")

pf.setFont(QFont("Segoe UI", 18, QFont.DemiBold))
pf.setPen(QColor("#e0e7ff"))
pf.drawText(QRectF(70, cta_y + 125, 940, 26), Qt.AlignCenter, "Te enviamos el instalador y la app móvil de inmediato")

pf.setFont(QFont("Segoe UI", 28, QFont.Bold))
pf.setPen(QColor("#4ade80"))
pf.drawText(QRectF(70, 1345, 940, 45), Qt.AlignCenter, "👇 O COMENTA 'DEMO' Y TE RESPONDEMOS")

draw_footer_cta(pf, "Oficial", 1, "MobilDesk POS · El Sistema para Negocios en Venezuela 🇻🇪")
pf.end()
img_f.save(str(out_dir / "Flyer_Marketing_Oficial_15USD.png"), "PNG")


# ==============================================================================
# 2. CARRUSEL: SLIDE 1 - PORTADA
# ==============================================================================
img1, p1 = create_base_canvas()
draw_top_badge(p1, "🏪 PARA DUEÑOS DE BODEGAS EN VENEZUELA 🇻🇪", "#38bdf8", 120)
draw_header_title(p1, "Deja de anotar las ventas y los fiados en un cuaderno 📖❌", 195)
draw_pc_screen(p1, img_sales_real, 60, 360, 960, 930, "🛒 Facturación y Punto de Venta en Vivo · MobilDesk")
draw_bottom_highlight(
    p1,
    "🚀 Conoce MobilDesk POS (PC + App Móvil)",
    "Punto de Venta rápido, Tasa BCV automática y Control de Fiados por solo $15 único.",
    1330
)
draw_footer_cta(p1, 1, 6, "👉 Desliza para ver el Punto de Venta ➡️")
p1.end()
img1.save(str(out_dir / "Carrusel_01_Portada.png"), "PNG")


# ==============================================================================
# 3. CARRUSEL: SLIDE 2 - VENTAS Y TASA BCV
# ==============================================================================
img2, p2 = create_base_canvas()
draw_top_badge(p2, "1. FACTURACIÓN & TASA BCV AUTOMÁTICA", "#38bdf8", 120)
draw_header_title(p2, "Cobra en $ y calcula el vuelto exacto en Bolívares 💵", 195)
draw_pc_screen(p2, img_sales_real, 60, 360, 960, 930, "🛒 Facturación y Punto de Venta en Vivo · MobilDesk")
draw_bottom_highlight(
    p2,
    "⚡ Pagos Mixtos y Tasa del Día",
    "Actualiza la Tasa BCV con 1 clic. Acepta Efectivo, Punto y Pago Móvil sin equivocarte.",
    1330
)
draw_footer_cta(p2, 2, 6, "👉 Desliza para ver el Inventario ➡️")
p2.end()
img2.save(str(out_dir / "Carrusel_02_PuntoVenta_BCV.png"), "PNG")


# ==============================================================================
# 4. CARRUSEL: SLIDE 3 - INVENTARIO REAL LIMPIO
# ==============================================================================
img3, p3 = create_base_canvas()
draw_top_badge(p2, "2. INVENTARIO Y GESTIÓN DE PRODUCTOS", "#38bdf8", 120)
draw_header_title(p3, "Controla existencias, precios en $ y alertas de stock 📦", 195)
draw_pc_screen(p3, img_inv_real, 60, 360, 960, 930, "📦 Catálogo de Productos e Inventario · MobilDesk")
draw_bottom_highlight(
    p3,
    "🔍 Búsqueda Instantánea y Código de Barras",
    "Da entradas de mercancía, ajusta stock y define precios con cálculo automático en Bs.",
    1330
)
draw_footer_cta(p3, 3, 6, "👉 Desliza para ver los Fiados ➡️")
p3.end()
img3.save(str(out_dir / "Carrusel_03_Inventario_Productos.png"), "PNG")


# ==============================================================================
# 5. CARRUSEL: SLIDE 4 - CONTROL DE FIADOS REAL
# ==============================================================================
img4, p4 = create_base_canvas()
draw_top_badge(p4, "3. CONTROL DE FIADOS Y DEUDAS", "#fbbf24", 120)
draw_header_title(p4, "Olvídate del cuaderno de fiados y recupera tu dinero 📋✨", 195)
draw_pc_screen(p4, img_fiados_real, 60, 360, 960, 930, "👥 Cuentas por Cobrar (Fiados) · MobilDesk")
draw_bottom_highlight(
    p4,
    "🔒 Control Total de Cuentas por Cobrar",
    "Lista de clientes con saldo exacto en $ y Bs. Registra abonos con 1 clic y consulta el historial.",
    1330
)
draw_footer_cta(p4, 4, 6, "👉 Desliza para ver la App Móvil ➡️")
p4.end()
img4.save(str(out_dir / "Carrusel_04_Control_Fiados.png"), "PNG")


# ==============================================================================
# 6. CARRUSEL: SLIDE 5 - APP MÓVIL EN SMARTPHONE NATIVO
# ==============================================================================
img5, p5 = create_base_canvas()
draw_top_badge(p5, "4. APP MÓVIL EN TU TELÉFONO", "#38bdf8", 120)
draw_header_title(p5, "Tu bodega en tu bolsillo sincronizada en tiempo real 📱", 195)
draw_smartphone(p5, img_mobile_fresh, 230, 360, 620, 930)
draw_bottom_highlight(
    p5,
    "🔄 Sincronización en Tiempo Real",
    "Todo lo que vendes en la computadora se refleja de inmediato en tu celular Android.",
    1330
)
draw_footer_cta(p5, 5, 6, "👉 Desliza para ver la Oferta $15 ➡️")
p5.end()
img5.save(str(out_dir / "Carrusel_05_App_Movil.png"), "PNG")


# ==============================================================================
# 7. CARRUSEL: SLIDE 6 - OFERTA Y CIERRE DE VENTA
# ==============================================================================
img6, p6 = create_base_canvas()
draw_top_badge(p6, "💎 OFERTA ESPECIAL · PAGO ÚNICO", "#fbbf24", 120)
draw_header_title(p6, "Digitaliza tu negocio hoy por solo $15 USD 🚀", 195)

card_y6 = 345
card_h6 = 710
p6.setBrush(QBrush(QColor("#0d1b38")))
p6.setPen(QPen(QColor("#fbbf24"), 4))
p6.drawRoundedRect(QRectF(70, card_y6, 940, card_h6), 24, 24)

p6.setFont(QFont("Segoe UI", 24, QFont.Bold))
p6.setPen(QColor("#93c5fd"))
p6.drawText(QRectF(70, card_y6 + 25, 940, 36), Qt.AlignCenter, "LICENCIA PERMANENTE VITALICIA")

p6.setFont(QFont("Segoe UI", 85, QFont.Black))
p6.setPen(QColor("#fbbf24"))
p6.drawText(QRectF(70, card_y6 + 65, 940, 95), Qt.AlignCenter, "$15 USD")

p6.setFont(QFont("Segoe UI", 22, QFont.Bold))
p6.setPen(QColor("#ffffff"))
p6.drawText(QRectF(70, card_y6 + 165, 940, 34), Qt.AlignCenter, "Pagas 1 sola vez a Tasa BCV · Cero Mensualidades")

p6.setPen(QPen(QColor("#1e3a8a"), 2))
p6.drawLine(140, card_y6 + 215, 940, card_y + 215)

def draw_chk6(text, y_pos):
    p6.setFont(QFont("Segoe UI", 22, QFont.Bold))
    p6.setPen(QColor("#4ade80"))
    p6.drawText(QRectF(130, y_pos, 35, 30), Qt.AlignLeft, "✔")
    p6.setFont(QFont("Segoe UI", 21, QFont.DemiBold))
    p6.setPen(QColor("#f8fafc"))
    p6.drawText(QRectF(175, y_pos, 760, 30), Qt.AlignLeft | Qt.AlignVCenter, text)

draw_chk6("Punto de Venta para Computadora (Windows)", card_y6 + 245)
draw_chk6("App Móvil para Android (.apk sincronizada)", card_y6 + 305)
draw_chk6("Control de Inventario, Ventas, Caja y Fiados", card_y6 + 365)
draw_chk6("Conversor Automático de Tasa BCV (USD / Bs)", card_y6 + 425)
draw_chk6("Instalación rápida en 1 minuto + Soporte", card_y6 + 485)
draw_chk6("Prueba DEMO Gratis para probarlo hoy", card_y6 + 545)
draw_chk6("Sin mensualidades ni cobros ocultos", card_y6 + 605)

cta_y6 = 1085
p6.setBrush(QBrush(QColor("#2563eb")))
p6.setPen(QPen(QColor("#93c5fd"), 3))
p6.drawRoundedRect(QRectF(70, cta_y6, 940, 160), 22, 22)

p6.setFont(QFont("Segoe UI", 24, QFont.Bold))
p6.setPen(QColor("#ffffff"))
p6.drawText(QRectF(70, cta_y6 + 22, 940, 32), Qt.AlignCenter, "📩 ESCRÍBENOS PARA PEDIR TU DEMO:")

p6.setFont(QFont("Segoe UI", 40, QFont.Black))
p6.setPen(QColor("#fbbf24"))
p6.drawText(QRectF(70, cta_y6 + 65, 940, 52), Qt.AlignCenter, "mobildeskpos@gmail.com")

p6.setFont(QFont("Segoe UI", 18, QFont.DemiBold))
p6.setPen(QColor("#e0e7ff"))
p6.drawText(QRectF(70, cta_y6 + 120, 940, 26), Qt.AlignCenter, "Te respondemos de inmediato con el instalador")

p6.setFont(QFont("Segoe UI", 28, QFont.Bold))
p6.setPen(QColor("#4ade80"))
p6.drawText(QRectF(70, 1275, 940, 45), Qt.AlignCenter, "👇 O COMENTA 'DEMO' Y TE RESPONDEMOS")

draw_footer_cta(p6, 6, 6, "¡Gracias por revisar MobilDesk POS! ✨")
p6.end()
img6.save(str(out_dir / "Carrusel_06_Oferta_15USD.png"), "PNG")


# ==============================================================================
# 8. BANNER CUADRADO PARA WHATSAPP / FEED (1080x1080)
# ==============================================================================
BW, BH = 1080, 1080
img_b, pb = create_base_canvas(BW, BH)

draw_top_badge(pb, "🏪 SISTEMA DE VENTAS · MOBILDESK POS 🇻🇪", "#fbbf24", 50, BW)
draw_header_title(pb, "El Punto de Venta Completo para tu Bodega o Negocio", 125, 100, 38, BW)

card_b_y = 235
card_b_h = 580
pb.setBrush(QBrush(QColor("#0d1b38")))
pb.setPen(QPen(QColor("#fbbf24"), 3.5))
pb.drawRoundedRect(QRectF(50, card_b_y, 980, card_b_h), 22, 22)

pb.setFont(QFont("Segoe UI", 20, QFont.Bold))
pb.setPen(QColor("#93c5fd"))
pb.drawText(QRectF(80, card_b_y + 30, 360, 30), Qt.AlignCenter, "LICENCIA PERMANENTE")

pb.setFont(QFont("Segoe UI", 70, QFont.Black))
pb.setPen(QColor("#fbbf24"))
pb.drawText(QRectF(80, card_b_y + 65, 360, 80), Qt.AlignCenter, "$15")

pb.setFont(QFont("Segoe UI", 17, QFont.Bold))
pb.setPen(QColor("#ffffff"))
pb.drawText(QRectF(80, card_b_y + 155, 360, 24), Qt.AlignCenter, "PAGO ÚNICO · TASA BCV")

pb.setFont(QFont("Segoe UI", 15, QFont.Medium))
pb.setPen(QColor("#94a3b8"))
pb.drawText(QRectF(80, card_b_y + 185, 360, 22), Qt.AlignCenter, "Sin Rentas Mensuales")

pb.setPen(QPen(QColor("#1e3a8a"), 2))
pb.drawLine(470, card_b_y + 30, 470, card_b_y + 380)

def draw_b_chk(text, y_pos):
    pb.setFont(QFont("Segoe UI", 19, QFont.Bold))
    pb.setPen(QColor("#4ade80"))
    pb.drawText(QRectF(500, y_pos, 30, 28), Qt.AlignLeft, "✔")
    pb.setFont(QFont("Segoe UI", 18, QFont.DemiBold))
    pb.setPen(QColor("#f8fafc"))
    pb.drawText(QRectF(540, y_pos, 460, 28), Qt.AlignLeft | Qt.AlignVCenter, text)

draw_b_chk("Punto de Venta para PC (Windows)", card_b_y + 35)
draw_b_chk("App Móvil Android sincronizada", card_b_y + 85)
draw_b_chk("Tasa BCV Automática ($ y Bs)", card_b_y + 135)
draw_b_chk("Control de Fiados y Clientes", card_b_y + 185)
draw_b_chk("Inventario y Código de Barras", card_b_y + 235)
draw_b_chk("Cierre de Caja Diario y Reportes", card_b_y + 285)
draw_b_chk("Instalación rápida + Soporte", card_b_y + 335)

cta_by = card_b_y + 420
pb.setBrush(QBrush(QColor("#2563eb")))
pb.setPen(QPen(QColor("#93c5fd"), 2.5))
pb.drawRoundedRect(QRectF(80, cta_by, 920, 125), 18, 18)

pb.setFont(QFont("Segoe UI", 20, QFont.Bold))
pb.setPen(QColor("#ffffff"))
pb.drawText(QRectF(80, cta_by + 16, 920, 28), Qt.AlignCenter, "📩 Pide tu DEMO Gratis al Correo Oficial:")

pb.setFont(QFont("Segoe UI", 34, QFont.Black))
pb.setPen(QColor("#fbbf24"))
pb.drawText(QRectF(80, cta_by + 52, 920, 44), Qt.AlignCenter, "mobildeskpos@gmail.com")

pb.setFont(QFont("Segoe UI", 16, QFont.Medium))
pb.setPen(QColor("#e0e7ff"))
pb.drawText(QRectF(80, cta_by + 96, 920, 22), Qt.AlignCenter, "Instalación inmediata • Soporte y Garantía Total")

pb.setFont(QFont("Segoe UI", 20, QFont.Bold))
pb.setPen(QColor("#38bdf8"))
pb.drawText(QRectF(0, 850, BW, 35), Qt.AlignCenter, "👉 Comenta 'DEMO' o Escríbenos para enviarte el instalador")

pb.setFont(QFont("Segoe UI", 15, QFont.DemiBold))
pb.setPen(QColor("#64748b"))
pb.drawText(QRectF(0, 895, BW, 25), Qt.AlignCenter, "MobilDesk POS · Hecho para Comercios y Bodegas en Venezuela 🇻🇪")

pb.end()
img_b.save(str(out_dir / "Banner_Cuadrado_1080x1080.png"), "PNG")

print("PERFECT_MARKETING_IMAGES_GENERATED_100_OK")
