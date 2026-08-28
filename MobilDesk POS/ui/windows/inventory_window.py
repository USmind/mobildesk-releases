from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QMessageBox,
    QComboBox,
    QLineEdit,
    QDialog,
    QFormLayout,
    QDialogButtonBox,
    QHeaderView,
    QInputDialog,
    QFrame,
    QGridLayout,
    QScrollArea,
)
from database.connection import get_connection
from modules.productos.product_service import (
    get_products,
    get_next_product_code,
    create_product,
    update_product,
    delete_product,
    ProductoYaExiste,
    get_categories,
    create_category,
)
from modules.inventario.inventory_service import (
    add_inventory_entry,
    add_inventory_adjustment,
    get_inventory_movements,
    update_inventory_movement_motivo,
    delete_inventory_movement,
)
from modules.configuracion.exchange_rate_service import (
    get_current_rate_value,
    get_profit_percentage,
    sale_price_usd,
)

UNIDADES = ["Unidad", "Kg", "g", "L", "ml", "Paquete", "Caja", "Bulto", "Docena", "Metro", "Saco"]


def category_box(selected=None):
    box = QComboBox()
    box.setEditable(True)
    box.addItem("", None)
    for item in get_categories():
        box.addItem(item["nombre"], item["id"])
    if selected:
        box.setCurrentText(selected)
    return box


# ============================================================
# DIÁLOGO DE CREACIÓN / EDICIÓN DE PRODUCTO CON CALCULADORA
# ============================================================

class ProductDialog(QDialog):
    def __init__(self, producto=None, parent=None, codigo_precargado=None):
        super().__init__(parent)
        self.producto = producto
        self.es_edicion = producto is not None
        self.codigo_precargado = codigo_precargado
        self.setWindowTitle("Modificar Producto" if self.es_edicion else "Nuevo Producto")
        self.resize(650, 520)
        self.setMinimumSize(560, 460)
        self.tasa_actual = 0.0
        self.margen_configurado = 0.0
        self.cargar_tasa_y_margen()
        self.crear_interfaz()
        self.cargar_datos_si_edicion()

    def cargar_tasa_y_margen(self):
        try:
            self.tasa_actual = float(get_current_rate_value() or 0.0)
            self.margen_configurado = float(get_profit_percentage() or 0.0)
        except Exception:
            self.tasa_actual = 0.0
            self.margen_configurado = 0.0

    def crear_interfaz(self):
        self.setStyleSheet("""
            QDialog { background-color: #ffffff; font-family: 'Segoe UI', sans-serif; }
            QLabel { background: transparent; border: none; color: #334155; font-size: 13px; font-weight: 600; }
            QLineEdit { background-color: #ffffff; border: 1.5px solid #cbd5e1; border-radius: 7px; padding: 8px 10px; font-size: 13.5px; min-height: 22px; color: #0f172a; }
            QLineEdit:focus { border: 2px solid #2563eb; }
            QComboBox {
                background-color: #ffffff;
                border: 1.5px solid #cbd5e1;
                border-radius: 7px;
                padding: 8px 10px;
                font-size: 13.5px;
                min-height: 22px;
                color: #0f172a;
            }
            QComboBox:focus { border: 2px solid #2563eb; }
            QComboBox QLineEdit {
                background-color: #ffffff;
                color: #0f172a;
                border: none;
                padding: 0px;
            }
            QComboBox QAbstractItemView {
                background-color: #ffffff;
                color: #0f172a;
                selection-background-color: #2563eb;
                selection-color: #ffffff;
                border: 1.5px solid #cbd5e1;
                border-radius: 6px;
                padding: 4px;
                outline: none;
            }
            QComboBox QAbstractItemView::item {
                min-height: 28px;
                padding: 6px 10px;
                color: #0f172a;
                background-color: #ffffff;
            }
            QComboBox QAbstractItemView::item:selected, QComboBox QAbstractItemView::item:hover {
                background-color: #2563eb;
                color: #ffffff;
            }
            QFrame#calc_card { background-color: #f8fafc; border: 1.5px solid #cbd5e1; border-radius: 10px; }
            QScrollArea { border: none; background: transparent; }
        """)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(16, 16, 16, 16)
        main_layout.setSpacing(10)

        # Encabezado
        title = QLabel("MODIFICAR PRODUCTO" if self.es_edicion else "NUEVO PRODUCTO")
        title.setStyleSheet("font-size: 19px; font-weight: 800; color: #1e293b; border: none;")
        main_layout.addWidget(title)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll_content = QWidget()
        scroll_content.setStyleSheet("background: transparent;")
        layout = QVBoxLayout(scroll_content)
        layout.setSpacing(14)
        layout.setContentsMargins(4, 4, 4, 4)

        # Formulario Superior
        form_grid = QGridLayout()
        form_grid.setHorizontalSpacing(14)
        form_grid.setVerticalSpacing(10)

        # Fila 0 y 1: Código (escaneable) y Nombre
        lbl_cod = QLabel("Código / Código de Barras (*):")
        form_grid.addWidget(lbl_cod, 0, 0)
        self.txt_codigo = QLineEdit()
        self.txt_codigo.setPlaceholderText("Escanea o escribe el código de barras")
        if self.es_edicion:
            self.txt_codigo.setReadOnly(True)
            self.txt_codigo.setStyleSheet("background-color: #f1f5f9; font-weight: 700;")
        elif self.codigo_precargado:
            self.txt_codigo.setText(self.codigo_precargado)
        form_grid.addWidget(self.txt_codigo, 1, 0)

        lbl_nom = QLabel("Nombre del Producto (*):")
        form_grid.addWidget(lbl_nom, 0, 1)
        self.txt_nombre = QLineEdit()
        self.txt_nombre.setPlaceholderText("Ej: Arroz Blanco 1Kg")
        form_grid.addWidget(self.txt_nombre, 1, 1)

        # Fila 2 y 3: Unidad de Medida
        lbl_uni = QLabel("Unidad de Medida:")
        form_grid.addWidget(lbl_uni, 2, 0)
        self.combo_unidad = QComboBox()
        self.combo_unidad.addItems(UNIDADES)
        form_grid.addWidget(self.combo_unidad, 3, 0)

        layout.addLayout(form_grid)

        # ====================================================
        # CALCULADORA DE PRECIOS Y GANANCIA
        # ====================================================
        calc_box = QFrame()
        calc_box.setObjectName("calc_card")
        calc_layout = QVBoxLayout(calc_box)
        calc_layout.setSpacing(10)
        calc_layout.setContentsMargins(16, 14, 16, 14)

        lbl_calc_title = QLabel("💰 Calculadora de Precios y Ganancia")
        lbl_calc_title.setStyleSheet("font-size: 14px; font-weight: 700; color: #1e3a8a; border: none;")
        calc_layout.addWidget(lbl_calc_title)

        prices_grid = QGridLayout()
        prices_grid.setHorizontalSpacing(14)
        prices_grid.setVerticalSpacing(6)

        # Etiquetas (Fila 0)
        lbl_p1 = QLabel("Costo Base ($ USD):")
        lbl_p2 = QLabel("Ganancia (%):")
        lbl_p3 = QLabel("Precio Venta ($ USD):")
        prices_grid.addWidget(lbl_p1, 0, 0)
        prices_grid.addWidget(lbl_p2, 0, 1)
        prices_grid.addWidget(lbl_p3, 0, 2)

        # Inputs (Fila 1)
        self.txt_costo_usd = QLineEdit("0.00")
        self.txt_costo_usd.setStyleSheet("font-size: 14px; font-weight: 600;")
        self.txt_costo_usd.textChanged.connect(self._recalcular_desde_costo)
        prices_grid.addWidget(self.txt_costo_usd, 1, 0)

        self.txt_margen_pct = QLineEdit(str(self.margen_configurado if self.margen_configurado > 0 else 30.0))
        self.txt_margen_pct.setStyleSheet("font-size: 14px; font-weight: 600;")
        self.txt_margen_pct.textChanged.connect(self._recalcular_desde_costo)
        prices_grid.addWidget(self.txt_margen_pct, 1, 1)

        self.txt_precio_usd = QLineEdit("0.00")
        self.txt_precio_usd.setStyleSheet("font-size: 14px; font-weight: 700; color: #15803d;")
        self.txt_precio_usd.textChanged.connect(self._recalcular_desde_precio_usd)
        prices_grid.addWidget(self.txt_precio_usd, 1, 2)

        # Botones Rápidos de Margen (Fila 2)
        quick_btns = QHBoxLayout()
        quick_btns.setSpacing(4)
        for pct in [15, 20, 30, 40, 50]:
            btn_pct = QPushButton(f"{pct}%")
            btn_pct.setStyleSheet("background: #e2e8f0; color: #1e293b; font-size: 11px; padding: 4px 8px; border-radius: 4px; font-weight: 700; border: none;")
            btn_pct.clicked.connect(lambda ch=False, val=pct: self._aplicar_margen_rapido(val))
            quick_btns.addWidget(btn_pct)
        prices_grid.addLayout(quick_btns, 2, 1)

        calc_layout.addLayout(prices_grid)

        # Resumen en Bolívares
        self.lbl_preview_bs = QLabel("")
        self.lbl_preview_bs.setStyleSheet("font-size: 13px; font-weight: 700; color: #1e40af; padding-top: 4px; border: none;")
        self.lbl_preview_bs.setWordWrap(True)
        calc_layout.addWidget(self.lbl_preview_bs)

        layout.addWidget(calc_box)
        scroll.setWidget(scroll_content)
        main_layout.addWidget(scroll, 1)

        # Botones Inferiores
        actions = QHBoxLayout()
        btn_cancel = QPushButton("Cancelar")
        btn_cancel.setStyleSheet("background: #f1f5f9; color: #475569; border: 1px solid #cbd5e1; padding: 9px 18px; border-radius: 7px; font-weight: 600;")
        btn_cancel.clicked.connect(self.reject)
        actions.addWidget(btn_cancel)

        actions.addStretch()

        btn_save = QPushButton("💾 Guardar Producto")
        btn_save.setStyleSheet("background: #2563eb; color: white; padding: 9px 24px; border-radius: 7px; font-weight: 700; font-size: 14px; border: none;")
        btn_save.clicked.connect(self.validar_y_guardar)
        actions.addWidget(btn_save)

        main_layout.addLayout(actions)
        self._recalcular_desde_costo()

    def _aplicar_margen_rapido(self, pct):
        self.txt_margen_pct.setText(str(pct))

    def _recalcular_desde_costo(self):
        try:
            costo = float(self.txt_costo_usd.text().replace(",", ".").strip() or 0)
            margen = float(self.txt_margen_pct.text().replace(",", ".").strip() or 0)
            precio_usd = costo * (1.0 + (margen / 100.0))

            self.txt_precio_usd.blockSignals(True)
            self.txt_precio_usd.setText(f"{precio_usd:.2f}")
            self.txt_precio_usd.blockSignals(False)

            precio_bs = precio_usd * self.tasa_actual
            ganancia_usd = precio_usd - costo
            tasa_str = f"{self.tasa_actual:,.2f}" if self.tasa_actual > 0 else "Sin tasa"
            self.lbl_preview_bs.setText(
                f"💵 Precio al Público: ${precio_usd:,.2f} USD  âž”  Bs {precio_bs:,.2f} (Tasa: {tasa_str})  |  Ganancia: +${ganancia_usd:,.2f}"
            )
        except Exception:
            pass

    def _recalcular_desde_precio_usd(self):
        try:
            precio_usd = float(self.txt_precio_usd.text().replace(",", ".").strip() or 0)
            costo = float(self.txt_costo_usd.text().replace(",", ".").strip() or 0)

            if costo > 0:
                margen = ((precio_usd - costo) / costo) * 100.0
                self.txt_margen_pct.blockSignals(True)
                self.txt_margen_pct.setText(f"{margen:.1f}")
                self.txt_margen_pct.blockSignals(False)

            precio_bs = precio_usd * self.tasa_actual
            ganancia_usd = precio_usd - costo
            tasa_str = f"{self.tasa_actual:,.2f}" if self.tasa_actual > 0 else "Sin tasa"
            self.lbl_preview_bs.setText(
                f"💵 Precio al Público: ${precio_usd:,.2f} USD  âž”  Bs {precio_bs:,.2f} (Tasa: {tasa_str})  |  Ganancia: +${ganancia_usd:,.2f}"
            )
        except Exception:
            pass

    def cargar_datos_si_edicion(self):
        if not self.producto:
            return
        p = self.producto
        self.txt_codigo.setText(p["codigo"])
        self.txt_nombre.setText(p["nombre"])
        self.combo_unidad.setCurrentText(p["unidad"] if ("unidad" in p.keys() and p["unidad"]) else "Unidad")

        precio_actual = float(p["precio_usd"] if p["precio_usd"] is not None else 0.0)
        self.txt_costo_usd.setText(f"{precio_actual:.2f}")
        self.txt_precio_usd.setText(f"{precio_actual:.2f}")
        self._recalcular_desde_costo()

    def validar_y_guardar(self):
        codigo = self.txt_codigo.text().strip()
        nombre = self.txt_nombre.text().strip()
        if not codigo:
            QMessageBox.warning(self, "Aviso", "Debe ingresar o escanear el código del producto.")
            self.txt_codigo.setFocus()
            return
        if not nombre:
            QMessageBox.warning(self, "Aviso", "Debe ingresar el nombre del producto.")
            return

        try:
            precio_usd = float(self.txt_precio_usd.text().replace(",", ".").strip() or 0)
            if precio_usd <= 0:
                QMessageBox.warning(self, "Aviso", "El precio de venta en USD debe ser mayor a cero.")
                return
        except ValueError:
            QMessageBox.warning(self, "Aviso", "Los valores numéricos no son válidos.")
            return

        self.datos_resultado = {
            "codigo": codigo,
            "nombre": nombre,
            "unidad": self.combo_unidad.currentText(),
            "precio_usd": precio_usd,
            "stock_minimo": 0,
            "stock_inicial": 0,
            "categoria_id": None,
            "codigo_barras": codigo,
        }
        self.accept()


# ============================================================
# DIÁLOGOS DE ENTRADA Y AJUSTE DE INVENTARIO
# ============================================================

class InventoryMovementDialog(QDialog):
    def __init__(self, productos, usuario_id, tipo_inicial="entrada", parent=None):
        super().__init__(parent)
        self.usuario_id = usuario_id
        self.setWindowTitle("Entrada de Mercancía" if tipo_inicial == "entrada" else "Ajuste de Inventario")
        self.resize(520, 320)
        self.crear_interfaz(productos, tipo_inicial)

    def crear_interfaz(self, productos, tipo_inicial):
        self.setStyleSheet("""
            QDialog { background-color: #ffffff; font-family: 'Segoe UI', sans-serif; }
            QLabel { background: transparent; border: none; color: #334155; font-size: 13px; font-weight: 600; }
            QLineEdit { background-color: #ffffff; border: 1.5px solid #cbd5e1; border-radius: 7px; padding: 8px 10px; font-size: 13.5px; min-height: 22px; color: #0f172a; }
            QLineEdit:focus { border: 2px solid #2563eb; }
            QComboBox {
                background-color: #ffffff;
                border: 1.5px solid #cbd5e1;
                border-radius: 7px;
                padding: 8px 10px;
                font-size: 13.5px;
                min-height: 22px;
                color: #0f172a;
            }
            QComboBox:focus { border: 2px solid #2563eb; }
            QComboBox QLineEdit {
                background-color: #ffffff;
                color: #0f172a;
                border: none;
                padding: 0px;
            }
            QComboBox QAbstractItemView {
                background-color: #ffffff;
                color: #0f172a;
                selection-background-color: #2563eb;
                selection-color: #ffffff;
                border: 1.5px solid #cbd5e1;
                border-radius: 6px;
                padding: 4px;
                outline: none;
            }
            QComboBox QAbstractItemView::item {
                min-height: 28px;
                padding: 6px 10px;
                color: #0f172a;
                background-color: #ffffff;
            }
            QComboBox QAbstractItemView::item:selected, QComboBox QAbstractItemView::item:hover {
                background-color: #2563eb;
                color: #ffffff;
            }
        """)
        layout = QFormLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(20, 18, 20, 18)

        self.producto = QComboBox()
        for p in productos:
            self.producto.addItem(f"{p['codigo']} - {p['nombre']}", p["id"])

        self.tipo = QComboBox()
        self.tipo.addItem("Entrada de mercancía", "entrada")
        self.tipo.addItem("Ajuste de inventario", "ajuste")
        self.tipo.setCurrentIndex(1 if tipo_inicial == "ajuste" else 0)

        self.cantidad = QLineEdit()
        self.cantidad.setPlaceholderText("Ej: 24")

        self.motivo = QComboBox()
        self.motivo.setEditable(True)
        self.motivo.addItems([
            "Compra de mercancía", "Reposición de stock", "Producto dañado",
            "Producto vencido", "Pérdida / Merma", "Ajuste por conteo", "Devolución", "Otro"
        ])

        layout.addRow("Producto:", self.producto)
        layout.addRow("Tipo de Operación:", self.tipo)
        layout.addRow("Cantidad:", self.cantidad)
        layout.addRow("Motivo / Observación:", self.motivo)

        info = QLabel("Nota: En 'Ajuste' usa cantidad positiva para sumar stock o negativa para restar.")
        info.setStyleSheet("color: #64748b; font-size: 12px; border: none;")
        layout.addRow(info)

        botones = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        botones.accepted.connect(self.validar_y_aceptar)
        botones.rejected.connect(self.reject)
        layout.addRow(botones)

    def validar_y_aceptar(self):
        try:
            self.obtener_datos()
            self.accept()
        except ValueError as error:
            QMessageBox.warning(self, "Dato incorrecto", str(error))

    def obtener_datos(self):
        if self.producto.currentData() is None:
            raise ValueError("Debe seleccionar un producto.")

        txt = self.cantidad.text().strip()
        if not txt:
            raise ValueError("Debe ingresar una cantidad.")

        try:
            cantidad = float(txt.replace(",", "."))
        except ValueError:
            raise ValueError("La cantidad debe ser un número válido.")

        if cantidad == 0:
            raise ValueError("La cantidad no puede ser cero.")

        tipo = self.tipo.currentData()
        if tipo == "entrada" and cantidad < 0:
            raise ValueError("Una entrada de mercancía debe tener una cantidad positiva.")

        return {
            "producto_id": self.producto.currentData(),
            "tipo": tipo,
            "cantidad": cantidad,
            "motivo": self.motivo.currentText().strip() or "Sin motivo"
        }


class InventoryHistoryDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Historial de Movimientos de Inventario")
        self.setWindowFlags(Qt.Window | Qt.WindowTitleHint | Qt.WindowSystemMenuHint | Qt.WindowMinMaxButtonsHint | Qt.WindowCloseButtonHint)
        self.resize(1000, 560)
        self.setMinimumSize(780, 460)
        self.crear_interfaz()
        self.cargar_historial()

    def crear_interfaz(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(18, 16, 18, 16)

        titulo = QLabel("HISTORIAL DE MOVIMIENTOS")
        titulo.setStyleSheet("font-size: 18px; font-weight: 800; color: #1e293b; border: none;")
        layout.addWidget(titulo)

        self.tabla = QTableWidget()
        self.tabla.verticalHeader().setVisible(False)
        self.tabla.setColumnCount(8)
        self.tabla.setHorizontalHeaderLabels([
            "ID", "Código", "Producto", "Tipo", "Cantidad", "Motivo", "Usuario", "Fecha"
        ])
        self.tabla.setEditTriggers(QTableWidget.NoEditTriggers)
        self.tabla.setSelectionBehavior(QTableWidget.SelectRows)
        self.tabla.setSelectionMode(QTableWidget.SingleSelection)
        self.tabla.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.tabla)

        acciones = QHBoxLayout()
        boton_modificar = QPushButton("✏️ Modificar Motivo")
        boton_eliminar = QPushButton("🗑️ Eliminar Movimiento")
        boton_modificar.setStyleSheet("background: #f1f5f9; color: #1e293b; border: 1px solid #cbd5e1; padding: 7px 14px; border-radius: 6px; font-weight: 600;")
        boton_eliminar.setStyleSheet("background: #fef2f2; color: #b91c1c; border: 1px solid #fca5a5; padding: 7px 14px; border-radius: 6px; font-weight: 600;")
        boton_modificar.clicked.connect(self.modificar_movimiento)
        boton_eliminar.clicked.connect(self.eliminar_movimiento)
        acciones.addWidget(boton_modificar)
        acciones.addWidget(boton_eliminar)
        acciones.addStretch()

        boton_cerrar = QPushButton("Cerrar")
        boton_cerrar.setStyleSheet("background: #2563eb; color: white; padding: 8px 18px; border-radius: 7px; font-weight: 700;")
        boton_cerrar.clicked.connect(self.accept)
        acciones.addWidget(boton_cerrar)
        layout.addLayout(acciones)

    def cargar_historial(self):
        movimientos = get_inventory_movements()
        self.tabla.setRowCount(len(movimientos))
        for fila, m in enumerate(movimientos):
            valores = [m[0], m[1], m[2], m[3], m[4], m[5] or "", m[6], m[7]]
            for col, val in enumerate(valores):
                item = QTableWidgetItem(str(val))
                if col == 4:
                    item.setTextAlignment(Qt.AlignCenter)
                self.tabla.setItem(fila, col, item)

    def movimiento_seleccionado(self):
        fila = self.tabla.currentRow()
        if fila < 0:
            QMessageBox.warning(self, "Inventario", "Seleccione un movimiento de la lista.")
            return None
        return int(self.tabla.item(fila, 0).text()), self.tabla.item(fila, 5).text()

    def modificar_movimiento(self):
        sel = self.movimiento_seleccionado()
        if not sel:
            return
        motivo, ok = QInputDialog.getText(self, "Modificar Motivo", "Nuevo motivo:", text=sel[1])
        if ok:
            try:
                update_inventory_movement_motivo(sel[0], motivo)
                self.cargar_historial()
            except ValueError as error:
                QMessageBox.warning(self, "Inventario", str(error))

    def eliminar_movimiento(self):
        sel = self.movimiento_seleccionado()
        if not sel:
            return
        msg = QMessageBox(self)
        msg.setWindowTitle("Eliminar Movimiento")
        msg.setIcon(QMessageBox.Question)
        msg.setText("¿Deseas eliminar este movimiento de inventario?")
        btn_si = msg.addButton("🗑️ Sí, Eliminar", QMessageBox.YesRole)
        btn_si.setStyleSheet("background-color: #dc2626; color: white; font-weight: 700; padding: 8px 18px; border-radius: 7px; border: none;")
        btn_no = msg.addButton("Cancelar", QMessageBox.NoRole)
        btn_no.setStyleSheet("background-color: #f1f5f9; color: #1e293b; border: 1.5px solid #cbd5e1; font-weight: 700; padding: 8px 18px; border-radius: 7px;")
        msg.exec()
        if msg.clickedButton() == btn_si:
            try:
                delete_inventory_movement(sel[0])
                self.cargar_historial()
            except ValueError as error:
                QMessageBox.warning(self, "Inventario", str(error))


# ============================================================
# VENTANA PRINCIPAL UNIFICADA: INVENTARIO Y PRODUCTOS
# ============================================================

class UnifiedInventoryWindow(QWidget):
    products_changed = Signal()

    def __init__(self, usuario=None):
        super().__init__()
        self.usuario = usuario
        self.setWindowTitle("Inventario y Productos - MobilDesk")
        self.resize(1200, 750)
        self.setMinimumSize(850, 520)
        self.tasa_actual = 0.0
        self.productos = []
        self.crear_interfaz()
        self.cargar_todo()

    def crear_interfaz(self):
        self.setStyleSheet("""
            * { outline: none; }
            QWidget { font-family: 'Segoe UI', sans-serif; color: #0f172a; }
            QLabel { color: #0f172a; border: none; background: transparent; outline: none; }
            QLabel:focus { border: none; outline: none; }
            QPushButton {
                background-color: #2563eb;
                color: #ffffff;
                font-weight: 700;
                font-size: 13px;
                padding: 9px 15px;
                border-radius: 8px;
                min-height: 20px;
                border: none;
            }
            QPushButton:hover { background-color: #1d4ed8; }
            QPushButton:disabled { background-color: #e2e8f0; color: #94a3b8; }
            QMessageBox { background-color: #ffffff; }
            QMessageBox QLabel { color: #0f172a; font-size: 14px; font-weight: 600; border: none; background: transparent; }
            QMessageBox QPushButton {
                background-color: #2563eb;
                color: #ffffff;
                border: none;
                border-radius: 7px;
                padding: 8px 18px;
                font-size: 13.5px;
                font-weight: 700;
                min-width: 80px;
                min-height: 28px;
            }
            QMessageBox QPushButton:hover { background-color: #1d4ed8; }
            QDialogButtonBox QPushButton {
                background-color: #2563eb;
                color: #ffffff;
                border: none;
                border-radius: 7px;
                padding: 8px 18px;
                font-size: 13.5px;
                font-weight: 700;
                min-width: 80px;
                min-height: 26px;
            }
            QDialogButtonBox QPushButton:hover { background-color: #1d4ed8; }
            QLineEdit {
                background: white;
                border: 1.5px solid #cbd5e1;
                border-radius: 8px;
                padding: 8px 14px;
                font-size: 13.5px;
                color: #0f172a;
            }
            QLineEdit:focus { border: 2px solid #2563eb; }
            QTableWidget {
                background: white;
                border: 1px solid #cbd5e1;
                border-radius: 10px;
                gridline-color: #f1f5f9;
                font-size: 13.5px;
                color: #0f172a;
                outline: none;
            }
            QTableWidget::item { padding: 6px; border: none; outline: none; }
            QTableWidget::item:focus { border: none; outline: none; background: #dbeafe; color: #1e3a8a; }
            QTableWidget::item:selected { background: #dbeafe; color: #1e3a8a; border: none; outline: none; }
            QHeaderView::section {
                background: #f8fafc;
                color: #0f172a;
                font-weight: 700;
                font-size: 13px;
                border: none;
                border-bottom: 2px solid #e2e8f0;
                padding: 10px 8px;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setSpacing(14)
        layout.setContentsMargins(18, 16, 18, 16)

        # Fila 1: Encabezado con Tasa
        header_layout = QHBoxLayout()
        titulo = QLabel("📦 INVENTARIO Y GESTIÓN DE PRODUCTOS")
        titulo.setStyleSheet("font-size: 21px; font-weight: 800; color: #0f172a; border: none;")
        header_layout.addWidget(titulo)
        header_layout.addStretch()

        self.lbl_tasa_info = QLabel("Cargando tasa...")
        self.lbl_tasa_info.setStyleSheet("background: #eff6ff; color: #1d4ed8; font-weight: 800; font-size: 13.5px; padding: 6px 14px; border-radius: 8px; border: none;")
        header_layout.addWidget(self.lbl_tasa_info)
        layout.addLayout(header_layout)

        # Fila 2: Barra de Botones de Acción con Colores Vivos y Efectos Hover
        botones_layout = QHBoxLayout()
        botones_layout.setSpacing(10)

        btn_nuevo = QPushButton("➕ Nuevo Producto")
        btn_nuevo.setStyleSheet("""
            QPushButton { background: #2563eb; color: white; border: none; }
            QPushButton:hover { background: #1d4ed8; }
        """)
        btn_nuevo.clicked.connect(self.nuevo_producto)
        botones_layout.addWidget(btn_nuevo)

        btn_modificar = QPushButton("✏️ Modificar")
        btn_modificar.setStyleSheet("""
            QPushButton { background: #f8fafc; color: #1e293b; border: 1.5px solid #cbd5e1; }
            QPushButton:hover { background: #e2e8f0; }
        """)
        btn_modificar.clicked.connect(self.modificar_producto)
        botones_layout.addWidget(btn_modificar)

        btn_entrada = QPushButton("📥 Entrada Stock")
        btn_entrada.setStyleSheet("""
            QPushButton { background: #f0fdf4; color: #15803d; border: 1.5px solid #86efac; }
            QPushButton:hover { background: #dcfce7; }
        """)
        btn_entrada.clicked.connect(self.nueva_entrada)
        botones_layout.addWidget(btn_entrada)

        btn_ajuste = QPushButton("⚖️ Ajuste Stock")
        btn_ajuste.setStyleSheet("""
            QPushButton { background: #fffbeb; color: #b45309; border: 1.5px solid #fde68a; }
            QPushButton:hover { background: #fef3c7; }
        """)
        btn_ajuste.clicked.connect(self.nuevo_ajuste)
        botones_layout.addWidget(btn_ajuste)

        btn_historial = QPushButton("📋 Historial")
        btn_historial.setStyleSheet("""
            QPushButton { background: #f8fafc; color: #334155; border: 1.5px solid #cbd5e1; }
            QPushButton:hover { background: #e2e8f0; }
        """)
        btn_historial.clicked.connect(self.mostrar_historial)
        botones_layout.addWidget(btn_historial)

        btn_eliminar = QPushButton("🗑️ Eliminar")
        btn_eliminar.setStyleSheet("""
            QPushButton { background: #fef2f2; color: #dc2626; border: 1.5px solid #fca5a5; }
            QPushButton:hover { background: #fee2e2; }
        """)
        btn_eliminar.clicked.connect(self.eliminar_producto)
        botones_layout.addWidget(btn_eliminar)

        botones_layout.addStretch()
        layout.addLayout(botones_layout)

        # Fila 3: Barra de Búsqueda Completa (No cortada)
        self.txt_buscar = QLineEdit()
        self.txt_buscar.setPlaceholderText("🔍 Buscar producto por nombre, código o categoría...")
        self.txt_buscar.setMinimumHeight(38)
        self.txt_buscar.textChanged.connect(self.filtrar_tabla)
        layout.addWidget(self.txt_buscar)

        # Fila 4: Tabla Principal Unificada con Columnas Espaciosas
        self.tabla = QTableWidget()
        self.tabla.verticalHeader().setVisible(False)
        self.tabla.setColumnCount(5)
        self.tabla.setHorizontalHeaderLabels([
            "Código", "Producto", "Unidad", "Precio Venta (USD / Bs)", "Stock Disponible"
        ])
        self.tabla.setEditTriggers(QTableWidget.NoEditTriggers)
        self.tabla.setSelectionBehavior(QTableWidget.SelectRows)
        self.tabla.setSelectionMode(QTableWidget.SingleSelection)
        self.tabla.setFocusPolicy(Qt.NoFocus)
        self.tabla.verticalHeader().setVisible(False)

        # Ajuste de tamaño de columnas
        self.tabla.setColumnWidth(0, 130)
        self.tabla.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.tabla.setColumnWidth(2, 100)
        self.tabla.horizontalHeader().setSectionResizeMode(3, QHeaderView.Stretch)
        self.tabla.setColumnWidth(4, 150)

        self.tabla.doubleClicked.connect(self.modificar_producto)
        layout.addWidget(self.tabla)

    def cargar_tasa(self):
        con = get_connection()
        try:
            row = con.execute("SELECT valor FROM exchange_rates ORDER BY id DESC LIMIT 1").fetchone()
            self.tasa_actual = float(row["valor"]) if row else 0.0
            tasa_str = f"1 USD = {self.tasa_actual:,.2f} Bs" if self.tasa_actual > 0 else "Tasa No configurada"
            self.lbl_tasa_info.setText(f"💵 Tasa Actual: {tasa_str}")
        finally:
            con.close()

    def cargar_todo(self):
        self.cargar_tasa()
        self.productos = get_products()
        self.filtrar_tabla()

    def filtrar_tabla(self):
        busqueda = self.txt_buscar.text().strip().lower()
        filtrados = []
        for p in self.productos:
            nombre = str(p["nombre"] or "").lower()
            codigo = str(p["codigo"] or "").lower()
            cb = str(p["codigo_barras"] or "").lower() if "codigo_barras" in p.keys() else ""
            if not busqueda or busqueda in nombre or busqueda in codigo or busqueda in cb:
                filtrados.append(p)

        self.tabla.setRowCount(len(filtrados))
        for fila, p in enumerate(filtrados):
            precio_usd = float(p["precio_usd"] if p["precio_usd"] is not None else 0.0)
            precio_bs = precio_usd * self.tasa_actual
            stock_act = float(p["stock_actual"] if ("stock_actual" in p.keys() and p["stock_actual"] is not None) else 0.0)

            precio_str = f"${precio_usd:,.2f}  (Bs {precio_bs:,.2f})"
            uni_name = p["unidad"] if ("unidad" in p.keys() and p["unidad"]) else "Unidad"

            valores = [
                p["codigo"],
                p["nombre"],
                uni_name,
                precio_str,
                f"{stock_act:g}"
            ]

            for col, val in enumerate(valores):
                item = QTableWidgetItem(str(val))
                if col in (2, 4):
                    item.setTextAlignment(Qt.AlignCenter)
                if col == 4 and stock_act <= 0:
                    item.setToolTip("⚠️ï¸ Agotado / Sin Stock")
                    item.setForeground(Qt.red)
                self.tabla.setItem(fila, col, item)

    def producto_seleccionado(self):
        row = self.tabla.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Aviso", "Seleccione un producto de la tabla.")
            return None
        codigo = self.tabla.item(row, 0).text()
        for p in self.productos:
            if p["codigo"] == codigo:
                return p
        return None

    def nuevo_producto(self):
        dialogo = ProductDialog(None, self)
        if dialogo.exec() == QDialog.Accepted:
            d = dialogo.datos_resultado
            try:
                create_product(
                    codigo=d["codigo"],
                    nombre=d["nombre"],
                    unidad=d["unidad"],
                    precio_usd=d["precio_usd"],
                    stock_inicial=d["stock_inicial"],
                    categoria_id=d["categoria_id"],
                    stock_minimo=d["stock_minimo"],
                    codigo_barras=d["codigo_barras"]
                )
                QMessageBox.information(self, "Éxito", f"Producto '{d['nombre']}' registrado correctamente.")
                self.cargar_todo()
                self.products_changed.emit()
            except ProductoYaExiste as existe:
                respuesta = QMessageBox.question(
                    self,
                    "Producto ya existe",
                    f"El código {existe.codigo} ya está registrado.\n\n¿Deseas editar el producto existente?",
                    QMessageBox.Yes | QMessageBox.No
                )
                if respuesta == QMessageBox.Yes:
                    p = next((x for x in self.productos if x["codigo"] == existe.codigo), None)
                    if p:
                        self.modificar_producto_directo(p)
            except Exception as e:
                QMessageBox.critical(self, "Error", f"No se pudo guardar el producto: {e}")

    def modificar_producto(self):
        p = self.producto_seleccionado()
        if not p:
            QMessageBox.warning(self, "Aviso", "Seleccione un producto de la tabla.")
            return
        self.modificar_producto_directo(p)

    def modificar_producto_directo(self, p):
        dialogo = ProductDialog(p, self)
        if dialogo.exec() == QDialog.Accepted:
            d = dialogo.datos_resultado
            try:
                update_product(
                    producto_id=p["id"],
                    nombre=d["nombre"],
                    unidad=d["unidad"],
                    precio_usd=d["precio_usd"],
                    stock_minimo=d["stock_minimo"],
                    categoria_id=d["categoria_id"],
                    codigo_barras=d["codigo_barras"]
                )
                QMessageBox.information(self, "Éxito", "Producto modificado correctamente.")
                self.cargar_todo()
                self.products_changed.emit()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"No se pudo modificar el producto: {e}")

    def nueva_entrada(self):
        if not self.productos:
            QMessageBox.warning(self, "Aviso", "Primero debe crear al menos un producto.")
            return
        uid = self.usuario["id"] if self.usuario else 1
        dialogo = InventoryMovementDialog(self.productos, uid, "entrada", self)
        if dialogo.exec() == QDialog.Accepted:
            d = dialogo.obtener_datos()
            add_inventory_entry(d["producto_id"], d["cantidad"], uid, d["motivo"])
            QMessageBox.information(self, "Éxito", "Entrada de mercancía registrada correctamente.")
            self.cargar_todo()
            self.products_changed.emit()

    def nuevo_ajuste(self):
        if not self.productos:
            QMessageBox.warning(self, "Aviso", "Primero debe crear al menos un producto.")
            return
        uid = self.usuario["id"] if self.usuario else 1
        dialogo = InventoryMovementDialog(self.productos, uid, "ajuste", self)
        if dialogo.exec() == QDialog.Accepted:
            d = dialogo.obtener_datos()
            res = add_inventory_adjustment(d["producto_id"], d["cantidad"], uid, d["motivo"])
            QMessageBox.information(
                self,
                "Éxito",
                f"Ajuste registrado con éxito.\n\n"
                f"Stock anterior: {res['stock_anterior']:g}\n"
                f"Ajuste: {res['ajuste']:g}\n"
                f"Stock nuevo: {res['stock_nuevo']:g}"
            )
            self.cargar_todo()
            self.products_changed.emit()

    def mostrar_historial(self):
        dialogo = InventoryHistoryDialog(self)
        dialogo.exec()

    def eliminar_producto(self):
        p = self.producto_seleccionado()
        if not p:
            return
        msg = QMessageBox(self)
        msg.setWindowTitle("Eliminar Producto")
        msg.setIcon(QMessageBox.Question)
        msg.setText(f"¿Estás seguro de eliminar el producto '{p['nombre']}'?")
        btn_si = msg.addButton("🗑️ï¸ Sí, Eliminar", QMessageBox.YesRole)
        btn_si.setStyleSheet("background-color: #dc2626; color: white; font-weight: 700; padding: 8px 18px; border-radius: 7px; border: none;")
        btn_no = msg.addButton("Cancelar", QMessageBox.NoRole)
        btn_no.setStyleSheet("background-color: #f1f5f9; color: #1e293b; border: 1.5px solid #cbd5e1; font-weight: 700; padding: 8px 18px; border-radius: 7px;")
        msg.exec()
        if msg.clickedButton() == btn_si:
            delete_product(p["id"])
            QMessageBox.information(self, "Eliminado", "Producto eliminado correctamente.")
            self.cargar_todo()
            self.products_changed.emit()


# Alias de compatibilidad
InventoryWindow = UnifiedInventoryWindow
ProductsWindow = UnifiedInventoryWindow
