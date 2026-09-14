from PySide6.QtCore import Signal, Qt, QTimer
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
)
from modules.configuracion.bcv_service import fetch_and_apply_rate


class ExchangeRateWindow(QWidget):
    rate_changed = Signal()

    def __init__(self, usuario=None, parent=None):
        super().__init__(parent)
        self.usuario = usuario
        self.setWindowTitle("Tasa USD / Bs")
        self.resize(600, 480)
        self.setMinimumSize(480, 400)
        self.crear_interfaz()
        self.cargar_datos_actuales()

    def crear_interfaz(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 18, 24, 18)
        layout.setSpacing(14)

        # Header
        title = QLabel("Tasa Oficial USD / Bs")
        title.setObjectName("pageTitle")
        layout.addWidget(title)

        sub_info = QLabel("Configura el valor del dólar. Todos los precios de venta en Bs se recalculan solos.")
        sub_info.setWordWrap(True)
        sub_info.setObjectName("pageSubtitle")
        layout.addWidget(sub_info)

        # Banner de Estado Actual
        self.banner_actual = QFrame()
        self.banner_actual.setObjectName("banner")
        b_layout = QVBoxLayout(self.banner_actual)
        b_layout.setContentsMargins(18, 14, 18, 14)
        b_layout.setSpacing(6)

        lbl_tasa_tit = QLabel("TASA ACTUAL EN EL SISTEMA")
        lbl_tasa_tit.setObjectName("kpiLabel")
        self.lbl_tasa_val = QLabel("1 USD = Bs 0,00")
        self.lbl_tasa_val.setObjectName("kpiValue")

        b_layout.addWidget(lbl_tasa_tit)
        b_layout.addWidget(self.lbl_tasa_val)
        layout.addWidget(self.banner_actual)

        # Formulario
        form_frame = QFrame()
        form_frame.setObjectName("card")
        f_layout = QVBoxLayout(form_frame)
        f_layout.setContentsMargins(18, 18, 18, 18)
        f_layout.setSpacing(12)

        lbl_tasa = QLabel("NUEVA TASA DE CAMBIO (BS POR CADA $1 USD)")
        lbl_tasa.setObjectName("sectionLabel")
        f_layout.addWidget(lbl_tasa)
        tasa_box = QHBoxLayout()
        tasa_box.setSpacing(10)
        self.campo_tasa = QLineEdit()
        self.campo_tasa.setPlaceholderText("Ej: 832.49")
        self.campo_tasa.setStyleSheet("font-size: 16px; font-weight: 700;")
        self.campo_tasa.textChanged.connect(self._actualizar_equivalencia)
        tasa_box.addWidget(self.campo_tasa)

        btn_redondear = QPushButton("Redondear")
        btn_redondear.setProperty("variant", "ghost")
        btn_redondear.setToolTip("Redondear la tasa sin decimales")
        btn_redondear.clicked.connect(self._redondear_tasa)
        tasa_box.addWidget(btn_redondear)
        f_layout.addLayout(tasa_box)

        # Equivalencia en vivo (verificación rápida de lo escrito)
        self.lbl_preview = QLabel("")
        self.lbl_preview.setObjectName("pageSubtitle")
        self.lbl_preview.setWordWrap(True)
        f_layout.addWidget(self.lbl_preview)

        # Botón Obtener Tasa BCV: un solo clic la aplica de una vez
        bcv_box = QHBoxLayout()
        bcv_box.setSpacing(10)
        self.btn_bcv = QPushButton("Obtener Tasa del BCV")
        self.btn_bcv.setProperty("variant", "success")
        self.btn_bcv.setToolTip("Trae la tasa oficial y la aplica al instante, sin pasos extra")
        self.btn_bcv.clicked.connect(self._aplicar_bcv)
        bcv_box.addWidget(self.btn_bcv)
        bcv_info = QLabel("Un clic y listo: la obtiene y la deja aplicada")
        bcv_info.setObjectName("pageSubtitle")
        bcv_info.setWordWrap(True)
        bcv_box.addWidget(bcv_info)
        bcv_box.addStretch()
        f_layout.addLayout(bcv_box)

        layout.addWidget(form_frame)

        # Botón Guardar
        self.btn_guardar = QPushButton("Guardar Tasa")
        self.btn_guardar.setToolTip("Guardar la tasa escrita en el sistema")
        self.btn_guardar.clicked.connect(self.guardar_tasa)
        layout.addWidget(self.btn_guardar)

        layout.addStretch()

    def _aplicar_bcv(self):
        self.btn_bcv.setEnabled(False)
        self.btn_bcv.setText("Obteniendo...")
        QTimer.singleShot(100, self._ejecutar_bcv)

    def _ejecutar_bcv(self):
        try:
            user_id = self.usuario['id'] if self.usuario else 1
            ok, msg = fetch_and_apply_rate(user_id)
            if ok:
                self.cargar_datos_actuales()
                self.rate_changed.emit()
                self.btn_bcv.setText("¡Tasa aplicada!")
                QTimer.singleShot(2500, lambda: self.btn_bcv.setText("Obtener Tasa del BCV"))
            else:
                QMessageBox.warning(self, "BCV", msg)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo obtener la tasa: {e}")
        finally:
            self.btn_bcv.setEnabled(True)

    def cargar_datos_actuales(self):
        rate = get_current_exchange_rate()
        rate_val = float(rate) if rate is not None else 0.0

        self.lbl_tasa_val.setText(f"1 USD = Bs {rate_val:,.2f}" if rate_val > 0 else "Tasa: No configurada")

        if rate_val > 0:
            self.campo_tasa.setText(f"{rate_val:.2f}")

        self._actualizar_equivalencia()

    def _redondear_tasa(self):
        try:
            val = float(self.campo_tasa.text().strip().replace(",", "."))
            self.campo_tasa.setText(str(round(val)))
        except ValueError:
            pass

    def _actualizar_equivalencia(self):
        try:
            rate = float(self.campo_tasa.text().strip().replace(",", ".")) if self.campo_tasa.text().strip() else 0.0
        except ValueError:
            rate = 0.0

        if rate > 0:
            self.lbl_preview.setText(f"Con esta tasa: <b>$10.00 USD = Bs {10.0 * rate:,.2f}</b>")
        else:
            self.lbl_preview.setText("Escribe una tasa válida para ver su equivalencia.")

    def guardar_tasa(self):
        txt_tasa = self.campo_tasa.text().strip().replace(",", ".")
        if not txt_tasa:
            QMessageBox.information(self, "Aviso", "Escribe una tasa primero.")
            return
        try:
            rate = float(txt_tasa)
            if rate <= 0:
                raise ValueError("La tasa debe ser mayor que cero.")
            user_id = self.usuario['id'] if self.usuario else 1
            set_exchange_rate(rate, user_id)
        except ValueError as e:
            QMessageBox.warning(self, "Aviso", str(e))
            return

        self.cargar_datos_actuales()
        self.rate_changed.emit()

        QMessageBox.information(
            self,
            "Tasa Guardada",
            f"<b>Tasa aplicada:</b> 1 USD = Bs {rate:,.2f}"
            "<br><br><i>Los precios del punto de venta y las pantallas se actualizaron al instante.</i>",
        )
