from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QMessageBox,
    QLineEdit,
    QComboBox,
    QFormLayout,
    QHeaderView,
    QFrame,
    QTabWidget,
    QWidget,
    QInputDialog,
    QScrollArea,
)
from modules.caja.cash_service import (
    get_open_cash_register,
    open_cash_register,
    add_cash_movement,
    get_cash_movements,
    get_cash_register_summary,
    close_cash_register,
    get_cash_registers_history,
)


class CashWindow(QDialog):
    def __init__(self, user, parent=None):
        super().__init__(parent)
        self.user = user
        self.setWindowTitle("Control de Caja y Turnos")
        self.setWindowFlags(Qt.Window | Qt.WindowTitleHint | Qt.WindowSystemMenuHint | Qt.WindowMinMaxButtonsHint | Qt.WindowCloseButtonHint)
        self.resize(940, 580)
        self.setMinimumSize(720, 440)
        self.crear_interfaz()
        self.actualizar_vista()

    def crear_interfaz(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 18, 24, 18)
        layout.setSpacing(14)

        header = QHBoxLayout()
        head_box = QVBoxLayout()
        head_box.setSpacing(2)
        title = QLabel("CONTROL DE CAJA")
        title.setObjectName("pageTitle")
        head_sub = QLabel("Abre el turno, registra movimientos y cierra con el arqueo del día.")
        head_sub.setObjectName("pageSubtitle")
        head_box.addWidget(title)
        head_box.addWidget(head_sub)
        header.addLayout(head_box)
        header.addStretch()

        self.btn_refrescar = QPushButton("Actualizar")
        self.btn_refrescar.setProperty("variant", "ghost")
        self.btn_refrescar.setToolTip("Recargar el estado de la caja")
        self.btn_refrescar.clicked.connect(self.actualizar_vista)
        header.addWidget(self.btn_refrescar)
        layout.addLayout(header)

        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)

        # Tab 1: Turno Actual con ScrollArea
        self.tab_actual = QWidget()
        tab_act_layout = QVBoxLayout(self.tab_actual)
        tab_act_layout.setContentsMargins(0, 0, 0, 0)

        self.scroll_actual = QScrollArea()
        self.scroll_actual.setWidgetResizable(True)
        self.scroll_actual.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll_actual.setFrameShape(QFrame.NoFrame)
        self.container_actual = QWidget()
        self.layout_actual = QVBoxLayout(self.container_actual)
        self.layout_actual.setContentsMargins(0, 0, 0, 0)
        self.layout_actual.setSpacing(12)
        self.scroll_actual.setWidget(self.container_actual)

        tab_act_layout.addWidget(self.scroll_actual)
        self.tabs.addTab(self.tab_actual, "Caja Actual / Turno")

        # Tab 2: Historial de Cierres
        self.tab_historial = QWidget()
        self.layout_historial = QVBoxLayout(self.tab_historial)
        self.layout_historial.setContentsMargins(0, 0, 0, 0)
        self.layout_historial.setSpacing(12)
        self.tabs.addTab(self.tab_historial, "Historial de Cierres")

        self.crear_vista_historial()

    def limpiar_layout_actual(self):
        while self.layout_actual.count():
            item = self.layout_actual.takeAt(0)
            widget = item.widget()
            child_layout = item.layout()
            if widget:
                widget.deleteLater()
            elif child_layout:
                while child_layout.count():
                    child = child_layout.takeAt(0)
                    if child.widget():
                        child.widget().deleteLater()
                child_layout.deleteLater()

    def actualizar_vista(self):
        self.limpiar_layout_actual()
        caja = get_open_cash_register(self.user["id"] if self.user["role"] == "vendedor" else None)

        if not caja:
            self.mostrar_vista_apertura()
        else:
            self.mostrar_vista_caja_abierta(caja["id"])

        self.cargar_historial()

    def mostrar_vista_apertura(self):
        frame = QFrame()
        frame.setObjectName("card")
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(14)

        icono = QLabel("CAJA CERRADA")
        icono.setObjectName("pageTitle")
        layout.addWidget(icono)

        desc = QLabel(
            "No hay un turno de caja abierto actualmente para registrar ventas en efectivo o movimientos. "
            "Por favor, ingresa los montos iniciales de apertura para comenzar el turno."
        )
        desc.setWordWrap(True)
        desc.setObjectName("pageSubtitle")
        layout.addWidget(desc)

        form = QFormLayout()
        lbl_montos = QLabel("MONTOS INICIALES")
        lbl_montos.setObjectName("sectionLabel")
        form.addRow(lbl_montos)
        self.in_bs = QLineEdit("0.00")
        self.in_usd = QLineEdit("0.00")
        self.in_obs = QLineEdit()
        self.in_obs.setPlaceholderText("Observaciones o notas de apertura (opcional)")

        form.addRow("Fondo Inicial en Bs:", self.in_bs)
        form.addRow("Fondo Inicial en USD ($):", self.in_usd)
        form.addRow("Observaciones:", self.in_obs)
        layout.addLayout(form)

        btn_abrir = QPushButton("Abrir Turno de Caja")
        btn_abrir.setProperty("variant", "success")
        btn_abrir.setToolTip("Abrir un nuevo turno de caja")
        btn_abrir.clicked.connect(self.ejecutar_apertura)
        layout.addWidget(btn_abrir)

        self.layout_actual.addWidget(frame)
        self.layout_actual.addStretch()

    def ejecutar_apertura(self):
        try:
            m_bs = float(self.in_bs.text().replace(",", "."))
            m_usd = float(self.in_usd.text().replace(",", "."))
            open_cash_register(self.user["id"], m_bs, m_usd, self.in_obs.text().strip())
            QMessageBox.information(self, "Caja", "Turno de caja abierto correctamente.")
            self.actualizar_vista()
        except ValueError as error:
            QMessageBox.warning(self, "Caja", str(error))
        except Exception as error:
            QMessageBox.critical(self, "Error", f"No se pudo abrir la caja:\n{error}")

    def mostrar_vista_caja_abierta(self, caja_id):
        summary = get_cash_register_summary(caja_id)
        caja = summary["caja"]
        v_metodo = summary["ventas_por_metodo"]

        # Banner Superior
        banner = QFrame()
        banner.setObjectName("bannerDark")
        b_layout = QHBoxLayout(banner)
        b_layout.setContentsMargins(18, 14, 18, 14)
        b_layout.setSpacing(12)
        info_caja = QLabel(
            f"<b>TURNO ABIERTO # {caja['id']}</b> | Cajero: <b>{caja['usuario_nombre']}</b><br>"
            f"Apertura: {caja['fecha_apertura']}<br>"
            f"Fondo Inicial: Bs {float(caja['monto_inicial_bs']):,.2f} | USD ${float(caja['monto_inicial_usd']):,.2f}"
        )
        info_caja.setWordWrap(True)
        b_layout.addWidget(info_caja)
        b_layout.addStretch()

        btn_mov = QPushButton("Movimiento / Gasto")
        btn_mov.setProperty("variant", "soft")
        btn_mov.setToolTip("Registrar una entrada o gasto del turno")
        btn_mov.clicked.connect(lambda: self.dialogo_movimiento(caja_id))

        btn_cierre = QPushButton("Arqueo y Cierre de Caja")
        btn_cierre.setProperty("variant", "danger")
        btn_cierre.setToolTip("Contar el efectivo y cerrar el turno")
        btn_cierre.clicked.connect(lambda: self.dialogo_cierre(caja_id))

        b_layout.addWidget(btn_mov)
        b_layout.addWidget(btn_cierre)
        self.layout_actual.addWidget(banner)

        # Desglose en tarjetas
        grid = QHBoxLayout()
        grid.setSpacing(12)

        # Tarjeta 1: Ventas por método
        card_ventas = QFrame()
        card_ventas.setObjectName("card")
        cv_layout = QVBoxLayout(card_ventas)
        cv_layout.setContentsMargins(18, 18, 18, 18)
        cv_layout.setSpacing(8)
        lbl_ventas_titulo = QLabel("<b>VENTAS DEL TURNO</b>")
        lbl_ventas_titulo.setObjectName("sectionLabel")
        cv_layout.addWidget(lbl_ventas_titulo)
        cv_layout.addWidget(QLabel(f"Total Transacciones: <b>{summary['cantidad_ventas']}</b>"))
        cv_layout.addWidget(QLabel(f"Total Facturado: <b>Bs {summary['total_ventas_bs']:,.2f}</b> (${summary['total_ventas_usd']:,.2f})"))
        sep1 = QFrame()
        sep1.setFixedHeight(1)
        sep1.setStyleSheet("background-color: #E4E7EC; border: none;")
        cv_layout.addWidget(sep1)
        cv_layout.addWidget(QLabel(f"• Efectivo Bs: Bs {v_metodo['efectivo']:,.2f}"))
        cv_layout.addWidget(QLabel(f"• Divisas USD: ${v_metodo['divisas_usd']:,.2f} (Bs {v_metodo['divisas_bs']:,.2f})"))
        cv_layout.addWidget(QLabel(f"• Tarjeta: Bs {v_metodo['tarjeta']:,.2f}"))
        cv_layout.addWidget(QLabel(f"• Pago Móvil: Bs {v_metodo['pago_movil']:,.2f}"))
        cv_layout.addWidget(QLabel(f"• Fiados / Créditos: Bs {v_metodo['fiado']:,.2f}"))
        cv_layout.addStretch()
        grid.addWidget(card_ventas)

        # Tarjeta 2: Efectivo y Saldo Esperado en Caja
        card_esperado = QFrame()
        card_esperado.setObjectName("card")
        ce_layout = QVBoxLayout(card_esperado)
        ce_layout.setContentsMargins(18, 18, 18, 18)
        ce_layout.setSpacing(8)
        lbl_esp_titulo = QLabel("<b>EFECTIVO ESPERADO EN CAJA</b>")
        lbl_esp_titulo.setObjectName("sectionLabel")
        ce_layout.addWidget(lbl_esp_titulo)
        ce_layout.addWidget(QLabel(f"Entradas adicionales: Bs {summary['entradas_bs']:,.2f} | ${summary['entradas_usd']:,.2f}"))
        ce_layout.addWidget(QLabel(f"Salidas / Gastos: Bs {summary['salidas_bs']:,.2f} | ${summary['salidas_usd']:,.2f}"))
        sep2 = QFrame()
        sep2.setFixedHeight(1)
        sep2.setStyleSheet("background-color: #E4E7EC; border: none;")
        ce_layout.addWidget(sep2)

        lbl_esp_bs = QLabel(f"Esperado en Bs:<br><b style='font-size:18px;'>Bs {summary['esperado_bs']:,.2f}</b>")
        lbl_esp_usd = QLabel(f"Esperado en USD:<br><b style='font-size:18px;'>${summary['esperado_usd']:,.2f}</b>")
        ce_layout.addWidget(lbl_esp_bs)
        ce_layout.addWidget(lbl_esp_usd)
        ce_layout.addStretch()
        grid.addWidget(card_esperado)

        self.layout_actual.addLayout(grid)

        # Tabla de Movimientos del turno
        lbl_mov_titulo = QLabel("<b>Movimientos y Gastos del Turno Actual:</b>")
        lbl_mov_titulo.setObjectName("sectionLabel")
        self.layout_actual.addWidget(lbl_mov_titulo)
        tabla_mov = QTableWidget()
        tabla_mov.verticalHeader().setVisible(False)
        tabla_mov.setColumnCount(5)
        tabla_mov.setHorizontalHeaderLabels(["Fecha", "Tipo", "Moneda", "Monto", "Motivo"])
        tabla_mov.setEditTriggers(QTableWidget.NoEditTriggers)
        tabla_mov.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        movs = summary["movements"]
        tabla_mov.setRowCount(len(movs))
        for r, m in enumerate(movs):
            tabla_mov.setItem(r, 0, QTableWidgetItem(str(m["fecha"])))
            tabla_mov.setItem(r, 1, QTableWidgetItem(m["tipo"].upper()))
            tabla_mov.setItem(r, 2, QTableWidgetItem(m["moneda"]))
            tabla_mov.setItem(r, 3, QTableWidgetItem(f"{float(m['monto']):,.2f}"))
            tabla_mov.setItem(r, 4, QTableWidgetItem(m["motivo"]))

        self.layout_actual.addWidget(tabla_mov)

    def dialogo_movimiento(self, caja_id):
        dialogo = QDialog(self)
        dialogo.setWindowTitle("Registrar Movimiento de Caja")
        dialogo.resize(420, 260)
        dialogo.setMinimumSize(380, 240)
        layout = QVBoxLayout(dialogo)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(14)
        lbl_sec = QLabel("DATOS DEL MOVIMIENTO")
        lbl_sec.setObjectName("sectionLabel")
        layout.addWidget(lbl_sec)
        form = QFormLayout()

        tipo = QComboBox()
        tipo.addItem("Gasto de Caja", "gasto")
        tipo.addItem("Salida de Efectivo / Retiro", "salida")
        tipo.addItem("Entrada de Efectivo", "entrada")

        moneda = QComboBox()
        moneda.addItem("Bolívares (Bs)", "Bs")
        moneda.addItem("Dólares ($ USD)", "USD")

        monto = QLineEdit()
        monto.setPlaceholderText("0.00")
        motivo = QLineEdit()
        motivo.setPlaceholderText("Ej: Pago de flete, compra de bolsas, etc.")

        form.addRow("Tipo:", tipo)
        form.addRow("Moneda:", moneda)
        form.addRow("Monto:", monto)
        form.addRow("Motivo / Concepto:", motivo)
        layout.addLayout(form)

        btn_guardar = QPushButton("Guardar Movimiento")
        btn_guardar.setToolTip("Guardar el movimiento en el turno actual")
        btn_guardar.clicked.connect(lambda: self.guardar_movimiento(dialogo, caja_id, tipo.currentData(), moneda.currentData(), monto.text(), motivo.text()))
        layout.addWidget(btn_guardar)
        dialogo.exec()

    def guardar_movimiento(self, dialogo, caja_id, tipo, moneda, monto_txt, motivo_txt):
        try:
            m = float(monto_txt.replace(",", "."))
            add_cash_movement(caja_id, self.user["id"], tipo, moneda, m, motivo_txt)
            QMessageBox.information(self, "Caja", "Movimiento registrado correctamente.")
            dialogo.accept()
            self.actualizar_vista()
        except ValueError as error:
            QMessageBox.warning(self, "Caja", str(error))
        except Exception as error:
            QMessageBox.critical(self, "Error", str(error))

    def dialogo_cierre(self, caja_id):
        summary = get_cash_register_summary(caja_id)
        esp_bs = summary["esperado_bs"]
        esp_usd = summary["esperado_usd"]

        dialogo = QDialog(self)
        dialogo.setWindowTitle("Arqueo y Cierre de Caja")
        dialogo.resize(480, 420)
        dialogo.setMinimumSize(420, 360)
        layout = QVBoxLayout(dialogo)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(14)

        info = QLabel(
            f"<h3>ARQUEO DE CAJA</h3>"
            f"<p><b>Esperado en Bolívares:</b> Bs {esp_bs:,.2f}<br>"
            f"<b>Esperado en Dólares:</b> USD ${esp_usd:,.2f}</p>"
            f"<p style='color:#6B7280;'>Ingresa el monto de dinero físico contado en la gaveta:</p>"
        )
        layout.addWidget(info)

        lbl_conteo = QLabel("EFECTIVO CONTADO")
        lbl_conteo.setObjectName("sectionLabel")
        layout.addWidget(lbl_conteo)

        form = QFormLayout()
        in_real_bs = QLineEdit(f"{esp_bs:.2f}")
        in_real_usd = QLineEdit(f"{esp_usd:.2f}")
        in_obs = QLineEdit()
        in_obs.setPlaceholderText("Observaciones o justificación de diferencias")

        lbl_dif_bs = QLabel("Diferencia Bs: 0.00")
        lbl_dif_bs.setObjectName("money")
        lbl_dif_usd = QLabel("Diferencia USD: $0.00")
        lbl_dif_usd.setObjectName("money")

        def recalcular():
            try:
                r_bs = float((in_real_bs.text().strip() or "0").replace(",", "."))
                r_usd = float((in_real_usd.text().strip() or "0").replace(",", "."))
                d_bs = r_bs - esp_bs
                d_usd = r_usd - esp_usd

                color_bs = "#16A34A" if d_bs >= 0 else "#DC2626"
                color_usd = "#16A34A" if d_usd >= 0 else "#DC2626"

                lbl_dif_bs.setText(f"Diferencia Bs: {'+' if d_bs > 0 else ''}{d_bs:,.2f} ({'Sobrante' if d_bs > 0 else 'Faltante' if d_bs < 0 else 'Exacto'})")
                lbl_dif_bs.setStyleSheet(f"color: {color_bs}; font-weight: bold;")

                lbl_dif_usd.setText(f"Diferencia USD: {'+' if d_usd > 0 else ''}${d_usd:,.2f} ({'Sobrante' if d_usd > 0 else 'Faltante' if d_usd < 0 else 'Exacto'})")
                lbl_dif_usd.setStyleSheet(f"color: {color_usd}; font-weight: bold;")
            except ValueError:
                pass

        in_real_bs.textChanged.connect(recalcular)
        in_real_usd.textChanged.connect(recalcular)
        recalcular()

        form.addRow("Efectivo Contado en Bs:", in_real_bs)
        form.addRow("", lbl_dif_bs)
        form.addRow("Efectivo Contado en USD:", in_real_usd)
        form.addRow("", lbl_dif_usd)
        form.addRow("Observaciones:", in_obs)
        layout.addLayout(form)

        btn_confirmar = QPushButton("Confirmar Cierre de Caja")
        btn_confirmar.setProperty("variant", "danger")
        btn_confirmar.setToolTip("Cerrar el turno con los montos contados")
        btn_confirmar.clicked.connect(lambda: self.ejecutar_cierre(dialogo, caja_id, in_real_bs.text(), in_real_usd.text(), in_obs.text()))
        layout.addWidget(btn_confirmar)
        dialogo.exec()

    def ejecutar_cierre(self, dialogo, caja_id, real_bs_txt, real_usd_txt, obs_txt):
        try:
            r_bs = float(real_bs_txt.replace(",", "."))
            r_usd = float(real_usd_txt.replace(",", "."))
            resultado = close_cash_register(caja_id, r_bs, r_usd, obs_txt)
            QMessageBox.information(
                self,
                "Caja Cerrada",
                f"Turno de caja cerrado exitosamente.\n\n"
                f"Total Bs Contado: Bs {resultado['monto_final_bs']:,.2f} (Dif: Bs {resultado['diferencia_bs']:,.2f})\n"
                f"Total USD Contado: USD ${resultado['monto_final_usd']:,.2f} (Dif: USD ${resultado['diferencia_usd']:,.2f})"
            )
            dialogo.accept()
            self.actualizar_vista()
        except ValueError as error:
            QMessageBox.warning(self, "Caja", str(error))
        except Exception as error:
            QMessageBox.critical(self, "Error", str(error))

    def crear_vista_historial(self):
        self.tabla_historial = QTableWidget()
        self.tabla_historial.verticalHeader().setVisible(False)
        self.tabla_historial.setColumnCount(9)
        self.tabla_historial.setHorizontalHeaderLabels([
            "ID", "Cajero", "Apertura", "Cierre", "Inicial Bs", "Final Bs", "Dif Bs", "Final USD", "Dif USD"
        ])
        self.tabla_historial.setEditTriggers(QTableWidget.NoEditTriggers)
        self.tabla_historial.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.layout_historial.addWidget(self.tabla_historial)

    def cargar_historial(self):
        registros = get_cash_registers_history()
        self.tabla_historial.setRowCount(len(registros))
        for r, reg in enumerate(registros):
            final_bs = f"Bs {float(reg['monto_final_bs']):,.2f}" if reg["monto_final_bs"] is not None else "En curso"
            dif_bs = f"Bs {float(reg['diferencia_bs']):,.2f}" if reg["diferencia_bs"] is not None else ""
            final_usd = f"${float(reg['monto_final_usd']):,.2f}" if reg["monto_final_usd"] is not None else "En curso"
            dif_usd = f"${float(reg['diferencia_usd']):,.2f}" if reg["diferencia_usd"] is not None else ""

            valores = [
                reg["id"],
                reg["usuario_nombre"],
                reg["fecha_apertura"],
                reg["fecha_cierre"] or "Abierta",
                f"Bs {float(reg['monto_inicial_bs']):,.2f}",
                final_bs,
                dif_bs,
                final_usd,
                dif_usd,
            ]
            for c, val in enumerate(valores):
                item = QTableWidgetItem(str(val))
                if c in (0, 4, 5, 6, 7, 8):
                    item.setTextAlignment(Qt.AlignCenter)
                self.tabla_historial.setItem(r, c, item)
