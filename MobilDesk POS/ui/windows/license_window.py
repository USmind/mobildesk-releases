from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QMessageBox,
    QFrame,
    QApplication
)
from PySide6.QtCore import Qt, Signal
from modules.licencia.license_service import (
    init_or_get_license_info,
    activate_system_license,
    republicar_licencia_actual
)


class LicenseWindow(QDialog):
    licencia_actualizada = Signal()

    def __init__(self, parent=None, obligatorio=False):
        super().__init__(parent)
        self.obligatorio = obligatorio
        self.setWindowTitle("Licencia y Activación del Sistema")
        self.setWindowFlags(Qt.Window | Qt.WindowTitleHint | Qt.WindowSystemMenuHint | Qt.WindowCloseButtonHint)
        self.resize(560, 420)
        self.setMinimumSize(500, 380)
        self.crear_interfaz()
        self.cargar_estado()

    def crear_interfaz(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(14)
        layout.setContentsMargins(24, 20, 24, 20)

        # Encabezado
        title = QLabel("LICENCIA Y ACTIVACIÓN")
        title.setObjectName("pageTitle")
        layout.addWidget(title)

        desc = QLabel("Gestione la activación de MobilDesk POS en esta computadora.")
        desc.setObjectName("pageSubtitle")
        layout.addWidget(desc)

        # Tarjeta de Estado
        self.card_estado = QFrame()
        self.card_estado.setObjectName("card")
        card_layout = QVBoxLayout(self.card_estado)
        card_layout.setContentsMargins(16, 12, 16, 12)
        card_layout.setSpacing(6)

        self.lbl_estado_titulo = QLabel("Estado:")
        self.lbl_estado_titulo.setObjectName("sectionLabel")
        card_layout.addWidget(self.lbl_estado_titulo)

        self.lbl_estado_valor = QLabel("Cargando...")
        self.lbl_estado_valor.setObjectName("money")
        card_layout.addWidget(self.lbl_estado_valor)

        self.lbl_expiracion = QLabel("")
        self.lbl_expiracion.setObjectName("pageSubtitle")
        card_layout.addWidget(self.lbl_expiracion)

        layout.addWidget(self.card_estado)

        # Código de la Máquina (Hardware ID)
        lbl_mid = QLabel("Código de esta Computadora (Machine ID):")
        lbl_mid.setObjectName("sectionLabel")
        layout.addWidget(lbl_mid)

        mid_layout = QHBoxLayout()
        self.txt_machine_id = QLineEdit()
        self.txt_machine_id.setReadOnly(True)
        self.txt_machine_id.setStyleSheet("font-family: monospace; font-weight: 700;")
        mid_layout.addWidget(self.txt_machine_id)

        btn_copiar = QPushButton("Copiar")
        btn_copiar.setProperty("variant", "ghost")
        btn_copiar.setToolTip("Copiar el código al portapapeles")
        btn_copiar.clicked.connect(self.copiar_machine_id)
        mid_layout.addWidget(btn_copiar)
        layout.addLayout(mid_layout)

        # Campo de Clave de Activación
        lbl_clave = QLabel("Clave de Activación (Serial):")
        lbl_clave.setObjectName("sectionLabel")
        layout.addWidget(lbl_clave)

        self.txt_clave = QLineEdit()
        self.txt_clave.setPlaceholderText("Ej: KP-A365-68BD1A-9F42A1")
        self.txt_clave.setStyleSheet("font-family: monospace;")
        layout.addWidget(self.txt_clave)

        # Botones de Acción
        actions = QHBoxLayout()
        if not self.obligatorio:
            btn_cerrar = QPushButton("Cerrar")
            btn_cerrar.setProperty("variant", "ghost")
            btn_cerrar.setToolTip("Cerrar esta ventana")
            btn_cerrar.clicked.connect(self.reject)
            actions.addWidget(btn_cerrar)

        actions.addStretch()

        btn_sync_lic = QPushButton("Sincronizar Licencia")
        btn_sync_lic.setProperty("variant", "soft")
        btn_sync_lic.setToolTip("Publicar la licencia para la app móvil")
        btn_sync_lic.clicked.connect(self.republicar_licencia)
        actions.addWidget(btn_sync_lic)

        btn_activar = QPushButton("Activar Licencia")
        btn_activar.setToolTip("Activar el sistema con la clave ingresada")
        btn_activar.clicked.connect(self.procesar_activacion)
        actions.addWidget(btn_activar)

        layout.addLayout(actions)

    def cargar_estado(self):
        info = init_or_get_license_info()
        self.txt_machine_id.setText(info["machine_id"])

        if info["estado"] == "vitalicio":
            self.lbl_estado_valor.setText(info["plan_nombre"])
            self.lbl_estado_valor.setStyleSheet("color: #16A34A;")
            self.lbl_expiracion.setText("Vigencia permanente e ilimitada.")
        elif info["estado"] == "reloj_invalido":
            self.lbl_estado_valor.setText(info["plan_nombre"])
            self.lbl_estado_valor.setStyleSheet("color: #DC2626;")
            self.lbl_expiracion.setText("La fecha del equipo es anterior a tu último uso. Corrígelas para continuar. Tus datos están intactos.")
        elif info["estado"] == "demo":
            self.lbl_estado_valor.setText(f"{info['plan_nombre']} ({info['dias_restantes']} días restantes)")
            self.lbl_estado_valor.setStyleSheet("color: #EA580C;")
            self.lbl_expiracion.setText(f"Válido hasta: {info['fecha_expiracion']}. Ingrese una clave para activar su plan.")
        elif info["estado"] == "activo":
            self.lbl_estado_valor.setText(f"{info['plan_nombre']} ({info['dias_restantes']} días restantes)")
            self.lbl_estado_valor.setStyleSheet("color: #2563EB;")
            self.lbl_expiracion.setText(f"Vence el: {info['fecha_expiracion']}")
        else:
            self.lbl_estado_valor.setText(info["plan_nombre"])
            self.lbl_estado_valor.setStyleSheet("color: #DC2626;")
            self.lbl_expiracion.setText("El período de servicio ha vencido. Ingrese una nueva clave de activación.")

    def copiar_machine_id(self):
        mid = self.txt_machine_id.text()
        if mid:
            QApplication.clipboard().setText(mid)
            QMessageBox.information(self, "Copiado", "Código de la computadora copiado al portapapeles.\n\nPuedes pegarlo en WhatsApp para enviárselo a tu proveedor.")

    def procesar_activacion(self):
        clave = self.txt_clave.text().strip()
        if not clave:
            QMessageBox.warning(self, "Aviso", "Por favor ingrese una clave de activación.")
            return

        ok, msg = activate_system_license(clave)
        if ok:
            QMessageBox.information(self, "¡Activación Exitosa!", msg)
            self.licencia_actualizada.emit()
            self.cargar_estado()
            self.txt_clave.clear()
            if self.obligatorio:
                self.accept()
        else:
            QMessageBox.critical(self, "Error de Activación", msg)

    def republicar_licencia(self):
        ok, msg = republicar_licencia_actual()
        if ok:
            QMessageBox.information(self, "Sincronizado", msg + "\n\nAhora sincroniza en tu móvil para que reciba la licencia.")
            self.licencia_actualizada.emit()
            self.cargar_estado()
        else:
            QMessageBox.warning(self, "Error", msg)
