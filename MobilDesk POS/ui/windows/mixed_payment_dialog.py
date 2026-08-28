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

        self.setWindowTitle("🔀 Pago Mixto / Fraccionado - MobilDesk POS")
        self.setFixedSize(540, 560)
        self.crear_interfaz()
        self.recalcular()

    def crear_interfaz(self):
        self.setStyleSheet("""
            QDialog {
                background-color: #ffffff;
                font-family: 'Segoe UI', sans-serif;
            }
            QLabel {
                color: #334155;
                font-size: 13px;
                font-weight: 600;
            }
            QLineEdit {
                background-color: #ffffff;
                border: 1.5px solid #cbd5e1;
                border-radius: 8px;
                padding: 8px 12px;
                font-size: 14px;
                font-weight: 700;
                color: #0f172a;
                min-height: 22px;
            }
            QLineEdit:focus {
                border: 2px solid #2563eb;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(22, 20, 22, 20)
        layout.setSpacing(12)

        # Header
        lbl_titulo = QLabel("🔀 REGISTRO DE PAGO MIXTO")
        lbl_titulo.setStyleSheet("font-size: 18px; font-weight: 800; color: #0f172a;")
        layout.addWidget(lbl_titulo)

        # Banner de Total a Pagar
        banner = QFrame()
        banner.setStyleSheet("""
            QFrame {
                background-color: #eff6ff;
                border: 1.5px solid #bfdbfe;
                border-radius: 10px;
            }
        """)
        b_layout = QHBoxLayout(banner)
        b_layout.setContentsMargins(14, 10, 14, 10)

        lbl_tot_text = QLabel("TOTAL A PAGAR:")
        lbl_tot_text.setStyleSheet("font-size: 14px; font-weight: 700; color: #1e3a8a;")

        self.lbl_tot_val = QLabel(f"Bs {self.total_bs:,.2f}  (${self.total_usd:,.2f})")
        self.lbl_tot_val.setStyleSheet("font-size: 16px; font-weight: 900; color: #1e3a8a;")

        b_layout.addWidget(lbl_tot_text)
        b_layout.addStretch()
        b_layout.addWidget(self.lbl_tot_val)
        layout.addWidget(banner)

        # Formulario de Métodos de Pago
        form_card = QFrame()
        form_card.setStyleSheet("""
            QFrame {
                background-color: #f8fafc;
                border: 1px solid #e2e8f0;
                border-radius: 10px;
            }
        """)
        f_layout = QGridLayout(form_card)
        f_layout.setContentsMargins(16, 14, 16, 14)
        f_layout.setHorizontalSpacing(12)
        f_layout.setVerticalSpacing(10)

        # 1. Divisas USD
        f_layout.addWidget(QLabel("💵 Divisas ($ USD):"), 0, 0)
        self.txt_usd = QLineEdit("0.00")
        self.lbl_usd_eq = QLabel("= Bs 0.00")
        self.lbl_usd_eq.setStyleSheet("color: #2563eb; font-weight: 700; font-size: 12.5px;")
        f_layout.addWidget(self.txt_usd, 0, 1)
        f_layout.addWidget(self.lbl_usd_eq, 0, 2)

        # 2. Efectivo Bs
        f_layout.addWidget(QLabel("💵 Efectivo (Bs):"), 1, 0)
        self.txt_bs = QLineEdit("0.00")
        f_layout.addWidget(self.txt_bs, 1, 1, 1, 2)

        # 3. Pago Móvil Bs
        f_layout.addWidget(QLabel("📲 Pago Móvil (Bs):"), 2, 0)
        self.txt_pago_movil = QLineEdit("0.00")
        f_layout.addWidget(self.txt_pago_movil, 2, 1, 1, 2)

        # 4. Tarjeta / Punto Bs
        f_layout.addWidget(QLabel("💳 Tarjeta / Punto (Bs):"), 3, 0)
        self.txt_tarjeta = QLineEdit("0.00")
        f_layout.addWidget(self.txt_tarjeta, 3, 1, 1, 2)

        # 5. Fiado / Crédito Bs
        f_layout.addWidget(QLabel("🤝 Fiado / Crédito (Bs):"), 4, 0)
        self.txt_fiado = QLineEdit("0.00")
        f_layout.addWidget(self.txt_fiado, 4, 1, 1, 2)

        layout.addWidget(form_card)

        # Conectar señales de cambio
        for txt in (self.txt_usd, self.txt_bs, self.txt_pago_movil, self.txt_tarjeta, self.txt_fiado):
            txt.textChanged.connect(self.recalcular)

        # Resumen dinámico y estado
        self.status_card = QFrame()
        self.status_card.setStyleSheet("""
            QFrame {
                background-color: #f1f5f9;
                border: 1.5px solid #cbd5e1;
                border-radius: 10px;
            }
        """)
        s_layout = QVBoxLayout(self.status_card)
        s_layout.setContentsMargins(14, 10, 14, 10)
        s_layout.setSpacing(6)

        row1 = QHBoxLayout()
        row1.addWidget(QLabel("Total Abonado:"))
        self.lbl_abonado = QLabel("Bs 0.00")
        self.lbl_abonado.setStyleSheet("font-weight: 800; font-size: 14px; color: #0f172a;")
        row1.addStretch()
        row1.addWidget(self.lbl_abonado)
        s_layout.addLayout(row1)

        row2 = QHBoxLayout()
        self.lbl_restante_titulo = QLabel("Resta por Pagar:")
        self.lbl_restante = QLabel(f"Bs {self.total_bs:,.2f}")
        self.lbl_restante.setStyleSheet("font-weight: 900; font-size: 15px; color: #dc2626;")
        row2.addWidget(self.lbl_restante_titulo)
        row2.addStretch()
        row2.addWidget(self.lbl_restante)
        s_layout.addLayout(row2)

        layout.addWidget(self.status_card)

        # Botones de Acción
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)

        self.btn_cancelar = QPushButton("Cancelar")
        self.btn_cancelar.setStyleSheet("""
            QPushButton {
                background-color: #f1f5f9;
                color: #334155;
                font-weight: 700;
                font-size: 14px;
                padding: 10px 18px;
                border-radius: 8px;
                border: 1.5px solid #cbd5e1;
            }
            QPushButton:hover { background-color: #e2e8f0; }
        """)
        self.btn_cancelar.clicked.connect(self.reject)

        self.btn_confirmar = QPushButton("✅ Confirmar Pago Mixto")
        self.btn_confirmar.setStyleSheet("""
            QPushButton {
                background-color: #16a34a;
                color: #ffffff;
                font-weight: 800;
                font-size: 14px;
                padding: 11px 22px;
                border-radius: 8px;
                border: none;
            }
            QPushButton:hover { background-color: #15803d; }
            QPushButton:disabled { background-color: #94a3b8; color: #e2e8f0; }
        """)
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
                self.lbl_restante_titulo.setText("🎉 Vuelto a Entregar:")
                self.lbl_restante.setText(f"Bs {vuelto_bs:,.2f}  (${vuelto_usd:,.2f})")
                self.lbl_restante.setStyleSheet("font-weight: 900; font-size: 15px; color: #16a34a;")
            else:
                self.lbl_restante_titulo.setText("✅ Estado:")
                self.lbl_restante.setText("¡PAGO EXACTO COMPLETO!")
                self.lbl_restante.setStyleSheet("font-weight: 900; font-size: 15px; color: #16a34a;")

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
            self.lbl_restante.setStyleSheet("font-weight: 900; font-size: 15px; color: #dc2626;")
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
