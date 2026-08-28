from PySide6.QtCore import Qt
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
)


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
        layout.setContentsMargins(28, 24, 28, 24)
        layout.setSpacing(14)

        # Header suave
        h_box = QVBoxLayout()
        h_box.setSpacing(3)
        title = QLabel("Registrar Abono de Fiado")
        title.setStyleSheet("font-size: 18px; font-weight: 700; color: #1e293b;")
        sub = QLabel(f"Cliente: <b>{self.cliente}</b>  ·  Factura #{self.factura}")
        sub.setStyleSheet("font-size: 13px; color: #64748b;")
        h_box.addWidget(title)
        h_box.addWidget(sub)
        layout.addLayout(h_box)

        # Resumen de Deuda Minimalista
        card = QFrame()
        card.setObjectName("deudaCard")
        card.setStyleSheet("""
            QFrame#deudaCard {
                background-color: #f8fafc;
                border: 1px solid #e2e8f0;
                border-radius: 10px;
            }
            QFrame#deudaCard QLabel { border: none; background: transparent; }
        """)
        c_layout = QVBoxLayout(card)
        c_layout.setContentsMargins(16, 12, 16, 12)
        c_layout.setSpacing(6)

        row_tot = QHBoxLayout()
        row_tot.addWidget(QLabel("Monto original:"))
        lbl_tot = QLabel(f"Bs {self.total_venta:,.2f}")
        lbl_tot.setStyleSheet("font-weight: 600; color: #475569;")
        row_tot.addStretch()
        row_tot.addWidget(lbl_tot)
        c_layout.addLayout(row_tot)

        row_sal = QHBoxLayout()
        row_sal.addWidget(QLabel("Saldo pendiente:"))
        lbl_sal = QLabel(f"Bs {self.saldo_actual:,.2f}")
        lbl_sal.setStyleSheet("font-size: 16px; font-weight: 800; color: #0f172a;")
        row_sal.addStretch()
        row_sal.addWidget(lbl_sal)
        c_layout.addLayout(row_sal)

        layout.addWidget(card)

        # Campo de entrada
        lbl_m = QLabel("Monto a abonar (Bs):")
        lbl_m.setStyleSheet("font-size: 13px; font-weight: 600; color: #334155;")
        layout.addWidget(lbl_m)

        self.spin_monto = QDoubleSpinBox()
        self.spin_monto.setRange(0.01, self.saldo_actual)
        self.spin_monto.setValue(self.saldo_actual)
        self.spin_monto.setDecimals(2)
        self.spin_monto.setPrefix("Bs ")
        self.spin_monto.setStyleSheet(
            "QDoubleSpinBox { font-size: 17px; font-weight: bold; padding: 8px 12px; border: 1px solid #cbd5e1; border-radius: 8px; background: white; color: #0f172a; }"
        )
        layout.addWidget(self.spin_monto)

        # Accesos rápidos suaves
        quick_box = QHBoxLayout()
        quick_box.setSpacing(8)

        btn_total = QPushButton("Pagar Todo (100%)")
        btn_total.setStyleSheet("background: #f1f5f9; color: #1e293b; border: 1px solid #cbd5e1; font-weight: 600; border-radius: 6px; padding: 6px 12px;")
        btn_total.clicked.connect(lambda: self.spin_monto.setValue(self.saldo_actual))

        btn_mitad = QPushButton("Pagar la Mitad (50%)")
        btn_mitad.setStyleSheet("background: #f1f5f9; color: #1e293b; border: 1px solid #cbd5e1; font-weight: 600; border-radius: 6px; padding: 6px 12px;")
        btn_mitad.clicked.connect(lambda: self.spin_monto.setValue(round(self.saldo_actual / 2.0, 2)))

        quick_box.addWidget(btn_total)
        quick_box.addWidget(btn_mitad)
        quick_box.addStretch()
        layout.addLayout(quick_box)

        layout.addStretch()

        # Botones de Acción
        actions = QHBoxLayout()
        btn_cancel = QPushButton("Cancelar")
        btn_cancel.setStyleSheet("background: transparent; color: #64748b; padding: 9px 16px; border: none; font-weight: 600;")
        btn_cancel.clicked.connect(self.reject)

        btn_guardar = QPushButton("Confirmar Abono")
        btn_guardar.setStyleSheet("background: #2563eb; color: white; padding: 10px 20px; border-radius: 8px; font-weight: 600; font-size: 13.5px;")
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


class FiadosWindow(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Clientes y Cuentas por Cobrar")
        # Permitir maximizar, minimizar y redimensionar libremente
        self.setWindowFlags(Qt.Window | Qt.WindowTitleHint | Qt.WindowSystemMenuHint | Qt.WindowMinMaxButtonsHint | Qt.WindowCloseButtonHint)
        self.resize(1020, 640)
        self.setMinimumSize(780, 480)
        self.deudas = []
        self.cliente_seleccionado = None
        self.crear_interfaz()
        self.cargar_deudas()

    def crear_interfaz(self):
        self.setStyleSheet("""
            * { outline: none; }
            QWidget { font-family: 'Segoe UI', sans-serif; color: #0f172a; }
            QLabel { color: #0f172a; border: none; background: transparent; }
            QLabel:focus { border: none; outline: none; }
            QPushButton {
                background-color: #2563eb;
                color: #ffffff;
                border: none;
                border-radius: 7px;
                padding: 8px 16px;
                font-weight: 700;
                min-height: 22px;
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
            QLineEdit, QComboBox {
                background-color: #ffffff;
                border: 1.5px solid #cbd5e1;
                border-radius: 7px;
                padding: 7px 10px;
                color: #0f172a;
            }
            QLineEdit:focus, QComboBox:focus { border: 2px solid #2563eb; }
            QTableWidget {
                background-color: #ffffff;
                border: 1px solid #cbd5e1;
                border-radius: 8px;
                gridline-color: #f1f5f9;
                outline: none;
            }
            QTableWidget::item { border: none; outline: none; padding: 6px; }
            QTableWidget::item:focus { border: none; outline: none; }
            QTableWidget::item:selected { background-color: #dbeafe; color: #1e3a8a; border: none; outline: none; }
            QHeaderView::section {
                background-color: #f8fafc;
                color: #0f172a;
                font-weight: 700;
                border: none;
                border-bottom: 2px solid #cbd5e1;
                padding: 8px;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setSpacing(14)
        layout.setContentsMargins(22, 20, 22, 20)

        # Header limpio y minimalista
        header_layout = QHBoxLayout()
        title_box = QVBoxLayout()
        title_box.setSpacing(2)
        title_label = QLabel("Clientes y Cuentas por Cobrar")
        title_label.setStyleSheet("font-size: 20px; font-weight: 800; color: #0f172a; border: none; background: transparent;")
        sub_label = QLabel("Selecciona un cliente de la lista para registrar abonos o consultar su historial.")
        sub_label.setStyleSheet("font-size: 13px; color: #64748b; border: none; background: transparent;")
        title_box.addWidget(title_label)
        title_box.addWidget(sub_label)
        header_layout.addLayout(title_box)
        header_layout.addStretch()

        btn_refresh = QPushButton("🔄 Actualizar")
        btn_refresh.setStyleSheet("""
            QPushButton { background: #f8fafc; color: #334155; border: 1.5px solid #cbd5e1; font-weight: 700; padding: 7px 16px; border-radius: 7px; }
            QPushButton:hover { background: #e2e8f0; }
        """)
        btn_refresh.clicked.connect(self.cargar_deudas)
        header_layout.addWidget(btn_refresh)
        layout.addLayout(header_layout)

        # Resumen Minimalista (Barra limpia)
        kpi_bar = QFrame()
        kpi_bar.setObjectName("kpiBar")
        kpi_bar.setStyleSheet("QFrame#kpiBar { background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 10px; } QLabel { border: none; background: transparent; }")
        kpi_layout = QHBoxLayout(kpi_bar)
        kpi_layout.setContentsMargins(18, 12, 18, 12)
        kpi_layout.setSpacing(24)

        self.lbl_kpi_total = self._crear_kpi_item("TOTAL EN CRÉDITO", "Bs 0,00")
        self.lbl_kpi_pendiente = self._crear_kpi_item("SALDO PENDIENTE", "Bs 0,00", destacado=True)
        self.lbl_kpi_cobrado = self._crear_kpi_item("TOTAL RECUPERADO", "Bs 0,00")

        kpi_layout.addLayout(self.lbl_kpi_total)
        kpi_layout.addWidget(self._crear_separador())
        kpi_layout.addLayout(self.lbl_kpi_pendiente)
        kpi_layout.addWidget(self._crear_separador())
        kpi_layout.addLayout(self.lbl_kpi_cobrado)
        kpi_layout.addStretch()

        layout.addWidget(kpi_bar)

        # Buscador y Filtros
        search_layout = QHBoxLayout()
        search_layout.setSpacing(10)
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Buscar por nombre de cliente o número de factura...")
        self.search_input.setStyleSheet("padding: 8px 12px; font-size: 13.5px; border: 1px solid #cbd5e1; border-radius: 8px; background: white;")
        self.search_input.textChanged.connect(self.filtrar_tabla)
        search_layout.addWidget(self.search_input)

        self.btn_pendientes = QPushButton("Pendientes")
        self.btn_pendientes.setCheckable(True)
        self.btn_pendientes.setChecked(True)
        self.btn_pendientes.clicked.connect(lambda: self._set_filtro("pendientes"))

        self.btn_todos = QPushButton("Todos")
        self.btn_todos.setCheckable(True)
        self.btn_todos.clicked.connect(lambda: self._set_filtro("todos"))

        self.filtro_estado = "pendientes"
        self._actualizar_estilo_filtros()

        search_layout.addWidget(self.btn_pendientes)
        search_layout.addWidget(self.btn_todos)
        layout.addLayout(search_layout)

        # Tabla Minimalista
        self.tabla = QTableWidget()
        self.tabla.verticalHeader().setVisible(False)
        self.tabla.setColumnCount(7)
        self.tabla.setHorizontalHeaderLabels([
            "ID",
            "Cliente",
            "Teléfono",
            "Factura",
            "Total Venta",
            "Saldo Pendiente",
            "Estado",
        ])
        self.tabla.setFocusPolicy(Qt.NoFocus)
        self.tabla.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tabla.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.tabla.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.tabla.horizontalHeader().setSectionResizeMode(6, QHeaderView.ResizeToContents)
        self.tabla.setSelectionBehavior(QTableWidget.SelectRows)
        self.tabla.setSelectionMode(QTableWidget.SingleSelection)
        self.tabla.setEditTriggers(QTableWidget.NoEditTriggers)
        self.tabla.itemSelectionChanged.connect(self._on_seleccion_cambiada)
        self.tabla.doubleClicked.connect(self.registrar_abono_seleccionado)
        layout.addWidget(self.tabla)

        # Barra Inferior de Acción y Selección
        self.bottom_bar = QFrame()
        self.bottom_bar.setObjectName("bottomBar")
        self.bottom_bar.setStyleSheet("QFrame#bottomBar { background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 10px; padding: 4px; } QLabel { border: none; background: transparent; }")
        b_layout = QHBoxLayout(self.bottom_bar)
        b_layout.setContentsMargins(14, 10, 14, 10)
        b_layout.setSpacing(12)

        self.lbl_seleccion_info = QLabel("<i>Selecciona una fila de la tabla para gestionar el cobro</i>")
        self.lbl_seleccion_info.setStyleSheet("color: #64748b; font-size: 13.5px; border: none; background: transparent;")
        b_layout.addWidget(self.lbl_seleccion_info)
        b_layout.addStretch()

        self.btn_historial = QPushButton("📋 Ver Historial")
        self.btn_historial.setStyleSheet("""
            QPushButton {
                background: #f8fafc;
                color: #1e293b;
                border: 1.5px solid #cbd5e1;
                padding: 8px 16px;
                border-radius: 8px;
                font-weight: 700;
            }
            QPushButton:hover:!disabled { background: #e2e8f0; }
            QPushButton:disabled { color: #94a3b8; border-color: #e2e8f0; background: #f8fafc; }
        """)
        self.btn_historial.setEnabled(False)
        self.btn_historial.clicked.connect(self.ver_historial_abonos)
        b_layout.addWidget(self.btn_historial)

        self.btn_abonar = QPushButton("💵 Cobrar / Registrar Abono")
        self.btn_abonar.setStyleSheet("""
            QPushButton {
                background: #2563eb;
                color: white;
                font-weight: 800;
                padding: 8px 22px;
                border-radius: 8px;
                font-size: 13.5px;
                border: none;
            }
            QPushButton:hover:!disabled { background: #1d4ed8; }
            QPushButton:disabled { background: #cbd5e1; color: #64748b; }
        """)
        self.btn_abonar.setEnabled(False)
        self.btn_abonar.clicked.connect(self.registrar_abono_seleccionado)
        b_layout.addWidget(self.btn_abonar)

        layout.addWidget(self.bottom_bar)

    def _crear_kpi_item(self, title, default_val, destacado=False):
        vbox = QVBoxLayout()
        vbox.setSpacing(2)
        lbl_t = QLabel(title)
        lbl_t.setStyleSheet("font-size: 11px; font-weight: 600; color: #64748b; border: none; background: transparent;")
        lbl_v = QLabel(default_val)
        lbl_v.setStyleSheet("font-size: 16px; font-weight: 700; color: #0f172a; border: none; background: transparent;" if not destacado else "font-size: 17px; font-weight: 800; color: #2563eb; border: none; background: transparent;")
        vbox.addWidget(lbl_t)
        vbox.addWidget(lbl_v)
        vbox.val_label = lbl_v
        return vbox

    def _crear_separador(self):
        sep = QFrame()
        sep.setFrameShape(QFrame.VLine)
        sep.setFrameShadow(QFrame.Sunken)
        sep.setStyleSheet("color: #e2e8f0;")
        return sep

    def _set_filtro(self, filtro):
        self.filtro_estado = filtro
        self._actualizar_estilo_filtros()
        self.filtrar_tabla()

    def _actualizar_estilo_filtros(self):
        if self.filtro_estado == "pendientes":
            self.btn_pendientes.setStyleSheet("background: #e2e8f0; color: #0f172a; font-weight: 600; padding: 7px 14px; border-radius: 8px; border: none;")
            self.btn_todos.setStyleSheet("background: transparent; color: #64748b; border: 1px solid #cbd5e1; padding: 7px 14px; border-radius: 8px;")
        else:
            self.btn_todos.setStyleSheet("background: #e2e8f0; color: #0f172a; font-weight: 600; padding: 7px 14px; border-radius: 8px; border: none;")
            self.btn_pendientes.setStyleSheet("background: transparent; color: #64748b; border: 1px solid #cbd5e1; padding: 7px 14px; border-radius: 8px;")

    def cargar_deudas(self):
        self.deudas = get_credit_debts()
        total_fiado = sum(float(d["total_bs"] or 0) for d in self.deudas)
        total_pendiente = sum(float(d["saldo_bs"] or 0) for d in self.deudas)
        total_cobrado = total_fiado - total_pendiente

        self.lbl_kpi_total.val_label.setText(f"Bs {total_fiado:,.2f}")
        self.lbl_kpi_pendiente.val_label.setText(f"Bs {total_pendiente:,.2f}")
        self.lbl_kpi_cobrado.val_label.setText(f"Bs {total_cobrado:,.2f}")

        self.filtrar_tabla()

    def filtrar_tabla(self):
        query = self.search_input.text().strip().lower()
        self.tabla.setRowCount(0)

        for d in self.deudas:
            cliente = str(d["nombre"] or "")
            factura = str(d["numero_factura"] or "")
            telefono = str(d["telefono"] or "")
            saldo = float(d["saldo_bs"] or 0)
            total = float(d["total_bs"] or 0)
            estado = "Pagada" if saldo <= 0.001 else "Pendiente"

            if self.filtro_estado == "pendientes" and saldo <= 0.001:
                continue

            if query and query not in cliente.lower() and query not in factura.lower() and query not in telefono.lower():
                continue

            row = self.tabla.rowCount()
            self.tabla.insertRow(row)

            item_id = QTableWidgetItem(str(d["id"]))
            item_id.setData(Qt.UserRole, d["id"])
            item_cli = QTableWidgetItem(cliente)
            item_tel = QTableWidgetItem(telefono if telefono else "—")
            item_fac = QTableWidgetItem(f"#{factura}")
            item_tot = QTableWidgetItem(f"Bs {total:,.2f}")
            item_tot.setData(Qt.UserRole, total)

            item_sal = QTableWidgetItem(f"Bs {saldo:,.2f}")
            item_sal.setData(Qt.UserRole, saldo)
            item_est = QTableWidgetItem(estado)

            self.tabla.setItem(row, 0, item_id)
            self.tabla.setItem(row, 1, item_cli)
            self.tabla.setItem(row, 2, item_tel)
            self.tabla.setItem(row, 3, item_fac)
            self.tabla.setItem(row, 4, item_tot)
            self.tabla.setItem(row, 5, item_sal)
            self.tabla.setItem(row, 6, item_est)

        self._on_seleccion_cambiada()

    def _on_seleccion_cambiada(self):
        row = self.tabla.currentRow()
        if row >= 0:
            item_cli = self.tabla.item(row, 1)
            item_fac = self.tabla.item(row, 3)
            item_sal = self.tabla.item(row, 5)

            cliente = item_cli.text() if item_cli else ""
            factura = item_fac.text() if item_fac else ""
            saldo = float(item_sal.data(Qt.UserRole) or 0.0) if item_sal else 0.0

            if saldo > 0.001:
                self.lbl_seleccion_info.setText(
                    f"Seleccionado: <b>{cliente}</b> (Factura {factura}) · Saldo pendiente: <b>Bs {saldo:,.2f}</b>"
                )
                self.btn_abonar.setEnabled(True)
                self.btn_historial.setEnabled(True)
            else:
                self.lbl_seleccion_info.setText(
                    f"Seleccionado: <b>{cliente}</b> (Factura {factura}) · <i>Cuenta 100% Pagada</i>"
                )
                self.btn_abonar.setEnabled(False)
                self.btn_historial.setEnabled(True)
        else:
            self.lbl_seleccion_info.setText("<i>Haz clic en un cliente para ver opciones y cobrar</i>")
            self.btn_abonar.setEnabled(False)
            self.btn_historial.setEnabled(False)

    def registrar_abono_seleccionado(self):
        row = self.tabla.currentRow()
        if row < 0:
            QMessageBox.information(self, "Aviso", "Selecciona una cuenta por cobrar de la tabla.")
            return

        item_id = self.tabla.item(row, 0)
        item_cli = self.tabla.item(row, 1)
        item_fac = self.tabla.item(row, 3)
        item_tot = self.tabla.item(row, 4)
        item_sal = self.tabla.item(row, 5)

        deuda_id = int(item_id.data(Qt.UserRole) or item_id.text())
        cliente = item_cli.text()
        factura = item_fac.text().replace("#", "")
        saldo_actual = float(item_sal.data(Qt.UserRole) or 0.0)
        total_venta = float(item_tot.data(Qt.UserRole) or saldo_actual)

        if saldo_actual <= 0.001:
            QMessageBox.information(self, "Aviso", "Esta cuenta ya se encuentra 100% pagada.")
            return

        dialog = AbonoDialog(deuda_id, cliente, factura, saldo_actual, total_venta, self)
        if dialog.exec() == QDialog.Accepted:
            monto = dialog.monto_ingresado
            try:
                nuevo_saldo = register_debt_payment(deuda_id, monto)
                QMessageBox.information(
                    self,
                    "Abono Registrado",
                    f"Se registró el abono de Bs {monto:,.2f} exitosamente.\n\nSaldo restante: Bs {nuevo_saldo:,.2f}",
                )
                self.cargar_deudas()
                try:
                    from modules.sync.sync_service import is_configured, sync_now
                    import threading
                    if is_configured():
                        threading.Thread(target=sync_now, daemon=True).start()
                except Exception:
                    pass
            except Exception as e:
                QMessageBox.critical(self, "Error", str(e))

    def ver_historial_abonos(self):
        row = self.tabla.currentRow()
        if row < 0:
            QMessageBox.information(self, "Aviso", "Selecciona una cuenta para ver sus abonos.")
            return

        deuda_id = int(self.tabla.item(row, 0).data(Qt.UserRole) or self.tabla.item(row, 0).text())
        cliente = self.tabla.item(row, 1).text()
        factura = self.tabla.item(row, 3).text()

        pagos = get_debt_payments(deuda_id)
        if not pagos:
            QMessageBox.information(self, "Historial de Abonos", f"Aún no se han registrado abonos para la factura {factura} de {cliente}.")
            return

        msg = f"<b>Historial de Abonos - {cliente} (Factura {factura})</b><br><br>"
        for p in pagos:
            msg += f"• <b>Bs {float(p['monto_bs']):,.2f}</b> — {p['fecha']}<br>"

        QMessageBox.information(self, "Historial de Abonos", msg)
