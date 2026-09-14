from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QDialog,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QMessageBox,
    QFrame,
    QDoubleSpinBox,
    QScrollArea,
)
from modules.ventas.sales_service import (
    get_credit_debts,
    register_debt_payment,
    get_debt_payments,
    get_debt_detail,
    get_debts_by_client,
)
from modules.configuracion.exchange_rate_service import get_current_rate_value


class AbonoDialog(QDialog):
    """Diálogo minimalista y limpio para registrar abonos de dinero a fiados."""

    def __init__(self, deuda_id, cliente, factura, saldo_actual, total_venta, parent=None):
        super().__init__(parent)
        self.deuda_id = deuda_id
        self.cliente = cliente
        self.factura = factura
        self.saldo_actual = float(saldo_actual)
        self.total_venta = float(total_venta)
        self.monto_ingresado = 0.0

        self.setWindowTitle("Registrar Abono a Fiado")
        self.setWindowFlags(Qt.Window | Qt.WindowTitleHint | Qt.WindowSystemMenuHint | Qt.WindowCloseButtonHint)
        self.resize(460, 390)
        self.setMinimumSize(400, 350)
        self.crear_interfaz()

    def crear_interfaz(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(14)

        # Header suave
        h_box = QVBoxLayout()
        h_box.setSpacing(3)
        title = QLabel("Registrar Abono de Fiado")
        title.setObjectName("pageTitle")
        sub = QLabel(f"Cliente: <b>{self.cliente}</b>  ·  Factura #{self.factura}")
        sub.setObjectName("pageSubtitle")
        h_box.addWidget(title)
        h_box.addWidget(sub)
        layout.addLayout(h_box)

        # Resumen de Deuda Minimalista
        card = QFrame()
        card.setObjectName("card")
        c_layout = QVBoxLayout(card)
        c_layout.setContentsMargins(18, 18, 18, 18)
        c_layout.setSpacing(8)

        row_tot = QHBoxLayout()
        row_tot.addWidget(QLabel("Monto original:"))
        lbl_tot = QLabel(f"Bs {self.total_venta:,.2f}")
        lbl_tot.setObjectName("money")
        row_tot.addStretch()
        row_tot.addWidget(lbl_tot)
        c_layout.addLayout(row_tot)

        row_sal = QHBoxLayout()
        row_sal.addWidget(QLabel("Saldo pendiente:"))
        lbl_sal = QLabel(f"Bs {self.saldo_actual:,.2f}")
        lbl_sal.setObjectName("money")
        row_sal.addStretch()
        row_sal.addWidget(lbl_sal)
        c_layout.addLayout(row_sal)

        layout.addWidget(card)

        # Campo de entrada
        lbl_m = QLabel("Monto a abonar (Bs):")
        lbl_m.setObjectName("sectionLabel")
        layout.addWidget(lbl_m)

        self.spin_monto = QDoubleSpinBox()
        self.spin_monto.setRange(0.01, self.saldo_actual)
        self.spin_monto.setValue(self.saldo_actual)
        self.spin_monto.setDecimals(2)
        self.spin_monto.setPrefix("Bs ")
        layout.addWidget(self.spin_monto)

        # Accesos rápidos suaves
        quick_box = QHBoxLayout()
        quick_box.setSpacing(8)

        btn_total = QPushButton("Pagar Todo (100%)")
        btn_total.setProperty("variant", "ghost")
        btn_total.setToolTip("Abonar el saldo total pendiente")
        btn_total.clicked.connect(lambda: self.spin_monto.setValue(self.saldo_actual))

        btn_mitad = QPushButton("Pagar la Mitad (50%)")
        btn_mitad.setProperty("variant", "ghost")
        btn_mitad.setToolTip("Abonar la mitad del saldo pendiente")
        btn_mitad.clicked.connect(lambda: self.spin_monto.setValue(round(self.saldo_actual / 2.0, 2)))

        quick_box.addWidget(btn_total)
        quick_box.addWidget(btn_mitad)
        quick_box.addStretch()
        layout.addLayout(quick_box)

        layout.addStretch()

        # Botones de Acción
        actions = QHBoxLayout()
        btn_cancel = QPushButton("Cancelar")
        btn_cancel.setProperty("variant", "ghost")
        btn_cancel.setToolTip("Cerrar sin registrar el abono")
        btn_cancel.clicked.connect(self.reject)

        btn_guardar = QPushButton("Confirmar Abono")
        btn_guardar.setProperty("variant", "success")
        btn_guardar.setToolTip("Guardar el abono en la cuenta")
        btn_guardar.clicked.connect(self.confirmar_abono)

        actions.addWidget(btn_cancel)
        actions.addStretch()
        actions.addWidget(btn_guardar)
        layout.addLayout(actions)

    def confirmar_abono(self):
        monto = self.spin_monto.value()
        if monto <= 0:
            QMessageBox.warning(self, "Aviso", "Ingresa un monto mayor que cero.")
            return
        if monto > self.saldo_actual:
            QMessageBox.warning(self, "Aviso", f"El monto no puede superar el saldo pendiente (Bs {self.saldo_actual:,.2f}).")
            return
        self.monto_ingresado = monto
        self.accept()


def _sincronizar_en_segundo_plano():
    try:
        from modules.sync.sync_service import is_configured, sync_now
        import threading
        if is_configured():
            threading.Thread(target=sync_now, daemon=True).start()
    except Exception:
        pass


class DetalleClienteDialog(QDialog):
    """Un cliente, una cuenta: sus facturas fiadas con productos y abonos."""

    def __init__(self, cliente_id, parent=None):
        super().__init__(parent)
        self.cliente_id = cliente_id
        self.facturas = []
        self.setWindowTitle("Detalle de Cuenta - Fiado")
        self.setWindowFlags(Qt.Window | Qt.WindowTitleHint | Qt.WindowSystemMenuHint | Qt.WindowCloseButtonHint)
        self.resize(700, 580)
        self.setMinimumSize(560, 440)
        self._construir()
        self.cargar()

    def _construir(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(22, 18, 22, 18)
        layout.setSpacing(10)

        self.lbl_title = QLabel("Cuenta")
        self.lbl_title.setObjectName("pageTitle")
        self.lbl_sub = QLabel("")
        self.lbl_sub.setObjectName("pageSubtitle")
        self.lbl_sub.setWordWrap(True)
        layout.addWidget(self.lbl_title)
        layout.addWidget(self.lbl_sub)

        lbl_f = QLabel("FACTURAS FIADAS")
        lbl_f.setObjectName("sectionLabel")
        layout.addWidget(lbl_f)

        self.tabla_facturas = QTableWidget()
        self.tabla_facturas.verticalHeader().setVisible(False)
        self.tabla_facturas.setColumnCount(5)
        self.tabla_facturas.setHorizontalHeaderLabels(["Factura", "Fecha", "Total USD", "Saldo USD", "Estado"])
        self.tabla_facturas.setEditTriggers(QTableWidget.NoEditTriggers)
        self.tabla_facturas.setSelectionBehavior(QTableWidget.SelectRows)
        self.tabla_facturas.setSelectionMode(QTableWidget.SingleSelection)
        self.tabla_facturas.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tabla_facturas.itemSelectionChanged.connect(self.mostrar_factura)
        layout.addWidget(self.tabla_facturas)

        lbl_p = QLabel("PRODUCTOS DE LA FACTURA SELECCIONADA")
        lbl_p.setObjectName("sectionLabel")
        layout.addWidget(lbl_p)

        self.tabla_productos = QTableWidget()
        self.tabla_productos.verticalHeader().setVisible(False)
        self.tabla_productos.setColumnCount(5)
        self.tabla_productos.setHorizontalHeaderLabels(["Cant.", "Producto", "Precio USD", "Precio Bs", "Subtotal Bs"])
        self.tabla_productos.setEditTriggers(QTableWidget.NoEditTriggers)
        self.tabla_productos.setSelectionBehavior(QTableWidget.SelectRows)
        self.tabla_productos.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.tabla_productos.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        layout.addWidget(self.tabla_productos, 1)

        self.lbl_pagos = QLabel("")
        self.lbl_pagos.setWordWrap(True)
        layout.addWidget(self.lbl_pagos)

        btn_box = QHBoxLayout()
        btn_box.addStretch()
        self.btn_abonar_factura = QPushButton("Abonar esta factura")
        self.btn_abonar_factura.setProperty("variant", "success")
        self.btn_abonar_factura.setToolTip("Registrar un abono a la factura seleccionada")
        self.btn_abonar_factura.clicked.connect(self.abonar_factura)
        btn_box.addWidget(self.btn_abonar_factura)
        btn_cerrar = QPushButton("Cerrar")
        btn_cerrar.setProperty("variant", "ghost")
        btn_cerrar.clicked.connect(self.accept)
        btn_box.addWidget(btn_cerrar)
        layout.addLayout(btn_box)

    def _tasa(self):
        try:
            return get_current_rate_value() or 0
        except Exception:
            return 0

    def cargar(self):
        try:
            self.facturas = get_debts_by_client(self.cliente_id) or []
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))
            self.reject()
            return
        if not self.facturas:
            QMessageBox.information(self, "Aviso", "Este cliente ya no tiene facturas fiadas.")
            self.reject()
            return
        rate = self._tasa()
        try:
            det0 = get_debt_detail(int(self.facturas[0]["id"]))
            nombre = str(det0.get("cliente", {}).get("nombre") or "Cliente")
        except Exception:
            nombre = "Cliente"
        total_usd = sum(float(f.get("total_usd") or 0) for f in self.facturas)
        saldo_usd = sum(float(f.get("saldo_usd") or 0) for f in self.facturas)
        self.lbl_title.setText(f"{nombre} — {len(self.facturas)} factura(s)")
        self.lbl_sub.setText(
            f"Total fiado: Bs {total_usd * rate:,.2f} (${total_usd:,.2f}) · "
            f"Saldo pendiente: Bs {saldo_usd * rate:,.2f} (${saldo_usd:,.2f})"
        )
        self.tabla_facturas.setRowCount(0)
        for f in sorted(self.facturas, key=lambda x: int(x.get("id") or 0)):
            row = self.tabla_facturas.rowCount()
            self.tabla_facturas.insertRow(row)
            f_total = float(f.get("total_usd") or 0)
            f_saldo = float(f.get("saldo_usd") or 0)
            item_fac = QTableWidgetItem(f"#{f.get('numero_factura')}")
            item_fac.setData(Qt.UserRole, int(f.get("id")))
            self.tabla_facturas.setItem(row, 0, item_fac)
            self.tabla_facturas.setItem(row, 1, QTableWidgetItem(str(f.get("fecha") or "")[:19]))
            self.tabla_facturas.setItem(row, 2, QTableWidgetItem(f"$ {f_total:,.2f}"))
            self.tabla_facturas.setItem(row, 3, QTableWidgetItem(f"$ {f_saldo:,.2f}"))
            self.tabla_facturas.setItem(row, 4, QTableWidgetItem("Pagada" if f_saldo <= 0.001 else "Pendiente"))
        if self.tabla_facturas.rowCount():
            self.tabla_facturas.selectRow(0)
        self.mostrar_factura()

    def _factura_seleccionada(self):
        row = self.tabla_facturas.currentRow()
        if row < 0:
            return None
        item = self.tabla_facturas.item(row, 0)
        if not item:
            return None
        try:
            fid = int(item.data(Qt.UserRole) or 0)
        except Exception:
            return None
        for f in self.facturas:
            try:
                if int(f.get("id")) == fid:
                    return f
            except Exception:
                continue
        return None

    def mostrar_factura(self):
        f = self._factura_seleccionada()
        self.tabla_productos.setRowCount(0)
        if not f:
            self.lbl_pagos.setText("")
            self.btn_abonar_factura.setEnabled(False)
            return
        rate = self._tasa()
        try:
            det = get_debt_detail(int(f["id"]))
            items = det.get("items", [])
            pagos = det.get("pagos", [])
        except Exception:
            items, pagos = [], []
        for it in items:
            try:
                cant = float(it.get("cantidad") or 0)
            except Exception:
                cant = 0
            try:
                p_usd = float(it.get("precio_usd") or 0)
            except Exception:
                p_usd = 0
            p_bs = p_usd * rate if rate else 0
            row = self.tabla_productos.rowCount()
            self.tabla_productos.insertRow(row)
            self.tabla_productos.setItem(row, 0, QTableWidgetItem(f"{cant:g}"))
            self.tabla_productos.setItem(row, 1, QTableWidgetItem(f"{it.get('codigo','')} - {it.get('nombre','')}"))
            self.tabla_productos.setItem(row, 2, QTableWidgetItem(f"${p_usd:,.2f}"))
            self.tabla_productos.setItem(row, 3, QTableWidgetItem(f"Bs {p_bs:,.2f}"))
            self.tabla_productos.setItem(row, 4, QTableWidgetItem(f"Bs {cant * p_bs:,.2f}"))
        if pagos:
            txt = "<b>Abonos de esta factura:</b><br>" + "<br>".join(
                f"• <b>Bs {float(p.get('monto_bs') or 0):,.2f}</b> — {p.get('fecha','')}" for p in pagos
            )
        else:
            txt = "<i>Sin abonos registrados en esta factura.</i>"
        self.lbl_pagos.setText(txt)
        try:
            saldo_f = float(f.get("saldo_usd") or 0)
        except Exception:
            saldo_f = 0
        self.btn_abonar_factura.setEnabled(saldo_f > 0.001)

    def abonar_factura(self):
        f = self._factura_seleccionada()
        if not f:
            return
        rate = self._tasa()
        det = get_debt_detail(int(f["id"]))
        deuda = det["deuda"]
        cliente = det.get("cliente", {})
        total_bs = float(deuda.get("total_usd") or 0) * rate if rate else 0
        saldo_bs = float(deuda.get("saldo_usd") or 0) * rate if rate else 0
        if saldo_bs <= 0.001:
            QMessageBox.information(self, "Aviso", "Esta factura ya se encuentra 100% pagada.")
            return
        dlg = AbonoDialog(int(f["id"]), str(cliente.get("nombre") or ""), str(deuda.get("numero_factura") or ""), saldo_bs, total_bs, self)
        if dlg.exec() == QDialog.Accepted:
            try:
                nuevo = register_debt_payment(int(f["id"]), dlg.monto_ingresado)
                QMessageBox.information(
                    self, "Abono Registrado",
                    f"Abono de Bs {dlg.monto_ingresado:,.2f} registrado.\n\nSaldo restante de la factura: Bs {nuevo:,.2f}",
                )
                self.cargar()
                try:
                    self.parent().cargar_deudas()
                except Exception:
                    pass
                _sincronizar_en_segundo_plano()
            except Exception as e:
                QMessageBox.critical(self, "Error", str(e))


class FiadosWindow(QDialog):
    # Se emite cuando el usuario quiere fiarle más al cliente seleccionado.
    # dict: {'id','nombre','telefono','cedula'}
    fiar_mas_solicitado = Signal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Clientes y Cuentas por Cobrar")
        # Permitir maximizar, minimizar y redimensionar libremente
        self.setWindowFlags(Qt.Window | Qt.WindowTitleHint | Qt.WindowSystemMenuHint | Qt.WindowMinMaxButtonsHint | Qt.WindowCloseButtonHint)
        self.resize(1020, 640)
        self.setMinimumSize(780, 480)
        self.deudas = []
        self.grupos = []
        self.cliente_seleccionado = None
        self.crear_interfaz()
        self.cargar_deudas()

    def crear_interfaz(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(14)
        layout.setContentsMargins(24, 18, 24, 18)

        # Header limpio y minimalista
        header_layout = QHBoxLayout()
        title_box = QVBoxLayout()
        title_box.setSpacing(2)
        title_label = QLabel("Clientes y Cuentas por Cobrar")
        title_label.setObjectName("pageTitle")
        sub_label = QLabel("Un cliente, una fila: selecciona para ver sus facturas, productos y abonos.")
        sub_label.setObjectName("pageSubtitle")
        title_box.addWidget(title_label)
        title_box.addWidget(sub_label)
        header_layout.addLayout(title_box)
        header_layout.addStretch()

        btn_refresh = QPushButton("Actualizar")
        btn_refresh.setProperty("variant", "ghost")
        btn_refresh.setToolTip("Recargar las cuentas por cobrar")
        btn_refresh.clicked.connect(self.cargar_deudas)
        header_layout.addWidget(btn_refresh)
        layout.addLayout(header_layout)

        # Resumen Minimalista (KPIs duales BS + USD)
        kpi_row = QHBoxLayout()
        kpi_row.setSpacing(12)

        self.lbl_kpi_total = self._crear_kpi_item("TOTAL EN CRÉDITO", "Bs 0,00")
        frame_total = QFrame()
        frame_total.setObjectName("kpi")
        frame_total.setLayout(self.lbl_kpi_total)
        kpi_row.addWidget(frame_total)

        self.lbl_kpi_total_usd = self._crear_kpi_item("TOTAL USD", "$ 0,00")
        frame_total_usd = QFrame()
        frame_total_usd.setObjectName("kpi")
        frame_total_usd.setLayout(self.lbl_kpi_total_usd)
        kpi_row.addWidget(frame_total_usd)

        self.lbl_kpi_pendiente = self._crear_kpi_item("SALDO PENDIENTE", "Bs 0,00", destacado=True)
        frame_pend = QFrame()
        frame_pend.setObjectName("kpi")
        frame_pend.setLayout(self.lbl_kpi_pendiente)
        kpi_row.addWidget(frame_pend)

        self.lbl_kpi_pendiente_usd = self._crear_kpi_item("SALDO USD", "$ 0,00", destacado=True)
        frame_pend_usd = QFrame()
        frame_pend_usd.setObjectName("kpi")
        frame_pend_usd.setLayout(self.lbl_kpi_pendiente_usd)
        kpi_row.addWidget(frame_pend_usd)

        self.lbl_kpi_cobrado = self._crear_kpi_item("TOTAL RECUPERADO", "Bs 0,00")
        frame_cob = QFrame()
        frame_cob.setObjectName("kpi")
        frame_cob.setLayout(self.lbl_kpi_cobrado)
        kpi_row.addWidget(frame_cob)

        layout.addLayout(kpi_row)

        # Buscador y Filtros
        lbl_buscar = QLabel("BUSCAR Y FILTRAR")
        lbl_buscar.setObjectName("sectionLabel")
        layout.addWidget(lbl_buscar)
        search_layout = QHBoxLayout()
        search_layout.setSpacing(10)
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Buscar por nombre de cliente, teléfono o número de factura...")
        self.search_input.textChanged.connect(self.filtrar_tabla)
        search_layout.addWidget(self.search_input)

        self.btn_pendientes = QPushButton("Pendientes")
        self.btn_pendientes.setCheckable(True)
        self.btn_pendientes.setChecked(True)
        self.btn_pendientes.setToolTip("Mostrar solo cuentas pendientes")
        self.btn_pendientes.clicked.connect(lambda: self._set_filtro("pendientes"))

        self.btn_todos = QPushButton("Todos")
        self.btn_todos.setCheckable(True)
        self.btn_todos.setToolTip("Mostrar todas las cuentas")
        self.btn_todos.clicked.connect(lambda: self._set_filtro("todos"))

        self.filtro_estado = "pendientes"
        self._actualizar_estilo_filtros()

        search_layout.addWidget(self.btn_pendientes)
        search_layout.addWidget(self.btn_todos)
        layout.addLayout(search_layout)

        # Tabla: un cliente, una fila (su deuda total; el detalle va por dentro)
        self.tabla = QTableWidget()
        self.tabla.verticalHeader().setVisible(False)
        self.tabla.setColumnCount(8)
        self.tabla.setHorizontalHeaderLabels([
            "Cliente",
            "Teléfono",
            "Facturas",
            "Total Venta",
            "Total USD",
            "Saldo Pendiente",
            "Saldo USD",
            "Estado",
        ])
        self.tabla.setFocusPolicy(Qt.NoFocus)
        self.tabla.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tabla.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.tabla.horizontalHeader().setSectionResizeMode(7, QHeaderView.ResizeToContents)
        self.tabla.setSelectionBehavior(QTableWidget.SelectRows)
        self.tabla.setSelectionMode(QTableWidget.SingleSelection)
        self.tabla.setEditTriggers(QTableWidget.NoEditTriggers)
        self.tabla.itemSelectionChanged.connect(self._on_seleccion_cambiada)
        self.tabla.doubleClicked.connect(self.ver_detalle_productos)
        layout.addWidget(self.tabla)

        # Barra Inferior de Acción y Selección
        self.bottom_bar = QFrame()
        self.bottom_bar.setObjectName("card")
        b_layout = QHBoxLayout(self.bottom_bar)
        b_layout.setContentsMargins(18, 14, 18, 14)
        b_layout.setSpacing(12)

        self.lbl_seleccion_info = QLabel("<i>Selecciona un cliente de la tabla para gestionar su cuenta</i>")
        self.lbl_seleccion_info.setObjectName("pageSubtitle")
        self.lbl_seleccion_info.setWordWrap(True)
        b_layout.addWidget(self.lbl_seleccion_info)
        b_layout.addStretch()

        self.btn_historial = QPushButton("Ver Historial")
        self.btn_historial.setProperty("variant", "ghost")
        self.btn_historial.setToolTip("Ver abonos del cliente en todas sus facturas")
        self.btn_historial.setEnabled(False)
        self.btn_historial.clicked.connect(self.ver_historial_abonos)
        b_layout.addWidget(self.btn_historial)

        self.btn_detalle = QPushButton("Ver Detalle")
        self.btn_detalle.setProperty("variant", "soft")
        self.btn_detalle.setToolTip("Ver facturas del cliente con sus productos y abonos")
        self.btn_detalle.setEnabled(False)
        self.btn_detalle.clicked.connect(self.ver_detalle_productos)
        b_layout.addWidget(self.btn_detalle)

        self.btn_fiar_mas = QPushButton("Fiar más a este cliente")
        self.btn_fiar_mas.setProperty("variant", "ghost")
        self.btn_fiar_mas.setToolTip("Ir a Ventas con este cliente elegido para fiarle más")
        self.btn_fiar_mas.setEnabled(False)
        self.btn_fiar_mas.clicked.connect(self.fiar_mas_a_cliente)
        b_layout.addWidget(self.btn_fiar_mas)

        self.btn_abonar = QPushButton("Cobrar / Registrar Abono")
        self.btn_abonar.setProperty("variant", "success")
        self.btn_abonar.setToolTip("Registrar un abono a la cuenta seleccionada")
        self.btn_abonar.setEnabled(False)
        self.btn_abonar.clicked.connect(self.registrar_abono_seleccionado)
        b_layout.addWidget(self.btn_abonar)

        layout.addWidget(self.bottom_bar)

    def _crear_kpi_item(self, title, default_val, destacado=False):
        vbox = QVBoxLayout()
        vbox.setSpacing(2)
        vbox.setContentsMargins(14, 10, 14, 10)
        lbl_t = QLabel(title)
        lbl_t.setObjectName("kpiLabel")
        lbl_t.setWordWrap(True)
        lbl_v = QLabel(default_val)
        lbl_v.setObjectName("kpiValue")
        lbl_v.setWordWrap(True)
        if destacado:
            lbl_v.setProperty("accent", "brand")
        vbox.addWidget(lbl_t)
        vbox.addWidget(lbl_v)
        vbox.val_label = lbl_v
        return vbox

    def _crear_separador(self):
        sep = QFrame()
        sep.setFrameShape(QFrame.VLine)
        sep.setFrameShadow(QFrame.Sunken)
        return sep

    def _set_filtro(self, filtro):
        self.filtro_estado = filtro
        self._actualizar_estilo_filtros()
        self.filtrar_tabla()

    def _actualizar_estilo_filtros(self):
        if self.filtro_estado == "pendientes":
            self.btn_pendientes.setProperty("variant", "soft")
            self.btn_todos.setProperty("variant", "ghost")
        else:
            self.btn_todos.setProperty("variant", "soft")
            self.btn_pendientes.setProperty("variant", "ghost")
        for btn in (self.btn_pendientes, self.btn_todos):
            btn.style().unpolish(btn)
            btn.style().polish(btn)

    def cargar_deudas(self):
        self.deudas = get_credit_debts()
        rate = get_current_rate_value() or 0
        # USD es fuente de verdad; BS se recalcula con tasa actual
        total_usd = sum(float(d.get("total_usd") or 0) for d in self.deudas)
        saldo_usd = sum(float(d.get("saldo_usd") or 0) for d in self.deudas)
        total_bs = total_usd * rate if rate else 0
        pendiente_bs = saldo_usd * rate if rate else 0
        cobrado_bs = total_bs - pendiente_bs

        self.lbl_kpi_total.val_label.setText(f"Bs {total_bs:,.2f}")
        self.lbl_kpi_total_usd.val_label.setText(f"$ {total_usd:,.2f}")
        self.lbl_kpi_pendiente.val_label.setText(f"Bs {pendiente_bs:,.2f}")
        self.lbl_kpi_pendiente_usd.val_label.setText(f"$ {saldo_usd:,.2f}")
        self.lbl_kpi_cobrado.val_label.setText(f"Bs {cobrado_bs:,.2f}")

        self.filtrar_tabla()

    def _agrupar_por_cliente(self):
        """Agrupa las deudas por cliente: un cliente, una fila con su total."""
        grupos = {}
        for d in self.deudas:
            cid = d.get("cliente_id")
            key = ("id", cid) if cid is not None else ("n", str(d.get("nombre") or "").strip().lower())
            g = grupos.get(key)
            if g is None:
                g = {
                    "cliente_id": cid,
                    "nombre": str(d.get("nombre") or "Cliente"),
                    "telefono": str(d.get("telefono") or ""),
                    "cedula": str(d.get("cedula") or ""),
                    "deudas": [],
                }
                grupos[key] = g
            g["deudas"].append(d)
        lista = []
        for g in grupos.values():
            g["deudas"].sort(key=lambda x: int(x.get("id") or 0))
            g["num_facturas"] = len(g["deudas"])
            g["total_usd"] = sum(float(x.get("total_usd") or 0) for x in g["deudas"])
            g["saldo_usd"] = sum(float(x.get("saldo_usd") or 0) for x in g["deudas"])
            lista.append(g)
        lista.sort(key=lambda g: (-g["saldo_usd"], g["nombre"].lower()))
        return lista

    def filtrar_tabla(self):
        query = self.search_input.text().strip().lower()
        self.tabla.setRowCount(0)
        self.grupos = []
        rate = get_current_rate_value() or 0

        for g in self._agrupar_por_cliente():
            cliente = g["nombre"]
            telefono = g["telefono"]
            facturas_txt = " ".join(str(x.get("numero_factura") or "") for x in g["deudas"])
            total_usd = g["total_usd"]
            saldo_usd = g["saldo_usd"]
            total = total_usd * rate if rate else 0
            saldo = saldo_usd * rate if rate else 0
            estado = "Pagada" if saldo_usd <= 0.001 else "Pendiente"

            if self.filtro_estado == "pendientes" and saldo_usd <= 0.001:
                continue

            if query and query not in cliente.lower() and query not in facturas_txt.lower() and query not in telefono.lower():
                continue

            self.grupos.append(g)
            row = self.tabla.rowCount()
            self.tabla.insertRow(row)

            item_cli = QTableWidgetItem(cliente)
            item_cli.setData(Qt.UserRole, g["cliente_id"])
            item_tel = QTableWidgetItem(telefono if telefono else "—")
            item_fac = QTableWidgetItem(f"{g['num_facturas']} factura(s)")
            item_tot = QTableWidgetItem(f"Bs {total:,.2f}")
            item_tot.setData(Qt.UserRole, total)
            item_tot_usd = QTableWidgetItem(f"$ {total_usd:,.2f}")
            item_sal = QTableWidgetItem(f"Bs {saldo:,.2f}")
            item_sal.setData(Qt.UserRole, saldo)
            item_sal_usd = QTableWidgetItem(f"$ {saldo_usd:,.2f}")
            item_est = QTableWidgetItem(estado)

            self.tabla.setItem(row, 0, item_cli)
            self.tabla.setItem(row, 1, item_tel)
            self.tabla.setItem(row, 2, item_fac)
            self.tabla.setItem(row, 3, item_tot)
            self.tabla.setItem(row, 4, item_tot_usd)
            self.tabla.setItem(row, 5, item_sal)
            self.tabla.setItem(row, 6, item_sal_usd)
            self.tabla.setItem(row, 7, item_est)

        self._on_seleccion_cambiada()

    def _grupo_seleccionado(self):
        row = self.tabla.currentRow()
        if row < 0 or row >= len(getattr(self, "grupos", [])):
            return None
        return self.grupos[row]

    def _on_seleccion_cambiada(self):
        g = self._grupo_seleccionado()
        if g is not None:
            rate = get_current_rate_value() or 0
            saldo = g["saldo_usd"] * rate if rate else 0
            total = g["total_usd"] * rate if rate else 0
            cliente = g["nombre"]
            nfac = g["num_facturas"]
            if saldo > 0.001:
                self.lbl_seleccion_info.setText(
                    f"Seleccionado: <b>{cliente}</b> — {nfac} factura(s) · "
                    f"Total fiado: Bs {total:,.2f} · Deuda total: <b>Bs {saldo:,.2f}</b>"
                )
                self.btn_abonar.setEnabled(True)
            else:
                self.lbl_seleccion_info.setText(
                    f"Seleccionado: <b>{cliente}</b> — {nfac} factura(s) · <i>Cuenta 100% pagada</i>"
                )
                self.btn_abonar.setEnabled(False)
            self.btn_historial.setEnabled(True)
            self.btn_detalle.setEnabled(True)
            self.btn_fiar_mas.setEnabled(True)
        else:
            self.lbl_seleccion_info.setText("<i>Selecciona un cliente de la tabla para gestionar su cuenta</i>")
            self.btn_abonar.setEnabled(False)
            self.btn_historial.setEnabled(False)
            self.btn_detalle.setEnabled(False)
            self.btn_fiar_mas.setEnabled(False)

    def ver_detalle_productos(self):
        g = self._grupo_seleccionado()
        if not g or g.get("cliente_id") is None:
            QMessageBox.information(self, "Aviso", "Selecciona un cliente de la tabla.")
            return
        try:
            dlg = DetalleClienteDialog(int(g["cliente_id"]), self)
            dlg.exec()
            self.cargar_deudas()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo abrir el detalle:\n\n{e}")

    def fiar_mas_a_cliente(self):
        g = self._grupo_seleccionado()
        if not g:
            QMessageBox.information(self, "Aviso", "Selecciona un cliente de la tabla.")
            return
        cliente = {
            "id": g.get("cliente_id"),
            "nombre": str(g.get("nombre") or ""),
            "telefono": str(g.get("telefono") or ""),
            "cedula": str(g.get("cedula") or ""),
        }
        # Emitir para que el Dashboard abra Ventas con este cliente ya elegido.
        try:
            self.fiar_mas_solicitado.emit(cliente)
        except Exception:
            pass
        # Fallback si se usa como diálogo suelto (sin Dashboard escuchando):
        # igual informamos que ya puede ir a Ventas; no duplicará al cliente.
        if self.parent() is None:
            QMessageBox.information(
                self,
                "Fiar más",
                f"Ve a Ventas y elige método Fiado con cliente '{cliente['nombre']}'.\n"
                f"Lo nuevo quedará en su misma cuenta sin duplicarlo.",
            )

    def registrar_abono_seleccionado(self):
        g = self._grupo_seleccionado()
        if not g:
            QMessageBox.information(self, "Aviso", "Selecciona un cliente de la tabla.")
            return
        rate = get_current_rate_value() or 0
        pendientes = sorted(
            [d for d in g["deudas"] if float(d.get("saldo_usd") or 0) > 0.001],
            key=lambda x: int(x.get("id") or 0),
        )
        if not pendientes:
            QMessageBox.information(self, "Aviso", "Esta cuenta ya se encuentra 100% pagada.")
            return
        cliente = g["nombre"]
        total_bs = g["total_usd"] * rate if rate else 0
        saldo_total_bs = g["saldo_usd"] * rate if rate else 0

        dialog = AbonoDialog(0, cliente, f"{len(pendientes)} factura(s)", saldo_total_bs, total_bs, self)
        if dialog.exec() != QDialog.Accepted:
            return
        monto = dialog.monto_ingresado
        try:
            restante = float(monto)
            afectadas = 0
            for d in pendientes:
                if restante <= 0.001:
                    break
                try:
                    saldo_d = float(d.get("saldo_bs") or 0)
                except Exception:
                    saldo_d = 0
                if saldo_d <= 0.001 and rate:
                    saldo_d = float(d.get("saldo_usd") or 0) * rate
                pago = min(restante, saldo_d)
                if pago <= 0.001:
                    continue
                try:
                    register_debt_payment(int(d["id"]), round(pago, 2))
                except Exception:
                    # Saldo cambiado por otro cobro simultáneo: releer y reintentar.
                    det = get_debt_detail(int(d["id"]))
                    fresco = float(det["deuda"].get("saldo_bs") or 0)
                    pago2 = min(restante, fresco)
                    if pago2 <= 0.001:
                        continue
                    register_debt_payment(int(d["id"]), round(pago2, 2))
                    pago = pago2
                restante -= pago
                afectadas += 1
            self.cargar_deudas()
            g2 = next((x for x in self._agrupar_por_cliente() if x.get("cliente_id") == g.get("cliente_id")), None)
            saldo_rest = (g2["saldo_usd"] * rate if rate and g2 else 0)
            QMessageBox.information(
                self,
                "Abono Registrado",
                f"Se registró el abono de Bs {monto:,.2f} a {cliente}, repartido en {afectadas} factura(s).\n\nSaldo restante total: Bs {saldo_rest:,.2f}",
            )
            _sincronizar_en_segundo_plano()
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))
            self.cargar_deudas()

    def ver_historial_abonos(self):
        g = self._grupo_seleccionado()
        if not g:
            QMessageBox.information(self, "Aviso", "Selecciona un cliente para ver sus abonos.")
            return
        cliente = g["nombre"]
        bloques = []
        for d in sorted(g["deudas"], key=lambda x: int(x.get("id") or 0)):
            try:
                pagos = get_debt_payments(int(d["id"]))
            except Exception:
                pagos = []
            if pagos:
                lineas = "".join(f"• <b>Bs {float(p.get('monto_bs') or 0):,.2f}</b> — {p.get('fecha','')}<br>" for p in pagos)
                bloques.append(f"<b>Factura #{d.get('numero_factura')}</b><br>{lineas}")
        if not bloques:
            QMessageBox.information(self, "Historial de Abonos", f"Aún no se han registrado abonos para {cliente}.")
            return
        QMessageBox.information(self, "Historial de Abonos", f"<b>Historial de Abonos - {cliente}</b><br><br>" + "<br>".join(bloques))
