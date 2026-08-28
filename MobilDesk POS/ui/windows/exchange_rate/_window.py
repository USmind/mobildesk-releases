from PySide6.QtCore import Signal, Qt
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QMessageBox,
    QFrame,
)
from modules.configuracion.exchange_rate_service import (
    get_current_exchange_rate,
    set_exchange_rate,
    get_profit_percentage,
    set_profit_percentage,
)


class ExchangeRateWindow(QWidget):
    rate_changed = Signal()

    def __init__(self, usuario=None, parent=None):
        super().__init__(parent)
        self.usuario = usuario
        self.setWindowTitle("Tasa USD / Bs y Margen de Ganancia")
        self.resize(600, 520)
        self.setMinimumSize(480, 420)
        self.crear_interfaz()
        self.cargar_datos_actuales()

    def crear_interfaz(self):
        self.setStyleSheet("""
            QWidget { font-family: 'Segoe UI', sans-serif; color: #0f172a; }
            QLabel { color: #0f172a; border: none; background: transparent; }
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
            QLineEdit {
                background-color: #ffffff;
                border: 1.5px solid #cbd5e1;
                border-radius: 7px;
                padding: 7px 10px;
                color: #0f172a;
            }
            QLineEdit:focus { border: 2px solid #2563eb; }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 24, 28, 24)
        layout.setSpacing(14)

        # Header
        title = QLabel("💲 Tasa Oficial USD / Bs y Margen")
        title.setStyleSheet("font-size: 22px; font-weight: 800; color: #0f172a;")
        layout.addWidget(title)

        sub_info = QLabel("Configura el valor del dólar y tu margen de ganancia estándar. Todos los precios de venta en Bs y $ se recalculan solos.")
        sub_info.setWordWrap(True)
        sub_info.setStyleSheet("color: #64748b; font-size: 13px;")
        layout.addWidget(sub_info)

        # Banner de Estado Actual
        self.banner_actual = QFrame()
        self.banner_actual.setStyleSheet(
            "background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #1e3a8a, stop:1 #2563eb); "
            "border-radius: 12px; padding: 14px;"
        )
        b_layout = QVBoxLayout(self.banner_actual)
        b_layout.setContentsMargins(14, 10, 14, 10)
        b_layout.setSpacing(4)

        lbl_tasa_tit = QLabel("TASA ACTUAL EN EL SISTEMA")
        lbl_tasa_tit.setStyleSheet("color: #93c5fd; font-size: 11px; font-weight: bold; letter-spacing: 0.5px;")
        self.lbl_tasa_val = QLabel("1 USD = Bs 0,00")
        self.lbl_tasa_val.setStyleSheet("color: white; font-size: 22px; font-weight: 900;")

        self.lbl_margen_val = QLabel("Margen estándar: 30%")
        self.lbl_margen_val.setStyleSheet("color: #e0f2fe; font-size: 13px; font-weight: 600;")

        b_layout.addWidget(lbl_tasa_tit)
        b_layout.addWidget(self.lbl_tasa_val)
        b_layout.addWidget(self.lbl_margen_val)
        layout.addWidget(self.banner_actual)

        # Formulario Simplificado
        form_frame = QFrame()
        form_frame.setObjectName("formCard")
        form_frame.setStyleSheet("""
            QFrame#formCard {
                background-color: #ffffff;
                border: 1px solid #e2e8f0;
                border-radius: 12px;
            }
        """)
        f_layout = QVBoxLayout(form_frame)
        f_layout.setContentsMargins(18, 16, 18, 16)
        f_layout.setSpacing(12)

        # 1. Campo Tasa
        f_layout.addWidget(QLabel("<b>1. Nueva Tasa de Cambio (Bs por cada $1 USD):</b>"))
        tasa_box = QHBoxLayout()
        self.campo_tasa = QLineEdit()
        self.campo_tasa.setPlaceholderText("Ej: 763.50")
        self.campo_tasa.setStyleSheet("padding: 9px 12px; font-size: 16px; font-weight: bold; border: 1px solid #cbd5e1; border-radius: 8px;")
        self.campo_tasa.textChanged.connect(self._actualizar_simulacion)
        tasa_box.addWidget(self.campo_tasa)

        btn_redondear = QPushButton("Redondear")
        btn_redondear.setStyleSheet("""
            QPushButton { background: #f1f5f9; color: #334155; font-weight: 600; padding: 8px 12px; border-radius: 6px; border: 1px solid #cbd5e1; }
            QPushButton:hover { background: #e2e8f0; }
        """)
        btn_redondear.clicked.connect(self._redondear_tasa)
        tasa_box.addWidget(btn_redondear)
        f_layout.addLayout(tasa_box)

        # 2. Campo Margen
        f_layout.addWidget(QLabel("<b>2. Margen de Ganancia (% sobre costo):</b>"))
        margen_box = QHBoxLayout()
        self.campo_ganancia = QLineEdit()
        self.campo_ganancia.setPlaceholderText("Ej: 30")
        self.campo_ganancia.setStyleSheet("padding: 9px 12px; font-size: 16px; font-weight: bold; border: 1px solid #cbd5e1; border-radius: 8px;")
        self.campo_ganancia.textChanged.connect(self._actualizar_simulacion)
        margen_box.addWidget(self.campo_ganancia)

        # Presets rápidos de margen
        for pct in [20, 30, 40, 50]:
            btn_pct = QPushButton(f"{pct}%")
            btn_pct.setStyleSheet("""
                QPushButton { background: #eff6ff; color: #1e40af; font-weight: 700; padding: 8px 10px; border-radius: 6px; border: 1px solid #bfdbfe; }
                QPushButton:hover { background: #dbeafe; }
            """)
            btn_pct.clicked.connect(lambda _, p=pct: self.campo_ganancia.setText(str(p)))
            margen_box.addWidget(btn_pct)

        f_layout.addLayout(margen_box)

        # 3. Vista Previa / Simulador en Vivo
        self.lbl_preview = QLabel("💡 <b>Ejemplo:</b> Costo $10.00 USD ➔ Venta $13.00 USD (Bs 0,00)")
        self.lbl_preview.setStyleSheet("background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px; color: #0f172a; padding: 10px; font-size: 12.5px;")
        f_layout.addWidget(self.lbl_preview)

        layout.addWidget(form_frame)

        # Botón Guardar
        self.btn_guardar_todo = QPushButton("💾 Guardar y Aplicar Cambios")
        self.btn_guardar_todo.setStyleSheet("""
            QPushButton {
                background: #2563eb;
                color: white;
                font-size: 15px;
                font-weight: 700;
                padding: 12px;
                border-radius: 10px;
                border: none;
            }
            QPushButton:hover { background: #1d4ed8; }
        """)
        self.btn_guardar_todo.clicked.connect(self.guardar_todo)
        layout.addWidget(self.btn_guardar_todo)

        layout.addStretch()

    def cargar_datos_actuales(self):
        rate = get_current_exchange_rate()
        rate_val = float(rate) if rate is not None else 0.0
        profit = get_profit_percentage()

        self.lbl_tasa_val.setText(f"1 USD = Bs {rate_val:,.2f}" if rate_val > 0 else "Tasa: No configurada")
        self.lbl_margen_val.setText(f"Margen estándar: {profit:g}% de ganancia")

        if rate_val > 0:
            self.campo_tasa.setText(f"{rate_val:.2f}")
        self.campo_ganancia.setText(f"{profit:g}")

        self._actualizar_simulacion()

    def _redondear_tasa(self):
        try:
            val = float(self.campo_tasa.text().strip().replace(",", "."))
            self.campo_tasa.setText(str(round(val)))
        except ValueError:
            pass

    def _actualizar_simulacion(self):
        try:
            rate = float(self.campo_tasa.text().strip().replace(",", ".")) if self.campo_tasa.text().strip() else 0.0
        except ValueError:
            rate = 0.0

        try:
            profit = float(self.campo_ganancia.text().strip().replace(",", ".")) if self.campo_ganancia.text().strip() else 30.0
        except ValueError:
            profit = 30.0

        costo_ejemplo = 10.0
        venta_usd = costo_ejemplo * (1 + (profit / 100.0))
        venta_bs = venta_usd * rate

        self.lbl_preview.setText(
            f"💡 <b>Ejemplo en vivo:</b> Producto con costo de <b>$10.00 USD</b> (+{profit:g}%) ➔ "
            f"Precio de venta: <b>${venta_usd:,.2f} USD</b> (<b>Bs {venta_bs:,.2f}</b>)"
        )

    def guardar_todo(self):
        cambios = []
        tasa_modificada = False
        margen_modificado = False

        # Validar y guardar tasa
        txt_tasa = self.campo_tasa.text().strip().replace(",", ".")
        if txt_tasa:
            try:
                rate = float(txt_tasa)
                if rate <= 0:
                    raise ValueError("La tasa debe ser mayor que cero.")
                user_id = self.usuario['id'] if self.usuario else 1
                set_exchange_rate(rate, user_id)
                tasa_modificada = True
                cambios.append(f"• Tasa: 1 USD = Bs {rate:,.2f}")
            except ValueError as e:
                QMessageBox.warning(self, "Aviso", str(e))
                return

        # Validar y guardar margen
        txt_margen = self.campo_ganancia.text().strip().replace(",", ".")
        if txt_margen:
            try:
                gain = float(txt_margen)
                if gain < 0:
                    raise ValueError("El margen no puede ser negativo.")
                set_profit_percentage(gain)
                margen_modificado = True
                cambios.append(f"• Margen de ganancia: {gain:g}%")
            except ValueError as e:
                QMessageBox.warning(self, "Aviso", str(e))
                return

        if not cambios:
            QMessageBox.information(self, "Aviso", "No se ingresaron cambios.")
            return

        self.cargar_datos_actuales()
        self.rate_changed.emit()

        QMessageBox.information(
            self,
            "Configuración Guardada",
            "✅ <b>Cambios aplicados correctamente:</b><br><br>"
            + "<br>".join(cambios)
            + "<br><br><i>Los precios del punto de venta y las pantallas se actualizaron al instante.</i>",
        )
