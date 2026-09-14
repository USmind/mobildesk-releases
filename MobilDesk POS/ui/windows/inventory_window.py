from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QApplication,
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
    get_suppliers,
    create_supplier,
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

NUEVA_CATEGORIA = "__nueva_categoria__"
NUEVO_PROVEEDOR = "__nuevo_proveedor__"


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
        # Tamaño adaptativo: cabe en cualquier PC (usa el área libre real,
        # descontando barra de tareas). Nunca más alto que la pantalla.
        try:
            avail = QApplication.primaryScreen().availableGeometry()
            w = min(760, avail.width() - 60)
            h = min(800, avail.height() - 60)
        except Exception:
            w, h = 720, 700
        self.resize(max(640, w), max(560, h))
        self.setMinimumSize(620, 540)
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
        # Estilo global proveniente de ui/theme.py (GLOBAL_QSS aplicado en app).
        # Sin stylesheets locales: botones usan variant, etiquetas usan objectName.
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(24, 18, 24, 18)
        main_layout.setSpacing(12)

        # Encabezado
        title = QLabel("MODIFICAR PRODUCTO" if self.es_edicion else "NUEVO PRODUCTO")
        title.setObjectName("pageTitle")
        main_layout.addWidget(title)
        sub = QLabel("Completa los datos y fija el precio de venta con la calculadora.")
        sub.setObjectName("pageSubtitle")
        main_layout.addWidget(sub)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll_content = QWidget()
        layout = QVBoxLayout(scroll_content)
        layout.setSpacing(14)
        layout.setContentsMargins(4, 4, 4, 4)

        # Formulario Superior
        form_grid = QGridLayout()
        form_grid.setHorizontalSpacing(14)
        form_grid.setVerticalSpacing(12)
        form_grid.setColumnStretch(0, 1)
        form_grid.setColumnStretch(1, 1)

        # Fila 0 y 1: Código (escaneable) y Nombre
        lbl_cod = QLabel("CÓDIGO / CÓDIGO DE BARRAS (*)")
        lbl_cod.setObjectName("sectionLabel")
        lbl_cod.setWordWrap(True)
        form_grid.addWidget(lbl_cod, 0, 0)
        self.txt_codigo = QLineEdit()
        self.txt_codigo.setPlaceholderText("Escanea o escribe el código de barras")
        if not self.es_edicion and self.codigo_precargado:
            self.txt_codigo.setText(self.codigo_precargado)
        form_grid.addWidget(self.txt_codigo, 1, 0)

        lbl_nom = QLabel("NOMBRE DEL PRODUCTO (*)")
        lbl_nom.setObjectName("sectionLabel")
        lbl_nom.setWordWrap(True)
        form_grid.addWidget(lbl_nom, 0, 1)
        self.txt_nombre = QLineEdit()
        self.txt_nombre.setPlaceholderText("Ej: Arroz Blanco 1Kg")
        form_grid.addWidget(self.txt_nombre, 1, 1)

        # Fila 2 y 3: Unidad de Medida
        lbl_uni = QLabel("UNIDAD DE MEDIDA")
        lbl_uni.setObjectName("sectionLabel")
        form_grid.addWidget(lbl_uni, 2, 0)
        self.combo_unidad = QComboBox()
        self.combo_unidad.addItems(UNIDADES)
        form_grid.addWidget(self.combo_unidad, 3, 0)

        # Fila 4 y 5: Categoría y Proveedor lado a lado (opcionales)
        lbl_cat = QLabel("CATEGORÍA")
        lbl_cat.setObjectName("sectionLabel")
        form_grid.addWidget(lbl_cat, 4, 0)
        lbl_prov = QLabel("PROVEEDOR")
        lbl_prov.setObjectName("sectionLabel")
        form_grid.addWidget(lbl_prov, 4, 1)
        self.combo_categoria = QComboBox()
        self.combo_proveedor = QComboBox()
        form_grid.addWidget(self.combo_categoria, 5, 0)
        form_grid.addWidget(self.combo_proveedor, 5, 1)
        self._cargar_combo_categoria()
        self._cargar_combo_proveedor()
        self.combo_categoria.currentIndexChanged.connect(self._on_categoria_cambiada)
        self.combo_proveedor.currentIndexChanged.connect(self._on_proveedor_cambiado)

        layout.addLayout(form_grid)

        # ====================================================
        # CALCULADORA DE PRECIOS Y GANANCIA
        # ====================================================
        calc_box = QFrame()
        calc_box.setObjectName("card")
        calc_layout = QVBoxLayout(calc_box)
        calc_layout.setSpacing(12)
        calc_layout.setContentsMargins(16, 14, 16, 14)

        lbl_calc_title = QLabel("CALCULADORA DE PRECIOS Y GANANCIA")
        lbl_calc_title.setObjectName("sectionLabel")
        calc_layout.addWidget(lbl_calc_title)

        prices_grid = QGridLayout()
        prices_grid.setHorizontalSpacing(14)
        prices_grid.setVerticalSpacing(12)
        prices_grid.setColumnStretch(0, 1)
        prices_grid.setColumnStretch(1, 1)
        prices_grid.setColumnStretch(2, 1)

        # Etiquetas (Fila 0)
        lbl_p1 = QLabel("COSTO BASE ($ USD)")
        lbl_p1.setObjectName("sectionLabel")
        lbl_p2 = QLabel("GANANCIA (%)")
        lbl_p2.setObjectName("sectionLabel")
        lbl_p3 = QLabel("PRECIO VENTA ($ USD)")
        lbl_p3.setObjectName("sectionLabel")
        prices_grid.addWidget(lbl_p1, 0, 0)
        prices_grid.addWidget(lbl_p2, 0, 1)
        prices_grid.addWidget(lbl_p3, 0, 2)

        # Inputs (Fila 1)
        self.txt_costo_usd = QLineEdit("0.00")
        self.txt_costo_usd.textChanged.connect(self._recalcular_desde_costo)
        prices_grid.addWidget(self.txt_costo_usd, 1, 0)

        self.txt_margen_pct = QLineEdit(str(self.margen_configurado if self.margen_configurado > 0 else 30.0))
        self.txt_margen_pct.textChanged.connect(self._recalcular_desde_costo)
        prices_grid.addWidget(self.txt_margen_pct, 1, 1)

        self.txt_precio_usd = QLineEdit("0.00")
        self.txt_precio_usd.textChanged.connect(self._recalcular_desde_precio_usd)
        prices_grid.addWidget(self.txt_precio_usd, 1, 2)

        # Botones Rápidos de Margen (Fila 2, a todo lo ancho)
        quick_btns = QHBoxLayout()
        quick_btns.setSpacing(12)
        for pct in [15, 20, 30, 40, 50]:
            btn_pct = QPushButton(f"{pct}%")
            btn_pct.setProperty("variant", "soft")
            btn_pct.setToolTip(f"Aplicar margen de ganancia del {pct}%")
            btn_pct.clicked.connect(lambda ch=False, val=pct: self._aplicar_margen_rapido(val))
            quick_btns.addWidget(btn_pct)
        prices_grid.addLayout(quick_btns, 2, 0, 1, 3)

        calc_layout.addLayout(prices_grid)

        # Resumen en Bolívares
        self.lbl_preview_bs = QLabel("")
        self.lbl_preview_bs.setObjectName("money")
        self.lbl_preview_bs.setWordWrap(True)
        calc_layout.addWidget(self.lbl_preview_bs)

        layout.addWidget(calc_box)
        scroll.setWidget(scroll_content)
        main_layout.addWidget(scroll, 1)

        # Botones Inferiores
        actions = QHBoxLayout()
        actions.setSpacing(12)
        btn_cancel = QPushButton("Cancelar")
        btn_cancel.setProperty("variant", "ghost")
        btn_cancel.setToolTip("Cerrar sin guardar cambios")
        btn_cancel.clicked.connect(self.reject)
        actions.addWidget(btn_cancel)

        actions.addStretch()

        btn_save = QPushButton("Guardar Producto")
        btn_save.setProperty("variant", "success")
        btn_save.setToolTip("Guardar los datos del producto")
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
                f"Precio al Público: ${precio_usd:,.2f} USD  —  Bs {precio_bs:,.2f} (Tasa: {tasa_str})  |  Ganancia: +${ganancia_usd:,.2f}"
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
                f"Precio al Público: ${precio_usd:,.2f} USD  —  Bs {precio_bs:,.2f} (Tasa: {tasa_str})  |  Ganancia: +${ganancia_usd:,.2f}"
            )
        except Exception:
            pass

    def _cargar_combo_categoria(self, seleccionar_id=None):
        self.combo_categoria.blockSignals(True)
        try:
            self.combo_categoria.clear()
            self.combo_categoria.addItem("Sin categoría", None)
            try:
                categorias = get_categories()
            except Exception:
                categorias = []
            for c in categorias:
                self.combo_categoria.addItem(c["nombre"], c["id"])
            self.combo_categoria.addItem("＋ Nueva categoría...", NUEVA_CATEGORIA)
            if seleccionar_id is not None:
                idx = self.combo_categoria.findData(seleccionar_id)
                if idx >= 0:
                    self.combo_categoria.setCurrentIndex(idx)
        finally:
            self.combo_categoria.blockSignals(False)

    def _cargar_combo_proveedor(self, seleccionar_id=None):
        self.combo_proveedor.blockSignals(True)
        try:
            self.combo_proveedor.clear()
            self.combo_proveedor.addItem("Sin proveedor", None)
            try:
                proveedores = get_suppliers()
            except Exception:
                proveedores = []
            for s in proveedores:
                self.combo_proveedor.addItem(s["nombre"], s["id"])
            self.combo_proveedor.addItem("＋ Nuevo proveedor...", NUEVO_PROVEEDOR)
            if seleccionar_id is not None:
                idx = self.combo_proveedor.findData(seleccionar_id)
                if idx >= 0:
                    self.combo_proveedor.setCurrentIndex(idx)
        finally:
            self.combo_proveedor.blockSignals(False)

    def _on_categoria_cambiada(self, index):
        if self.combo_categoria.itemData(index) == NUEVA_CATEGORIA:
            nombre, ok = QInputDialog.getText(self, "Nueva categoría", "Nombre de la categoría:")
            if ok and (nombre or "").strip():
                try:
                    nuevo_id = create_category(nombre.strip())
                except Exception as e:
                    QMessageBox.warning(self, "Aviso", f"No se pudo crear la categoría: {e}")
                    self.combo_categoria.setCurrentIndex(0)
                    return
                self._cargar_combo_categoria(seleccionar_id=nuevo_id)
            else:
                self.combo_categoria.setCurrentIndex(0)

    def _on_proveedor_cambiado(self, index):
        if self.combo_proveedor.itemData(index) == NUEVO_PROVEEDOR:
            nombre, ok = QInputDialog.getText(self, "Nuevo proveedor", "Nombre del proveedor:")
            if ok and (nombre or "").strip():
                try:
                    nuevo_id = create_supplier(nombre.strip())
                except ValueError as e:
                    # Ya existe: seleccionar el existente en vez de duplicar
                    try:
                        existentes = get_suppliers()
                    except Exception:
                        existentes = []
                    hallado = next((s["id"] for s in existentes if str(s["nombre"]).strip().lower() == nombre.strip().lower()), None)
                    if hallado is not None:
                        self._cargar_combo_proveedor(seleccionar_id=hallado)
                    else:
                        QMessageBox.warning(self, "Aviso", str(e))
                        self.combo_proveedor.setCurrentIndex(0)
                    return
                except Exception as e:
                    QMessageBox.warning(self, "Aviso", f"No se pudo crear el proveedor: {e}")
                    self.combo_proveedor.setCurrentIndex(0)
                    return
                self._cargar_combo_proveedor(seleccionar_id=nuevo_id)
            else:
                self.combo_proveedor.setCurrentIndex(0)

    def cargar_datos_si_edicion(self):
        if not self.producto:
            return
        p = self.producto
        self.txt_codigo.setText(p["codigo"])
        self.txt_nombre.setText(p["nombre"])
        self.combo_unidad.setCurrentText(p["unidad"] if ("unidad" in p.keys() and p["unidad"]) else "Unidad")
        try:
            cat_id = p["categoria_id"] if ("categoria_id" in p.keys() and p["categoria_id"]) else None
        except Exception:
            cat_id = None
        try:
            prov_id = p["proveedor_id"] if ("proveedor_id" in p.keys() and p["proveedor_id"]) else None
        except Exception:
            prov_id = None
        self._cargar_combo_categoria(seleccionar_id=cat_id)
        self._cargar_combo_proveedor(seleccionar_id=prov_id)

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

        categoria_id = self.combo_categoria.currentData()
        if categoria_id == NUEVA_CATEGORIA:
            categoria_id = None
        proveedor_id = self.combo_proveedor.currentData()
        if proveedor_id == NUEVO_PROVEEDOR:
            proveedor_id = None
        self.datos_resultado = {
            "codigo": codigo,
            "nombre": nombre,
            "unidad": self.combo_unidad.currentText(),
            "precio_usd": precio_usd,
            "stock_minimo": 0,
            "stock_inicial": 0,
            "categoria_id": categoria_id,
            "proveedor_id": proveedor_id,
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
        self.setMinimumSize(460, 300)
        self.crear_interfaz(productos, tipo_inicial)

    def crear_interfaz(self, productos, tipo_inicial):
        layout = QFormLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(24, 18, 24, 18)

        lbl_sec = QLabel("DATOS DEL MOVIMIENTO")
        lbl_sec.setObjectName("sectionLabel")
        layout.addRow(lbl_sec)

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
        info.setObjectName("pageSubtitle")
        layout.addRow(info)

        botones = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        botones.button(QDialogButtonBox.Ok).setText("Guardar")
        botones.button(QDialogButtonBox.Cancel).setText("Cancelar")
        botones.button(QDialogButtonBox.Ok).setToolTip("Guardar el movimiento de inventario")
        botones.button(QDialogButtonBox.Cancel).setToolTip("Cerrar sin guardar cambios")
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
        layout.setContentsMargins(24, 18, 24, 18)

        titulo = QLabel("HISTORIAL DE MOVIMIENTOS")
        titulo.setObjectName("pageTitle")
        layout.addWidget(titulo)
        sub = QLabel("Consulta entradas y ajustes registrados en el inventario.")
        sub.setObjectName("pageSubtitle")
        layout.addWidget(sub)

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
        acciones.setSpacing(12)
        boton_modificar = QPushButton("Modificar Motivo")
        boton_eliminar = QPushButton("Eliminar Movimiento")
        boton_modificar.setProperty("variant", "ghost")
        boton_modificar.setToolTip("Editar el motivo del movimiento seleccionado")
        boton_eliminar.setProperty("variant", "danger")
        boton_eliminar.setToolTip("Eliminar el movimiento seleccionado")
        boton_modificar.clicked.connect(self.modificar_movimiento)
        boton_eliminar.clicked.connect(self.eliminar_movimiento)
        acciones.addWidget(boton_modificar)
        acciones.addWidget(boton_eliminar)
        acciones.addStretch()

        boton_cerrar = QPushButton("Cerrar")
        boton_cerrar.setProperty("variant", "ghost")
        boton_cerrar.setToolTip("Cerrar el historial")
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
        btn_si = msg.addButton("Sí, Eliminar", QMessageBox.YesRole)
        btn_si.setProperty("variant", "danger")
        btn_no = msg.addButton("Cancelar", QMessageBox.NoRole)
        btn_no.setProperty("variant", "ghost")
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
        # Estilo global proveniente de ui/theme.py (GLOBAL_QSS aplicado en app).
        # Sin stylesheets locales: botones usan variant, etiquetas usan objectName.
        layout = QVBoxLayout(self)
        layout.setSpacing(14)
        layout.setContentsMargins(24, 18, 24, 18)

        # Fila 1: Encabezado con Tasa
        header_layout = QHBoxLayout()
        head_box = QVBoxLayout()
        head_box.setSpacing(2)
        titulo = QLabel("INVENTARIO Y GESTIÓN DE PRODUCTOS")
        titulo.setObjectName("pageTitle")
        head_sub = QLabel("Crea productos, ajusta existencias y controla precios y stock.")
        head_sub.setObjectName("pageSubtitle")
        head_box.addWidget(titulo)
        head_box.addWidget(head_sub)
        header_layout.addLayout(head_box)
        header_layout.addStretch()

        self.lbl_tasa_info = QLabel("Cargando tasa...")
        self.lbl_tasa_info.setObjectName("money")
        header_layout.addWidget(self.lbl_tasa_info)
        layout.addLayout(header_layout)

        # Fila 2: Barra de Botones de Acción con Colores Vivos y Efectos Hover
        botones_layout = QHBoxLayout()
        botones_layout.setSpacing(12)

        btn_nuevo = QPushButton("Nuevo Producto")
        btn_nuevo.setToolTip("Registrar un producto nuevo")
        btn_nuevo.clicked.connect(self.nuevo_producto)
        botones_layout.addWidget(btn_nuevo)

        btn_modificar = QPushButton("Modificar")
        btn_modificar.setProperty("variant", "ghost")
        btn_modificar.setToolTip("Editar el producto seleccionado")
        btn_modificar.clicked.connect(self.modificar_producto)
        botones_layout.addWidget(btn_modificar)

        btn_entrada = QPushButton("Entrada Stock")
        btn_entrada.setProperty("variant", "success")
        btn_entrada.setToolTip("Sumar existencias al inventario")
        btn_entrada.clicked.connect(self.nueva_entrada)
        botones_layout.addWidget(btn_entrada)

        btn_ajuste = QPushButton("Ajuste Stock")
        btn_ajuste.setProperty("variant", "soft")
        btn_ajuste.setToolTip("Corregir existencias por merma o conteo")
        btn_ajuste.clicked.connect(self.nuevo_ajuste)
        botones_layout.addWidget(btn_ajuste)

        btn_historial = QPushButton("Historial")
        btn_historial.setProperty("variant", "ghost")
        btn_historial.setToolTip("Ver movimientos de inventario")
        btn_historial.clicked.connect(self.mostrar_historial)
        botones_layout.addWidget(btn_historial)

        btn_eliminar = QPushButton("Eliminar")
        btn_eliminar.setProperty("variant", "danger")
        btn_eliminar.setToolTip("Eliminar el producto seleccionado")
        btn_eliminar.clicked.connect(self.eliminar_producto)
        botones_layout.addWidget(btn_eliminar)

        botones_layout.addStretch()
        layout.addLayout(botones_layout)

        # Fila 3: Barra de Búsqueda Completa (No cortada)
        self.txt_buscar = QLineEdit()
        self.txt_buscar.setPlaceholderText("Buscar producto por nombre, código o categoría...")
        self.txt_buscar.setMinimumHeight(38)
        self.txt_buscar.textChanged.connect(self.filtrar_tabla)
        layout.addWidget(self.txt_buscar)

        # Fila 4: Tabla Principal Unificada con Columnas Espaciosas
        self.tabla = QTableWidget()
        self.tabla.verticalHeader().setVisible(False)
        self.tabla.setColumnCount(7)
        self.tabla.setHorizontalHeaderLabels([
            "Código", "Producto", "Categoría", "Proveedor", "Unidad", "Precio Venta (USD / Bs)", "Stock Disponible"
        ])
        self.tabla.setEditTriggers(QTableWidget.NoEditTriggers)
        self.tabla.setSelectionBehavior(QTableWidget.SelectRows)
        self.tabla.setSelectionMode(QTableWidget.SingleSelection)
        self.tabla.setFocusPolicy(Qt.NoFocus)
        self.tabla.verticalHeader().setVisible(False)

        # Ajuste de tamaño de columnas
        self.tabla.setColumnWidth(0, 110)
        self.tabla.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.tabla.setColumnWidth(2, 130)
        self.tabla.setColumnWidth(3, 130)
        self.tabla.setColumnWidth(4, 90)
        self.tabla.horizontalHeader().setSectionResizeMode(5, QHeaderView.Stretch)
        self.tabla.setColumnWidth(6, 140)

        self.tabla.doubleClicked.connect(self.modificar_producto)
        layout.addWidget(self.tabla)

    def cargar_tasa(self):
        con = get_connection()
        try:
            row = con.execute("SELECT valor FROM exchange_rates ORDER BY id DESC LIMIT 1").fetchone()
            self.tasa_actual = float(row["valor"]) if row else 0.0
            tasa_str = f"1 USD = {self.tasa_actual:,.2f} Bs" if self.tasa_actual > 0 else "Tasa No configurada"
            self.lbl_tasa_info.setText(f"Tasa Actual: {tasa_str}")
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
            cat = str(p["categoria"] or "").lower() if "categoria" in p.keys() else ""
            prov = str(p["proveedor"] or "").lower() if "proveedor" in p.keys() else ""
            if not busqueda or busqueda in nombre or busqueda in codigo or busqueda in cb or busqueda in cat or busqueda in prov:
                filtrados.append(p)

        self.tabla.setRowCount(len(filtrados))
        for fila, p in enumerate(filtrados):
            precio_usd = float(p["precio_usd"] if p["precio_usd"] is not None else 0.0)
            precio_bs = precio_usd * self.tasa_actual
            stock_act = float(p["stock_actual"] if ("stock_actual" in p.keys() and p["stock_actual"] is not None) else 0.0)

            precio_str = f"${precio_usd:,.2f}  (Bs {precio_bs:,.2f})"
            uni_name = p["unidad"] if ("unidad" in p.keys() and p["unidad"]) else "Unidad"
            cat_name = p["categoria"] if ("categoria" in p.keys() and p["categoria"]) else "Sin categoría"
            prov_name = p["proveedor"] if ("proveedor" in p.keys() and p["proveedor"]) else "Sin proveedor"

            valores = [
                p["codigo"],
                p["nombre"],
                cat_name,
                prov_name,
                uni_name,
                precio_str,
                f"{stock_act:g}"
            ]

            for col, val in enumerate(valores):
                item = QTableWidgetItem(str(val))
                if col in (4, 6):
                    item.setTextAlignment(Qt.AlignCenter)
                if col == 6 and stock_act <= 0:
                    item.setToolTip("Agotado / Sin Stock")
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
                    codigo_barras=d["codigo_barras"],
                    proveedor_id=d.get("proveedor_id"),
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
                    codigo_barras=d["codigo_barras"],
                    proveedor_id=d.get("proveedor_id"),
                    codigo=d["codigo"],
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
        btn_si = msg.addButton("Sí, Eliminar", QMessageBox.YesRole)
        btn_si.setProperty("variant", "danger")
        btn_no = msg.addButton("Cancelar", QMessageBox.NoRole)
        btn_no.setProperty("variant", "ghost")
        msg.exec()
        if msg.clickedButton() == btn_si:
            delete_product(p["id"])
            QMessageBox.information(self, "Eliminado", "Producto eliminado correctamente.")
            self.cargar_todo()
            self.products_changed.emit()


# Alias de compatibilidad
InventoryWindow = UnifiedInventoryWindow
ProductsWindow = UnifiedInventoryWindow
