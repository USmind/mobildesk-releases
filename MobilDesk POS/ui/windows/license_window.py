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
        layout.setSpacing(14)
        layout.setContentsMargins(24, 20, 24, 20)

        # Encabezado
        title = QLabel("🔑 LICENCIA Y ACTIVACIÓN")
        title.setStyleSheet("font-size: 19px; font-weight: 800; color: #1e293b; border: none;")
        layout.addWidget(title)

        desc = QLabel("Gestione la activación de MobilDesk POS en esta computadora.")
        desc.setStyleSheet("color: #64748b; font-size: 13.5px; border: none;")
        layout.addWidget(desc)

        # Tarjeta de Estado
        self.card_estado = QFrame()
        self.card_estado.setObjectName("estadoCard")
        self.card_estado.setStyleSheet("""
            QFrame#estadoCard {
                background-color: #f8fafc;
                border: 1px solid #e2e8f0;
                border-radius: 10px;
            }
            QFrame#estadoCard QLabel { border: none; background: transparent; }
        """)
        card_layout = QVBoxLayout(self.card_estado)
        card_layout.setSpacing(6)

        self.lbl_estado_titulo = QLabel("Estado:")
        self.lbl_estado_titulo.setStyleSheet("font-size: 12px; font-weight: 600; color: #64748b;")
        card_layout.addWidget(self.lbl_estado_titulo)

        self.lbl_estado_valor = QLabel("Cargando...")
        self.lbl_estado_valor.setStyleSheet("font-size: 16px; font-weight: 700; color: #2563eb;")
        card_layout.addWidget(self.lbl_estado_valor)

        self.lbl_expiracion = QLabel("")
        self.lbl_expiracion.setStyleSheet("font-size: 13px; color: #475569;")
        card_layout.addWidget(self.lbl_expiracion)

        layout.addWidget(self.card_estado)

        # Código de la Máquina (Hardware ID)
        lbl_mid = QLabel("Código de esta Computadora (Machine ID):")
        lbl_mid.setStyleSheet("font-weight: 600; font-size: 13px; color: #334155;")
        layout.addWidget(lbl_mid)

        mid_layout = QHBoxLayout()
        self.txt_machine_id = QLineEdit()
        self.txt_machine_id.setReadOnly(True)
        self.txt_machine_id.setStyleSheet("background: #f1f5f9; font-weight: 700; font-family: monospace; font-size: 14px; color: #0f172a; padding: 8px;")
        mid_layout.addWidget(self.txt_machine_id)

        btn_copiar = QPushButton("📋 Copiar")
        btn_copiar.setStyleSheet("background: #e2e8f0; color: #1e293b; font-weight: 600; padding: 8px 14px; border-radius: 7px;")
        btn_copiar.clicked.connect(self.copiar_machine_id)
        mid_layout.addWidget(btn_copiar)
        layout.addLayout(mid_layout)

        # Campo de Clave de Activación
        lbl_clave = QLabel("Clave de Activación (Serial):")
        lbl_clave.setStyleSheet("font-weight: 600; font-size: 13px; color: #334155;")
        layout.addWidget(lbl_clave)

        self.txt_clave = QLineEdit()
        self.txt_clave.setPlaceholderText("Ej: KP-A365-68BD1A-9F42A1")
        self.txt_clave.setStyleSheet("font-family: monospace; font-size: 14px; font-weight: 600; padding: 8px;")
        layout.addWidget(self.txt_clave)

        # Botones de Acción
        actions = QHBoxLayout()
        if not self.obligatorio:
            btn_cerrar = QPushButton("Cerrar")
            btn_cerrar.setStyleSheet("background: #f1f5f9; color: #475569; border: 1px solid #cbd5e1; padding: 9px 16px; border-radius: 8px; font-weight: 600;")
            btn_cerrar.clicked.connect(self.reject)
            actions.addWidget(btn_cerrar)

        actions.addStretch()

        btn_sync_lic = QPushButton("☁️ Sincronizar Licencia")
        btn_sync_lic.setStyleSheet("background: #0891b2; color: white; padding: 9px 20px; border-radius: 8px; font-weight: 700; font-size: 13px;")
        btn_sync_lic.clicked.connect(self.republicar_licencia)
        actions.addWidget(btn_sync_lic)

        btn_activar = QPushButton("✅ Activar Licencia")
        btn_activar.setStyleSheet("background: #2563eb; color: white; padding: 9px 22px; border-radius: 8px; font-weight: 700; font-size: 14px;")
        btn_activar.clicked.connect(self.procesar_activacion)
        actions.addWidget(btn_activar)

        layout.addLayout(actions)

    def cargar_estado(self):
        info = init_or_get_license_info()
        self.txt_machine_id.setText(info["machine_id"])

        if info["estado"] == "vitalicio":
            self.lbl_estado_valor.setText("💎 " + info["plan_nombre"])
            self.lbl_estado_valor.setStyleSheet("font-size: 16px; font-weight: 800; color: #16a34a;")
            self.lbl_expiracion.setText("Vigencia permanente e ilimitada.")
        elif info["estado"] == "demo":
            self.lbl_estado_valor.setText(f"🎁 {info['plan_nombre']} ({info['dias_restantes']} días restantes)")
            self.lbl_estado_valor.setStyleSheet("font-size: 16px; font-weight: 700; color: #ea580c;")
            self.lbl_expiracion.setText(f"Válido hasta: {info['fecha_expiracion']}. Ingrese una clave para activar su plan.")
        elif info["estado"] == "activo":
            self.lbl_estado_valor.setText(f"✅ {info['plan_nombre']} ({info['dias_restantes']} días restantes)")
            self.lbl_estado_valor.setStyleSheet("font-size: 16px; font-weight: 700; color: #2563eb;")
            self.lbl_expiracion.setText(f"Vence el: {info['fecha_expiracion']}")
        else:
            self.lbl_estado_valor.setText("⚠️ " + info["plan_nombre"])
            self.lbl_estado_valor.setStyleSheet("font-size: 16px; font-weight: 800; color: #dc2626;")
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
