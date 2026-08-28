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
    QHeaderView,
    QCompleter,
    QInputDialog,
    QSizePolicy,
    QFrame
)

from PySide6.QtCore import Qt, QStringListModel, Signal

from modules.ventas.sales_service import (
    get_sale_products,
    get_product_stock,
    create_sale,
    get_sales_history,
    get_credit_debts,
    register_debt_payment,
    get_debt_payments
)

from modules.configuracion.exchange_rate_service import (
    get_current_rate_value, sale_price_usd
)
from modules.productos.product_service import create_product, ProductoYaExiste
from ui.windows.inventory_window import ProductDialog
from ui.windows.ticket_preview_dialog import TicketPreviewDialog


class SalesWindow(QWidget):
    sale_registered = Signal()

    def __init__(self, usuario):

        super().__init__()

        self.usuario = usuario

        self.productos = []

        self.setWindowTitle(
            "Gestión de Ventas"
        )

        self.resize(
            1100,
            650
        )

        self.crear_interfaz()

        self.cargar_productos()

        self.cargar_tasa()

    # ==================================================
    # INTERFAZ
    # ==================================================
    def crear_interfaz(self):
        self.setStyleSheet("""
            QWidget { font-family: 'Segoe UI', sans-serif; }
            QLabel { color: #0f172a; font-weight: 600; border: none; background: transparent; font-size: 13.5px; }
            QLineEdit {
                background: white;
                border: 1.5px solid #cbd5e1;
                border-radius: 8px;
                padding: 7px 12px;
                font-size: 13.5px;
                color: #0f172a;
            }
            QLineEdit:focus { border: 2px solid #2563eb; }
            QComboBox {
                background: white;
                border: 1.5px solid #cbd5e1;
                border-radius: 8px;
                padding: 6px 12px;
                font-size: 13.5px;
                color: #0f172a;
            }
            QPushButton {
                background-color: #2563eb;
                color: #ffffff;
                border: none;
                border-radius: 7px;
                padding: 8px 16px;
                font-weight: 700;
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
                min-width: 85px;
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
            QComboBox:focus { border: 2px solid #2563eb; }
            QTableWidget {
                background: white;
                border: 1px solid #cbd5e1;
                border-radius: 10px;
                gridline-color: #f1f5f9;
                font-size: 13.5px;
                color: #0f172a;
            }
            QTableWidget::item { padding: 6px; }
            QTableWidget::item:selected { background: #dbeafe; color: #1e3a8a; }
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
        layout.setSpacing(12)
        layout.setContentsMargins(16, 12, 16, 12)

        # Header de Ventas
        header_vta = QHBoxLayout()
        titulo = QLabel("🛒 PUNTO DE VENTA (FACTURACIÓN)")
        titulo.setStyleSheet("font-size: 21px; font-weight: 800; color: #0f172a; border: none;")
        header_vta.addWidget(titulo)
        header_vta.addStretch()

        self.tasa_label = QLabel("Tasa: No configurada")
        self.tasa_label.setStyleSheet("font-size: 14px; font-weight: 800; color: #1d4ed8; background: #eff6ff; padding: 6px 14px; border-radius: 8px; border: none;")
        header_vta.addWidget(self.tasa_label)
        layout.addLayout(header_vta)

        # Barra de Selección de Producto
        formulario = QHBoxLayout()
        formulario.setSpacing(8)

        lbl_prod = QLabel("Producto:")
        formulario.addWidget(lbl_prod)

        self.producto = QLineEdit()
        self.producto.setPlaceholderText("Buscar por código de barras o nombre...")
        self.producto.setMinimumWidth(320)
        self.producto.setMinimumHeight(38)
        formulario.addWidget(self.producto)

        lbl_cant = QLabel("Cantidad:")
        formulario.addWidget(lbl_cant)

        self.cantidad = QLineEdit()
        self.cantidad.setPlaceholderText("1")
        self.cantidad.setMaximumWidth(90)
        self.cantidad.setMinimumHeight(38)
        formulario.addWidget(self.cantidad)

        boton_agregar = QPushButton("➕ Agregar Producto")
        boton_agregar.setMinimumHeight(38)
        boton_agregar.setStyleSheet("""
            QPushButton {
                background: #2563eb;
                color: white;
                font-weight: 700;
                font-size: 13.5px;
                padding: 8px 18px;
                border-radius: 8px;
                border: none;
            }
            QPushButton:hover { background: #1d4ed8; }
        """)
        boton_agregar.clicked.connect(self.agregar_producto)
        formulario.addWidget(boton_agregar)

        formulario.addStretch()
        layout.addLayout(formulario)

        # Tabla de Carrito de Compras
        self.tabla = QTableWidget()
        self.tabla.verticalHeader().setVisible(False)
        self.tabla.setColumnCount(6)
        self.tabla.setHorizontalHeaderLabels([
            "Código", "Producto", "Cantidad", "Precio Bs", "Subtotal Bs", "Stock Disponible"
        ])
        self.tabla.setEditTriggers(QTableWidget.NoEditTriggers)
        self.tabla.setSelectionBehavior(QTableWidget.SelectRows)
        self.tabla.setFocusPolicy(Qt.NoFocus)

        self.tabla.setColumnWidth(0, 110)
        self.tabla.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.tabla.setColumnWidth(2, 100)
        self.tabla.setColumnWidth(3, 130)
        self.tabla.setColumnWidth(4, 140)
        self.tabla.setColumnWidth(5, 130)

        layout.addWidget(self.tabla)

        # Métodos de Pago y Datos del Cliente
        pago = QHBoxLayout()
        pago.setSpacing(10)
        lbl_met = QLabel("Método de Pago:")
        self.metodo_pago = QComboBox()
        self.metodo_pago.addItem("Efectivo", "efectivo")
        self.metodo_pago.addItem("Tarjeta / Débito", "tarjeta")
        self.metodo_pago.addItem("Pago móvil", "pago_movil")
        self.metodo_pago.addItem("Divisas ($ USD)", "divisas")
        self.metodo_pago.addItem("Fiado / Crédito", "fiado")
        self.metodo_pago.addItem("🔀 Pago Mixto / Fraccionado", "mixto")
        self.metodo_pago.setMinimumHeight(36)

        self.monto_recibido = QLineEdit()
        self.monto_recibido.setPlaceholderText("Monto recibido en Bs...")
        self.monto_recibido.setMaximumWidth(200)
        self.monto_recibido.setMinimumHeight(36)

        self.vuelto = QLabel("Vuelto: Bs 0.00")
        self.vuelto.setStyleSheet("font-size: 15px; font-weight: 800; color: #15803d; background: #f0fdf4; padding: 6px 14px; border-radius: 8px; border: 1px solid #bbf7d0;")

        self.btn_config_mixto = QPushButton("⚙️ Configurar Desglose")
        self.btn_config_mixto.setStyleSheet("""
            QPushButton {
                background-color: #2563eb;
                color: #ffffff;
                font-weight: 700;
                font-size: 13px;
                padding: 6px 14px;
                border-radius: 8px;
                min-height: 24px;
                border: none;
            }
            QPushButton:hover { background-color: #1d4ed8; }
        """)
        self.btn_config_mixto.setVisible(False)
        self.btn_config_mixto.clicked.connect(self.abrir_dialogo_pago_mixto)

        self.metodo_pago.currentIndexChanged.connect(self.actualizar_pago)
        self.monto_recibido.textChanged.connect(self.actualizar_pago)

        pago.addWidget(lbl_met)
        pago.addWidget(self.metodo_pago)
        pago.addWidget(self.monto_recibido)
        pago.addWidget(self.btn_config_mixto)
        pago.addWidget(self.vuelto)
        pago.addStretch()
        layout.addLayout(pago)

        cliente = QHBoxLayout()
        cliente.setSpacing(8)
        lbl_cli = QLabel("Cliente:")
        self.cliente_nombre, self.cliente_telefono = QLineEdit(), QLineEdit()
        self.cliente_direccion, self.cliente_cedula = QLineEdit(), QLineEdit()
        self.cliente_nombre.setPlaceholderText("Nombre (opcional / requerido en fiado)")
        self.cliente_telefono.setPlaceholderText("Teléfono")
        self.cliente_direccion.setPlaceholderText("Dirección")
        self.cliente_cedula.setPlaceholderText("Cédula / RIF")

        for c_input in (self.cliente_nombre, self.cliente_telefono, self.cliente_direccion, self.cliente_cedula):
            c_input.setMinimumHeight(34)

        cliente.addWidget(lbl_cli)
        cliente.addWidget(self.cliente_nombre)
        cliente.addWidget(self.cliente_telefono)
        cliente.addWidget(self.cliente_direccion)
        cliente.addWidget(self.cliente_cedula)
        layout.addLayout(cliente)

        # Fila de Totales y Botones de Acción
        resumen = QHBoxLayout()
        resumen.setSpacing(8)

        self.total_usd = QLabel("Total: Bs 0.00 ($0.00)")
        self.total_usd.setStyleSheet("""
            QLabel {
                font-size: 16.5px;
                font-weight: 800;
                color: #0f172a;
                background: #f8fafc;
                padding: 6px 12px;
                border-radius: 8px;
                border: 1.5px solid #cbd5e1;
            }
        """)
        self.total_usd.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.Fixed)

        resumen.addWidget(self.total_usd, 1)

        boton_eliminar = QPushButton("🗑️ Eliminar")
        boton_eliminar.setToolTip("Eliminar producto seleccionado")
        boton_eliminar.setStyleSheet("""
            QPushButton {
                background: #fef2f2;
                color: #dc2626;
                border: 1.5px solid #fca5a5;
                font-weight: 700;
                font-size: 13px;
                padding: 8px 12px;
                border-radius: 8px;
            }
            QPushButton:hover { background: #fee2e2; }
        """)
        boton_eliminar.clicked.connect(self.eliminar_producto)

        boton_vaciar = QPushButton("🧹 Cancelar")
        boton_vaciar.setToolTip("Vaciar carrito y cancelar venta actual")
        boton_vaciar.setStyleSheet("""
            QPushButton {
                background: #fff1f2;
                color: #e11d48;
                border: 1.5px solid #fecdd3;
                font-weight: 700;
                font-size: 13px;
                padding: 8px 12px;
                border-radius: 8px;
            }
            QPushButton:hover { background: #ffe4e6; }
        """)
        boton_vaciar.clicked.connect(self.vaciar_carrito)

        boton_historial = QPushButton("🧾 Historial")
        boton_historial.setToolTip("Ver historial de facturas y ventas")
        boton_historial.setStyleSheet("""
            QPushButton {
                background: #f8fafc;
                color: #1e293b;
                border: 1.5px solid #cbd5e1;
                font-weight: 700;
                font-size: 13px;
                padding: 8px 12px;
                border-radius: 8px;
            }
            QPushButton:hover { background: #e2e8f0; }
        """)
        boton_historial.clicked.connect(self.mostrar_historial)

        boton_vender = QPushButton("✅ Registrar Venta")
        boton_vender.setStyleSheet("""
            QPushButton {
                background: #16a34a;
                color: white;
                font-weight: 800;
                font-size: 14px;
                padding: 8px 18px;
                border-radius: 8px;
                border: none;
            }
            QPushButton:hover { background: #15803d; }
        """)
        boton_vender.clicked.connect(self.registrar_venta)

        resumen.addWidget(boton_eliminar)
        resumen.addWidget(boton_vaciar)
        resumen.addWidget(boton_historial)
        resumen.addWidget(boton_vender)

        layout.addLayout(resumen)
        self.actualizar_pago()

    # ==================================================
    # PRODUCTOS
    # ==================================================

    def cargar_productos(self):
        try:
            self.productos = get_sale_products()
        except Exception:
            self.productos = []
        self.cargar_tasa()

    def actualizar_autocompletado(self):
        try:
            tasa = get_current_rate_value() or 0.0
        except Exception:
            tasa = 0.0
        opciones = []
        for p in self.productos:
            try:
                precio_usd = float(p["precio_usd"] if p["precio_usd"] is not None else 0.0)
            except Exception:
                precio_usd = 0.0
            precio_bs = precio_usd * float(tasa) if tasa > 0 else 0.0
            opciones.append(f"{p['codigo']} - {p['nombre']} · {precio_bs:,.2f} Bs. ({precio_usd:,.2f}$)")

        modelo = QStringListModel(opciones, self)
        self.completador = QCompleter(modelo, self)
        self.completador.setCaseSensitivity(Qt.CaseInsensitive)
        self.completador.setFilterMode(Qt.MatchContains)
        self.producto.setCompleter(self.completador)

    # ==================================================
    # TASA
    # ==================================================

    def cargar_tasa(self):
        try:
            tasa = get_current_rate_value()
            if tasa is None or float(tasa) <= 0:
                self.tasa_label.setText("Tasa: No configurada")
            else:
                self.tasa_label.setText(f"Tasa actual: {float(tasa):,.2f} Bs/USD")
        except Exception:
            self.tasa_label.setText("Tasa: No configurada")

        try:
            self.actualizar_totales()
            self.actualizar_pago()
            self.actualizar_autocompletado()
        except Exception:
            pass

    # ==================================================
    # AGREGAR PRODUCTO
    # ==================================================

    def agregar_producto(self):
        if not self.productos:
            QMessageBox.warning(
                self,
                "Sin productos",
                "No existen productos disponibles."
            )
            return

        texto = self.cantidad.text().strip()
        if not texto:
            QMessageBox.warning(
                self,
                "Cantidad requerida",
                "Debe ingresar una cantidad."
            )
            return

        try:
            cantidad = float(texto.replace(",", "."))
        except ValueError:
            QMessageBox.warning(
                self,
                "Cantidad incorrecta",
                "La cantidad debe ser un número válido."
            )
            return

        if cantidad <= 0:
            QMessageBox.warning(
                self,
                "Cantidad incorrecta",
                "La cantidad debe ser mayor que cero."
            )
            return

        busqueda = self.producto.text().strip()
        if not busqueda:
            QMessageBox.warning(self, "Producto", "Busque y seleccione un producto.")
            self.producto.setFocus()
            return

        # Extraer el código si viene del autocompletado (ej: "P000001 - Chocolate · 300.00 Bs. (1.50$)")
        codigo_extraido = busqueda.split(" - ", 1)[0].strip().casefold()

        # 1. Búsqueda exacta por código interno O código de barras
        coincidencias = [
            item for item in self.productos
            if item["codigo"].casefold() == codigo_extraido
            or ((item["codigo_barras"] or "").casefold() == codigo_extraido)
        ]

        # 2. Si no coincide el código exacto, buscar coincidencias parciales por nombre, código o código de barras
        if not coincidencias:
            b_cf = busqueda.casefold()
            coincidencias = [
                item for item in self.productos
                if (b_cf == item["codigo"].casefold()
                    or b_cf == item["nombre"].casefold()
                    or (item["codigo_barras"] and b_cf == item["codigo_barras"].casefold())
                    or b_cf in item["codigo"].casefold()
                    or b_cf in item["nombre"].casefold()
                    or (item["codigo_barras"] and b_cf in item["codigo_barras"].casefold()))
            ]

        if len(coincidencias) == 0:
            # Producto no registrado: ofrecer crearlo al instante con el codigo escaneado
            respuesta = QMessageBox.question(
                self,
                "Producto no registrado",
                f"No existe un producto con el código:\n{busqueda}\n\n¿Deseas registrarlo ahora?",
                QMessageBox.Yes | QMessageBox.No
            )
            if respuesta != QMessageBox.Yes:
                self.producto.setFocus()
                return
            dialogo_nuevo = ProductDialog(None, self, codigo_precargado=busqueda)
            if dialogo_nuevo.exec() != QDialog.Accepted:
                self.producto.setFocus()
                return
            d_nuevo = dialogo_nuevo.datos_resultado
            try:
                create_product(
                    codigo=d_nuevo["codigo"],
                    nombre=d_nuevo["nombre"],
                    unidad=d_nuevo["unidad"],
                    precio_usd=d_nuevo["precio_usd"],
                    stock_inicial=0,
                    categoria_id=None,
                    stock_minimo=0,
                    codigo_barras=d_nuevo["codigo_barras"]
                )
            except ProductoYaExiste:
                QMessageBox.warning(self, "Producto", "El producto ya existe (se seleccionará el existente).")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"No se pudo guardar el producto: {e}")
                self.producto.setFocus()
                return
            self.cargar_productos()
            coincidencias = [p for p in self.productos if p["codigo"].casefold() == busqueda.casefold()]
            if not coincidencias:
                return
        elif len(coincidencias) > 1:
            QMessageBox.warning(
                self, "Producto", "Múltiples productos coinciden. Seleccione el producto específico de las sugerencias."
            )
            self.producto.setFocus()
            return

        producto = coincidencias[0]
        producto_id = producto["id"]

        if producto is None:

            QMessageBox.warning(
                self,
                "Producto",
                "No se encontró el producto."
            )

            return

        try:

            stock = get_product_stock(
                producto_id
            )

        except Exception as error:

            QMessageBox.critical(
                self,
                "Error",
                f"No se pudo consultar el stock.\n\n{error}"
            )

            return
        if producto is None:

            QMessageBox.warning(
                self,
                "Producto",
                "No se encontró el producto."
            )

            return

        try:

            stock = get_product_stock(
                producto_id
            )

        except Exception as error:

            QMessageBox.critical(
                self,
                "Error",
                f"No se pudo consultar el stock.\n\n{error}"
            )

            return

        if stock <= 0:
            QMessageBox.warning(
                self,
                "Sin Stock Disponible",
                f"El producto '{producto['nombre']}' no tiene stock disponible (Agotado).\nNo se puede registrar para la venta."
            )
            return

        if cantidad > stock:
            QMessageBox.warning(
                self,
                "Stock Insuficiente",
                f"No hay suficiente cantidad para '{producto['nombre']}'.\n\n"
                f"Stock disponible: {stock:g}\n"
                f"Cantidad solicitada: {cantidad:g}"
            )
            return

        tasa = get_current_rate_value()
        if tasa is None:
            QMessageBox.warning(self, "Tasa no configurada", "Configure la tasa USD/Bs antes de agregar productos.")
            return
        precio = sale_price_usd(producto["precio_usd"]) * float(tasa)
        fila = self.tabla.rowCount()
        self.tabla.insertRow(fila)

        item_cod = QTableWidgetItem(str(producto["codigo"]))
        item_nom = QTableWidgetItem(str(producto["nombre"]))

        qty_str = f"{int(cantidad)}" if float(cantidad).is_integer() else f"{cantidad:g}"
        item_can = QTableWidgetItem(qty_str)
        item_can.setData(Qt.UserRole, float(cantidad))

        item_pre = QTableWidgetItem(f"Bs {precio:,.2f}")
        item_pre.setData(Qt.UserRole, float(precio))

        subtotal = float(cantidad) * float(precio)
        item_sub = QTableWidgetItem(f"Bs {subtotal:,.2f}")
        item_sub.setData(Qt.UserRole, float(subtotal))

        stock_str = f"{int(stock)}" if float(stock).is_integer() else f"{stock:g}"
        item_stk = QTableWidgetItem(stock_str)
        item_stk.setData(Qt.UserRole, float(stock))

        self.tabla.setItem(fila, 0, item_cod)
        self.tabla.setItem(fila, 1, item_nom)
        self.tabla.setItem(fila, 2, item_can)
        self.tabla.setItem(fila, 3, item_pre)
        self.tabla.setItem(fila, 4, item_sub)
        self.tabla.setItem(fila, 5, item_stk)

        self.cantidad.clear()
        self.producto.clear()

        self.actualizar_totales()

    # ==================================================
    # ELIMINAR PRODUCTO
    # ==================================================

    def eliminar_producto(self):

        fila = self.tabla.currentRow()

        if fila < 0:

            QMessageBox.warning(
                self,
                "Selección requerida",
                "Debe seleccionar un producto de la tabla."
            )

            return

        self.tabla.removeRow(
            fila
        )

        self.actualizar_totales()

    def vaciar_carrito(self):
        if self.tabla.rowCount() == 0:
            return

        r = QMessageBox.question(
            self,
            "Cancelar Venta",
            "¿Estás seguro de que deseas vaciar el carrito y cancelar la venta actual?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if r == QMessageBox.Yes:
            self.tabla.setRowCount(0)
            self.actualizar_totales()
            self.cliente_nombre.clear()
            self.cliente_telefono.clear()
            self.cliente_direccion.clear()
            self.cliente_cedula.clear()
            self.monto_recibido.clear()
            self.datos_pago_mixto = None
            self.vuelto.setText("Vuelto: Bs 0.00")
            self.producto.setFocus()

    # ==================================================
    # TOTALES
    # ==================================================

    def actualizar_totales(self):
        total_bs = self.total_actual_bs()
        try:
            tasa = get_current_rate_value()
        except Exception:
            tasa = None

        total_usd = total_bs / float(tasa) if tasa else 0.0
        self.total_usd.setText(f"Total: Bs {total_bs:,.2f} (${total_usd:,.2f})")

        self.actualizar_pago()

    def total_actual_bs(self):
        tot = 0.0
        for fila in range(self.tabla.rowCount()):
            item = self.tabla.item(fila, 4)
            if item is not None:
                tot += float(item.data(Qt.UserRole) or 0.0)
        return tot

    def actualizar_pago(self):
        metodo = self.metodo_pago.currentData()
        es_mixto = (metodo == "mixto")
        requiere_calculadora = metodo in {"efectivo", "divisas"}
        self.monto_recibido.setVisible(requiere_calculadora)
        self.btn_config_mixto.setVisible(es_mixto)
        self.vuelto.setVisible(requiere_calculadora or es_mixto)
        if es_mixto:
            self.vuelto.setText("🔀 Pago Mixto: Haga clic en 'Configurar Desglose' o 'Registrar Venta'")
            return
        if not requiere_calculadora:
            self.vuelto.setText("Vuelto: Bs 0.00")
            return
        try:
            recibido = float((self.monto_recibido.text().strip() or "0").replace(",", "."))
            if metodo == "divisas":
                tasa = get_current_rate_value() or 0
                total_usd = self.total_actual_bs() / float(tasa) if tasa else 0
                vuelto_usd = max(0, recibido - total_usd)
                self.monto_recibido.setPlaceholderText("Monto recibido en USD")
                self.vuelto.setText(
                    f"Total: USD {total_usd:,.2f} | Bs {self.total_actual_bs():,.2f}  ·  "
                    f"Vuelto: USD {vuelto_usd:,.2f} | Bs {vuelto_usd * float(tasa):,.2f}"
                )
            else:
                vuelto = max(0, recibido - self.total_actual_bs())
                self.monto_recibido.setPlaceholderText("Monto recibido en Bs")
                self.vuelto.setText(f"Vuelto: Bs {vuelto:,.2f}")
        except ValueError:
            self.vuelto.setText("Vuelto: ingrese un monto válido")

    def abrir_dialogo_pago_mixto(self):
        if self.tabla.rowCount() == 0:
            QMessageBox.warning(self, "Venta Vacía", "Agregue al menos un producto antes de configurar el pago mixto.")
            return None
        tasa = get_current_rate_value()
        if not tasa:
            QMessageBox.warning(self, "Tasa No Configurada", "Debe configurar la tasa USD/Bs antes de procesar pagos.")
            return None
        from ui.windows.mixed_payment_dialog import MixedPaymentDialog
        total_bs = self.total_actual_bs()
        total_usd = total_bs / float(tasa)
        dlg = MixedPaymentDialog(total_bs, total_usd, tasa, parent=self)
        if dlg.exec():
            return dlg.datos_resultado
        return None

    # ==================================================
    # REGISTRAR VENTA
    # ==================================================

    def registrar_venta(self):
        from modules.licencia.license_service import init_or_get_license_info
        lic_info = init_or_get_license_info()
        if lic_info.get("bloqueado", False):
            QMessageBox.warning(
                self,
                "Licencia Requerida",
                "Tu período de prueba de 7 días ha finalizado.\n\n"
                "Para registrar ventas, por favor activa tu licencia en el menú 'Activar Licencia'."
            )
            return

        if self.tabla.rowCount() == 0:
            QMessageBox.warning(
                self,
                "Venta vacía",
                "Debe agregar al menos un producto."
            )
            return

        try:
            tasa = get_current_rate_value()
            if tasa is None:
                QMessageBox.warning(
                    self,
                    "Tasa no configurada",
                    "Debe configurar la tasa USD/Bs antes de registrar una venta."
                )
                return

            items = []
            for fila in range(self.tabla.rowCount()):
                codigo = self.tabla.item(fila, 0).text()
                item_can = self.tabla.item(fila, 2)
                cantidad = float(item_can.data(Qt.UserRole) if item_can.data(Qt.UserRole) is not None else item_can.text())

                item_pre = self.tabla.item(fila, 3)
                precio_bs = float(item_pre.data(Qt.UserRole) if item_pre.data(Qt.UserRole) is not None else 0.0)

                precio = precio_bs / float(tasa)
                producto_id = None
                for producto in self.productos:
                    if str(producto["codigo"]) == codigo:
                        producto_id = producto["id"]
                        break

                if producto_id is None:
                    raise ValueError(f"No se encontró el producto {codigo}.")

                items.append({
                    "producto_id": producto_id,
                    "cantidad": cantidad,
                    "precio_usd": precio
                })

            monto_recibido = None
            monto_recibido_usd = None
            pagos_detalle = None

            if self.metodo_pago.currentData() == "mixto":
                from ui.windows.mixed_payment_dialog import MixedPaymentDialog
                total_bs = self.total_actual_bs()
                total_usd = total_bs / float(tasa)
                dlg = MixedPaymentDialog(total_bs, total_usd, tasa, parent=self)
                if not dlg.exec():
                    return
                pagos_detalle = dlg.datos_resultado
                monto_recibido = pagos_detalle.get("efectivo_bs")
                monto_recibido_usd = pagos_detalle.get("divisas_usd")
            elif self.metodo_pago.currentData() in {"efectivo", "divisas"}:
                try:
                    recibido = float(self.monto_recibido.text().strip().replace(",", "."))
                except ValueError:
                    raise ValueError("Debe ingresar un monto recibido válido.")
                if self.metodo_pago.currentData() == "efectivo":
                    monto_recibido = recibido
                else:
                    monto_recibido_usd = recibido

            cliente = {"nombre": self.cliente_nombre.text(), "telefono": self.cliente_telefono.text(),
                       "direccion": self.cliente_direccion.text(), "cedula": self.cliente_cedula.text()}
            resultado = create_sale(
                self.usuario["id"], items,
                self.metodo_pago.currentData(), monto_recibido, monto_recibido_usd, cliente,
                self.metodo_pago.currentData() == "fiado", pagos_detalle
            )

            desglose_str = ""
            if resultado.get("metodo_pago") == "mixto" and resultado.get("pagos_detalle"):
                pd = resultado["pagos_detalle"]
                partes = []
                if pd.get("divisas_usd"): partes.append(f"  • Divisas ($): ${pd['divisas_usd']:,.2f} (Bs {pd.get('divisas_bs', 0):,.2f})")
                if pd.get("efectivo_bs"): partes.append(f"  • Efectivo: Bs {pd['efectivo_bs']:,.2f}")
                if pd.get("pago_movil_bs"): partes.append(f"  • Pago Móvil: Bs {pd['pago_movil_bs']:,.2f}")
                if pd.get("tarjeta_bs"): partes.append(f"  • Tarjeta: Bs {pd['tarjeta_bs']:,.2f}")
                if pd.get("fiado_bs"): partes.append(f"  • Fiado: Bs {pd['fiado_bs']:,.2f}")
                if partes:
                    desglose_str = "Desglose Recibido:\n" + "\n".join(partes) + "\n\n"

            msg = QMessageBox(self)
            msg.setWindowTitle("Venta Registrada")
            msg.setIcon(QMessageBox.Information)
            msg.setText(
                f"¡Venta registrada exitosamente!\n\n"
                f"• Factura: #{resultado['numero_factura']}\n"
                f"• Total Facturado: Bs {resultado['total_bs']:,.2f}\n"
                f"• Método de Pago: {self.metodo_pago.currentText()}\n\n"
                f"{desglose_str}"
                f"• Vuelto: Bs {resultado['vuelto_bs']:,.2f}"
                + (f"\n• Vuelto en Divisas: USD ${resultado['vuelto_usd']:,.2f}" if (resultado.get('metodo_pago') == 'divisas' or (resultado.get('pagos_detalle') and resultado['pagos_detalle'].get('vuelto_usd', 0) > 0)) else "")
                + "\n\n¿Deseas ver o imprimir el ticket de venta?"
            )
            btn_imprimir = msg.addButton("🖨️ Ver / Imprimir Ticket", QMessageBox.YesRole)
            btn_imprimir.setStyleSheet("background-color: #2563eb; color: white; font-weight: 700; padding: 8px 18px; border-radius: 7px; border: none;")
            btn_cerrar = msg.addButton("Continuar", QMessageBox.NoRole)
            btn_cerrar.setStyleSheet("background-color: #f1f5f9; color: #1e293b; border: 1.5px solid #cbd5e1; font-weight: 700; padding: 8px 18px; border-radius: 7px;")
            msg.exec()

            self.tabla.setRowCount(0)
            self.monto_recibido.clear()
            self.cliente_nombre.clear(); self.cliente_telefono.clear(); self.cliente_direccion.clear(); self.cliente_cedula.clear()

            self.actualizar_totales()
            self.cargar_productos()
            self.sale_registered.emit()

            try:
                from modules.sync.sync_service import is_configured, sync_now
                import threading
                if is_configured():
                    threading.Thread(target=sync_now, daemon=True).start()
            except Exception:
                pass

            if msg.clickedButton() == btn_imprimir:
                ticket_dlg = TicketPreviewDialog(resultado["venta_id"], self)
                ticket_dlg.exec()

        except ValueError as error:

            QMessageBox.warning(
                self,
                "Venta no permitida",
                str(error)
            )

        except Exception as error:

            QMessageBox.critical(
                self,
                "Error",
                f"No se pudo registrar la venta.\n\n{error}"
            )

    def mostrar_historial(self):
        try:
            parent_window = self.window()
            if hasattr(parent_window, "abrir_modulo"):
                parent_window.abrir_modulo("Historial")
            else:
                dialogo = SalesHistoryDialog(self)
                dialogo.exec()
        except Exception as error:
            QMessageBox.critical(
                self,
                "Error al abrir historial",
                f"No se pudo abrir el historial de ventas:\n\n{error}"
            )


class SalesHistoryWindow(QWidget):
    """Módulo integrado de Historial de Ventas para el panel principal de MobilDesk POS."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.ventas = []
        self.filtro_actual = "todas"
        self.setWindowTitle("Historial de Ventas - MobilDesk POS")
        self.crear_interfaz()
        self.cargar_historial()

    def crear_interfaz(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(20, 20, 20, 20)

        # Header
        h_layout = QHBoxLayout()
        titulo = QLabel("Historial de Ventas")
        titulo.setStyleSheet("font-size: 19px; font-weight: 800; color: #0f172a;")
        h_layout.addWidget(titulo)
        h_layout.addStretch()

        btn_refrescar = QPushButton("🔄 Actualizar")
        btn_refrescar.setStyleSheet("background: #f1f5f9; color: #334155; border: 1px solid #cbd5e1; font-weight: bold; padding: 6px 14px; border-radius: 6px;")
        btn_refrescar.clicked.connect(self.cargar_historial)
        h_layout.addWidget(btn_refrescar)
        layout.addLayout(h_layout)

        # KPIs Summary
        kpi_layout = QHBoxLayout()
        kpi_layout.setSpacing(10)
        self.card_count = self._crear_kpi_card("TOTAL FACTURAS", "0", "#2563eb")
        self.card_total_bs = self._crear_kpi_card("TOTAL VENTAS (BS)", "Bs 0,00", "#16a34a")
        self.card_total_usd = self._crear_kpi_card("TOTAL VENTAS (USD)", "$0,00", "#0284c7")
        kpi_layout.addWidget(self.card_count)
        kpi_layout.addWidget(self.card_total_bs)
        kpi_layout.addWidget(self.card_total_usd)
        layout.addLayout(kpi_layout)

        # Search and Filters
        search_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 Buscar por número de factura, cliente o cajero...")
        self.search_input.textChanged.connect(self.filtrar_tabla)
        search_layout.addWidget(self.search_input)

        self.btn_todas = QPushButton("Todas")
        self.btn_todas.clicked.connect(lambda: self._set_filtro("todas"))
        self.btn_hoy = QPushButton("Solo Hoy")
        self.btn_hoy.clicked.connect(lambda: self._set_filtro("hoy"))

        search_layout.addWidget(self.btn_todas)
        search_layout.addWidget(self.btn_hoy)
        layout.addLayout(search_layout)

        # Table
        self.tabla = QTableWidget()
        self.tabla.verticalHeader().setVisible(False)
        self.tabla.setColumnCount(8)
        self.tabla.setHorizontalHeaderLabels([
            "Factura #", "Fecha y Hora", "Cajero", "Cliente", "Método de Pago", "Total (Bs)", "Total (USD)", "Estado"
        ])
        self.tabla.setEditTriggers(QTableWidget.NoEditTriggers)
        self.tabla.setSelectionBehavior(QTableWidget.SelectRows)
        self.tabla.setSelectionMode(QTableWidget.SingleSelection)
        self.tabla.setFocusPolicy(Qt.NoFocus)
        self.tabla.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tabla.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.tabla.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.tabla.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeToContents)
        self.tabla.doubleClicked.connect(self.ver_ticket)
        layout.addWidget(self.tabla)

        # Actions
        acciones = QHBoxLayout()
        btn_ticket = QPushButton("🖨️ Ver / Imprimir Ticket")
        btn_ticket.setStyleSheet("background: #2563eb; color: white; font-weight: bold; padding: 10px 18px; border-radius: 8px; border: none;")
        btn_ticket.clicked.connect(self.ver_ticket)
        acciones.addWidget(btn_ticket)
        acciones.addStretch()

        layout.addLayout(acciones)
        self._actualizar_estilo_filtros()

    def cargar_todo(self):
        self.cargar_historial()

    def cargar_datos(self):
        self.cargar_historial()

    def _crear_kpi_card(self, title, val, color=""):
        """Tarjeta metrica neutral: fondo blanco plano, sin barras de color."""
        frame = QFrame()
        frame.setObjectName("kpiCard")
        frame.setStyleSheet("""
            QFrame#kpiCard {
                background-color: #ffffff;
                border: 1px solid #e2e8f0;
                border-radius: 10px;
            }
        """)
        vbox = QVBoxLayout(frame)
        vbox.setContentsMargins(14, 10, 14, 10)
        vbox.setSpacing(3)
        lbl_t = QLabel(title)
        lbl_t.setStyleSheet("font-size: 11px; font-weight: 700; color: #64748b; letter-spacing: 0.5px; border: none; background: transparent;")
        lbl_v = QLabel(val)
        lbl_v.setStyleSheet("font-size: 18px; font-weight: 700; color: #0f172a; border: none; background: transparent;")
        vbox.addWidget(lbl_t)
        vbox.addWidget(lbl_v)
        frame.val_label = lbl_v
        return frame

    def _set_filtro(self, filtro):
        self.filtro_actual = filtro
        self._actualizar_estilo_filtros()
        self.filtrar_tabla()

    def _actualizar_estilo_filtros(self):
        if self.filtro_actual == "hoy":
            self.btn_hoy.setStyleSheet("background: #2563eb; color: white; font-weight: 600; padding: 7px 16px; border-radius: 8px; border: none;")
            self.btn_todas.setStyleSheet("background: #f1f5f9; color: #475569; border: 1px solid #e2e8f0; font-weight: 600; padding: 7px 16px; border-radius: 8px;")
        else:
            self.btn_todas.setStyleSheet("background: #2563eb; color: white; font-weight: 600; padding: 7px 16px; border-radius: 8px; border: none;")
            self.btn_hoy.setStyleSheet("background: #f1f5f9; color: #475569; border: 1px solid #e2e8f0; font-weight: 600; padding: 7px 16px; border-radius: 8px;")

    def cargar_historial(self):
        try:
            self.ventas = get_sales_history() or []
        except Exception as e:
            self.ventas = []
            print(f"Error al obtener historial: {e}")
        self.filtrar_tabla()

    def filtrar_tabla(self):
        query = self.search_input.text().strip().lower()
        from datetime import date
        today_str = str(date.today())

        self.tabla.setRowCount(0)
        tot_bs = 0.0
        tot_usd = 0.0
        count = 0

        for venta in self.ventas:
            fac = str(venta["numero_factura"] if venta["numero_factura"] is not None else "")
            fecha = str(venta["fecha"] if venta["fecha"] is not None else "")
            cajero = str(venta["usuario_nombre"] if venta["usuario_nombre"] is not None else "")
            cliente = str(venta["cliente_nombre"] if venta["cliente_nombre"] is not None else "")
            raw_met = str(venta["metodo_pago"] if venta["metodo_pago"] is not None else "").strip().lower()

            if raw_met == "mixto":
                metodo = "🔀 Pago Mixto"
            elif raw_met == "pago_movil":
                metodo = "Pago Móvil"
            elif raw_met == "divisas":
                metodo = "Divisas ($ USD)"
            elif raw_met == "tarjeta":
                metodo = "Tarjeta / Débito"
            elif raw_met == "fiado":
                metodo = "Fiado / Crédito"
            else:
                metodo = raw_met.replace("_", " ").title()

            if self.filtro_actual == "hoy" and not fecha.startswith(today_str):
                continue

            if query and query not in fac.lower() and query not in cliente.lower() and query not in cajero.lower() and query not in metodo.lower():
                continue

            try:
                v_bs = float(venta["total_bs"] or 0)
            except Exception:
                v_bs = 0.0
            try:
                v_usd = float(venta["total_usd"] or 0)
            except Exception:
                v_usd = 0.0

            tot_bs += v_bs
            tot_usd += v_usd
            count += 1

            row = self.tabla.rowCount()
            self.tabla.insertRow(row)

            item_fac = QTableWidgetItem(f"#{fac}")
            item_fac.setData(Qt.UserRole, venta["id"])
            item_fecha = QTableWidgetItem(fecha[:19] if fecha else "—")
            item_cajero = QTableWidgetItem(cajero if cajero else "Sistema")
            item_cliente = QTableWidgetItem(cliente if cliente else "—")
            item_metodo = QTableWidgetItem(metodo)
            item_bs = QTableWidgetItem(f"Bs {v_bs:,.2f}")
            item_usd = QTableWidgetItem(f"${v_usd:,.2f}")
            
            estado_val = str(venta["estado"] if venta["estado"] is not None else "completada").title()
            item_estado = QTableWidgetItem(estado_val)

            self.tabla.setItem(row, 0, item_fac)
            self.tabla.setItem(row, 1, item_fecha)
            self.tabla.setItem(row, 2, item_cajero)
            self.tabla.setItem(row, 3, item_cliente)
            self.tabla.setItem(row, 4, item_metodo)
            self.tabla.setItem(row, 5, item_bs)
            self.tabla.setItem(row, 6, item_usd)
            self.tabla.setItem(row, 7, item_estado)

        self.card_count.val_label.setText(str(count))
        self.card_total_bs.val_label.setText(f"Bs {tot_bs:,.2f}")
        self.card_total_usd.val_label.setText(f"${tot_usd:,.2f}")

    def ver_ticket(self):
        row = self.tabla.currentRow()
        if row < 0:
            return QMessageBox.warning(self, "Ticket", "Selecciona una venta de la tabla.")
        item = self.tabla.item(row, 0)
        if not item:
            return
        venta_id = item.data(Qt.UserRole)
        if not venta_id:
            return
        try:
            dlg = TicketPreviewDialog(venta_id, self)
            dlg.exec()
        except Exception as e:
            QMessageBox.critical(self, "Error de Ticket", f"No se pudo abrir el ticket de la venta:\n\n{e}")


class SalesHistoryDialog(QDialog):
    """Diálogo modal para abrir el historial de ventas si se invoca como ventana flotante."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Historial de Ventas - MobilDesk POS")
        self.setWindowFlags(Qt.Window | Qt.WindowTitleHint | Qt.WindowSystemMenuHint | Qt.WindowMinMaxButtonsHint | Qt.WindowCloseButtonHint)
        self.resize(1100, 680)
        self.setMinimumSize(850, 520)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self.historial_widget = SalesHistoryWindow(self)
        layout.addWidget(self.historial_widget)
