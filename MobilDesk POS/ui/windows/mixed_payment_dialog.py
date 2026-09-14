from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QFrame,
    QMessageBox,
)


class MixedPaymentDialog(QDialog):
    def __init__(self, total_bs, total_usd, tasa, parent=None):
        super().__init__(parent)
        self.total_bs = float(total_bs)
        self.total_usd = float(total_usd)
        self.tasa = float(tasa)
        self.datos_resultado = None

        self.setWindowTitle("Pago Mixto / Fraccionado - MobilDesk POS")
        self.setFixedSize(540, 560)
        self.crear_interfaz()
        self.recalcular()

    def crear_interfaz(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 18, 24, 18)
        layout.setSpacing(14)

        # Header
        lbl_titulo = QLabel("REGISTRO DE PAGO MIXTO")
        lbl_titulo.setObjectName("pageTitle")
        layout.addWidget(lbl_titulo)
        lbl_sub = QLabel("Combina efectivo, divisas y otros métodos hasta cubrir el total.")
        lbl_sub.setObjectName("pageSubtitle")
        layout.addWidget(lbl_sub)

        # Banner de Total a Pagar
        banner = QFrame()
        banner.setObjectName("banner")
        b_layout = QHBoxLayout(banner)
        b_layout.setContentsMargins(18, 14, 18, 14)
        b_layout.setSpacing(12)

        lbl_tot_text = QLabel("TOTAL A PAGAR:")

        self.lbl_tot_val = QLabel(f"Bs {self.total_bs:,.2f}  (${self.total_usd:,.2f})")
        self.lbl_tot_val.setObjectName("money")

        b_layout.addWidget(lbl_tot_text)
        b_layout.addStretch()
        b_layout.addWidget(self.lbl_tot_val)
        layout.addWidget(banner)

        # Formulario de Métodos de Pago
        form_card = QFrame()
        form_card.setObjectName("card")
        f_layout = QGridLayout(form_card)
        f_layout.setContentsMargins(18, 18, 18, 18)
        f_layout.setHorizontalSpacing(12)
        f_layout.setVerticalSpacing(12)
        f_layout.setColumnStretch(1, 1)

        lbl_form = QLabel("DESGLOSE POR MÉTODO")
        lbl_form.setObjectName("sectionLabel")
        f_layout.addWidget(lbl_form, 0, 0, 1, 3)

        # 1. Divisas USD
        lbl_usd = QLabel("Divisas ($ USD):")
        lbl_usd.setObjectName("sectionLabel")
        f_layout.addWidget(lbl_usd, 1, 0)
        self.txt_usd = QLineEdit("0.00")
        self.lbl_usd_eq = QLabel("= Bs 0.00")
        self.lbl_usd_eq.setObjectName("pageSubtitle")
        f_layout.addWidget(self.txt_usd, 1, 1)
        f_layout.addWidget(self.lbl_usd_eq, 1, 2)

        # 2. Efectivo Bs
        lbl_bs = QLabel("Efectivo (Bs):")
        lbl_bs.setObjectName("sectionLabel")
        f_layout.addWidget(lbl_bs, 2, 0)
        self.txt_bs = QLineEdit("0.00")
        f_layout.addWidget(self.txt_bs, 2, 1, 1, 2)

        # 3. Pago Móvil Bs
        lbl_pm = QLabel("Pago Móvil (Bs):")
        lbl_pm.setObjectName("sectionLabel")
        f_layout.addWidget(lbl_pm, 3, 0)
        self.txt_pago_movil = QLineEdit("0.00")
        f_layout.addWidget(self.txt_pago_movil, 3, 1, 1, 2)

        # 4. Tarjeta / Punto Bs
        lbl_tar = QLabel("Tarjeta / Punto (Bs):")
        lbl_tar.setObjectName("sectionLabel")
        f_layout.addWidget(lbl_tar, 4, 0)
        self.txt_tarjeta = QLineEdit("0.00")
        f_layout.addWidget(self.txt_tarjeta, 4, 1, 1, 2)

        # 5. Fiado / Crédito Bs
        lbl_fiado = QLabel("Fiado / Crédito (Bs):")
        lbl_fiado.setObjectName("sectionLabel")
        f_layout.addWidget(lbl_fiado, 5, 0)
        self.txt_fiado = QLineEdit("0.00")
        f_layout.addWidget(self.txt_fiado, 5, 1, 1, 2)

        layout.addWidget(form_card)

        # Conectar señales de cambio
        for txt in (self.txt_usd, self.txt_bs, self.txt_pago_movil, self.txt_tarjeta, self.txt_fiado):
            txt.textChanged.connect(self.recalcular)

        # Resumen dinámico y estado
        self.status_card = QFrame()
        self.status_card.setObjectName("card")
        s_layout = QVBoxLayout(self.status_card)
        s_layout.setContentsMargins(18, 14, 18, 14)
        s_layout.setSpacing(8)

        row1 = QHBoxLayout()
        lbl_abonado_titulo = QLabel("Total Abonado:")
        lbl_abonado_titulo.setObjectName("sectionLabel")
        row1.addWidget(lbl_abonado_titulo)
        self.lbl_abonado = QLabel("Bs 0.00")
        self.lbl_abonado.setObjectName("money")
        row1.addStretch()
        row1.addWidget(self.lbl_abonado)
        s_layout.addLayout(row1)

        row2 = QHBoxLayout()
        self.lbl_restante_titulo = QLabel("Resta por Pagar:")
        self.lbl_restante_titulo.setObjectName("sectionLabel")
        self.lbl_restante = QLabel(f"Bs {self.total_bs:,.2f}")
        self.lbl_restante.setObjectName("money")
        row2.addWidget(self.lbl_restante_titulo)
        row2.addStretch()
        row2.addWidget(self.lbl_restante)
        s_layout.addLayout(row2)

        layout.addWidget(self.status_card)

        # Botones de Acción
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)

        self.btn_cancelar = QPushButton("Cancelar")
        self.btn_cancelar.setProperty("variant", "ghost")
        self.btn_cancelar.setToolTip("Cerrar sin guardar el pago")
        self.btn_cancelar.clicked.connect(self.reject)

        self.btn_confirmar = QPushButton("Confirmar Pago Mixto")
        self.btn_confirmar.setProperty("variant", "success")
        self.btn_confirmar.setToolTip("Guardar el desglose y volver a la venta")
        self.btn_confirmar.clicked.connect(self.validar_y_guardar)

        btn_layout.addWidget(self.btn_cancelar)
        btn_layout.addWidget(self.btn_confirmar)
        layout.addLayout(btn_layout)

    def _parse_val(self, line_edit):
        try:
            return max(0.0, float(line_edit.text().strip().replace(",", ".") or 0))
        except ValueError:
            return 0.0

    def recalcular(self):
        usd = self._parse_val(self.txt_usd)
        bs_efectivo = self._parse_val(self.txt_bs)
        pm = self._parse_val(self.txt_pago_movil)
        tarjeta = self._parse_val(self.txt_tarjeta)
        fiado = self._parse_val(self.txt_fiado)

        usd_en_bs = usd * self.tasa
        self.lbl_usd_eq.setText(f"= Bs {usd_en_bs:,.2f}")

        total_abonado = usd_en_bs + bs_efectivo + pm + tarjeta + fiado
        self.lbl_abonado.setText(f"Bs {total_abonado:,.2f}")

        diferencia = round(total_abonado - self.total_bs, 2)

        if diferencia >= 0:
            # Pago cubierto o con vuelto
            vuelto_bs = diferencia
            if vuelto_bs > 0:
                vuelto_usd = vuelto_bs / self.tasa if self.tasa > 0 else 0
                self.lbl_restante_titulo.setText("Vuelto a Entregar:")
                self.lbl_restante.setText(f"Bs {vuelto_bs:,.2f}  (${vuelto_usd:,.2f})")
                self.lbl_restante.setStyleSheet("font-weight: 900; font-size: 15px; color: #16A34A;")
            else:
                self.lbl_restante_titulo.setText("Estado:")
                self.lbl_restante.setText("¡PAGO EXACTO COMPLETO!")
                self.lbl_restante.setStyleSheet("font-weight: 900; font-size: 15px; color: #16A34A;")

            self.status_card.setStyleSheet("""
                QFrame {
                    background-color: #f0fdf4;
                    border: 1.5px solid #86efac;
                    border-radius: 10px;
                }
            """)
            self.btn_confirmar.setEnabled(True)
        else:
            # Falta dinero
            pendiente = abs(diferencia)
            self.lbl_restante_titulo.setText("Resta por Pagar:")
            self.lbl_restante.setText(f"Bs {pendiente:,.2f}")
            self.lbl_restante.setStyleSheet("font-weight: 900; font-size: 15px; color: #DC2626;")
            self.status_card.setStyleSheet("""
                QFrame {
                    background-color: #fef2f2;
                    border: 1.5px solid #fca5a5;
                    border-radius: 10px;
                }
            """)
            self.btn_confirmar.setEnabled(False)

    def validar_y_guardar(self):
        usd = self._parse_val(self.txt_usd)
        bs_efectivo = self._parse_val(self.txt_bs)
        pm = self._parse_val(self.txt_pago_movil)
        tarjeta = self._parse_val(self.txt_tarjeta)
        fiado = self._parse_val(self.txt_fiado)

        usd_en_bs = usd * self.tasa
        total_abonado = usd_en_bs + bs_efectivo + pm + tarjeta + fiado

        if total_abonado < self.total_bs:
            QMessageBox.warning(self, "Pago Incompleto", "El monto abonado no alcanza para cubrir el total de la venta.")
            return

        vuelto_bs = max(0.0, round(total_abonado - self.total_bs, 2))
        vuelto_usd = vuelto_bs / self.tasa if (self.tasa > 0 and vuelto_bs > 0) else 0.0

        self.datos_resultado = {
            "divisas_usd": usd,
            "divisas_bs": usd_en_bs,
            "efectivo_bs": bs_efectivo,
            "pago_movil_bs": pm,
            "tarjeta_bs": tarjeta,
            "fiado_bs": fiado,
            "total_abonado_bs": total_abonado,
            "vuelto_bs": vuelto_bs,
            "vuelto_usd": vuelto_usd,
        }
        self.accept()
