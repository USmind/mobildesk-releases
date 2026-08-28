from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtWidgets import (
    QDialog,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QMessageBox,
    QFrame,
    QProgressBar,
    QGridLayout,
)
from modules.configuracion.business_service import save_business_settings
from modules.usuarios.user_service import create_user
from modules.usuarios.session import set_user
from modules.sync.sync_service import set_business_code, generate_new_business_code, sync_now


class InitialSetupWorker(QThread):
    finished_signal = Signal()
    error_signal = Signal(str)

    def __init__(self, nombre_negocio, admin_nombre, admin_user, admin_pass, business_code):
        super().__init__()
        self.nombre_negocio = nombre_negocio
        self.admin_nombre = admin_nombre
        self.admin_user = admin_user
        self.admin_pass = admin_pass
        self.business_code = business_code
        self.user_obj = None

    def run(self):
        try:
            # 1. Guardar nombre del negocio
            save_business_settings(nombre_negocio=self.nombre_negocio)

            # 2. Crear usuario administrador
            user_id = create_user(self.admin_nombre, self.admin_user, self.admin_pass, "admin")
            self.user_obj = {
                "id": user_id,
                "nombre": self.admin_nombre,
                "username": self.admin_user,
                "role": "admin",
            }

            # 3. Guardar código de negocio
            if self.business_code:
                set_business_code(self.business_code)

            # 4. Intentar sincronización inicial sin bloquear
            try:
                sync_now()
            except Exception:
                pass

            self.finished_signal.emit()
        except Exception as e:
            self.error_signal.emit(str(e))


class InitialSetupWindow(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("MobilDesk POS - Bienvenido")
        self.resize(540, 620)
        self.setMinimumSize(480, 500)
        self.configurado_exitosamente = False
        self.worker = None
        self.crear_interfaz()

    def crear_interfaz(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(36, 32, 36, 32)
        main_layout.setSpacing(18)

        # Header Minimalista
        h_box = QVBoxLayout()
        h_box.setSpacing(4)
        h_box.setAlignment(Qt.AlignCenter)

        icon_label = QLabel("🏪")
        icon_label.setAlignment(Qt.AlignCenter)
        icon_label.setStyleSheet("font-size: 38px; margin-bottom: 2px;")
        h_box.addWidget(icon_label)

        title = QLabel("Bienvenido a MobilDesk POS")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 23px; font-weight: 800; color: #0f172a; letter-spacing: -0.3px;")
        h_box.addWidget(title)

        subtitle = QLabel("Configura tu comercio y tu acceso en 1 minuto")
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setStyleSheet("font-size: 13.5px; color: #64748b;")
        h_box.addWidget(subtitle)
        main_layout.addLayout(h_box)

        # Card Principal (Espaciosa, limpia, sin solapamientos)
        card = QFrame()
        card.setStyleSheet(
            "QFrame { background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 16px; } "
            "QLabel { color: #334155; font-size: 12.5px; font-weight: 600; background: transparent; border: none; } "
            "QLineEdit { background: white; border: 1px solid #cbd5e1; border-radius: 9px; padding: 10px 14px; font-size: 14px; color: #0f172a; min-height: 20px; } "
            "QLineEdit:focus { border: 2px solid #2563eb; background: #ffffff; }"
        )
        grid = QGridLayout(card)
        grid.setContentsMargins(24, 24, 24, 24)
        grid.setHorizontalSpacing(14)
        grid.setVerticalSpacing(14)

        # Fila 0: Nombre del Negocio
        grid.addWidget(QLabel("Nombre de tu Comercio"), 0, 0, 1, 2)
        self.txt_negocio = QLineEdit("Mi Comercio")
        self.txt_negocio.setPlaceholderText("Ej: Bodega San José, Minimarket Central...")
        grid.addWidget(self.txt_negocio, 1, 0, 1, 2)

        # Fila 2: Usuario y Contraseña (Lado a lado ordenado)
        grid.addWidget(QLabel("Usuario Admin"), 2, 0)
        grid.addWidget(QLabel("Contraseña"), 2, 1)

        self.txt_admin_user = QLineEdit("admin")
        self.txt_admin_user.setPlaceholderText("admin")
        grid.addWidget(self.txt_admin_user, 3, 0)

        self.txt_admin_pass = QLineEdit()
        self.txt_admin_pass.setEchoMode(QLineEdit.Password)
        self.txt_admin_pass.setPlaceholderText("Contraseña")
        grid.addWidget(self.txt_admin_pass, 3, 1)

        # Fila 4: Código de Negocio para App Móvil
        grid.addWidget(QLabel("Código de Negocio (para la App Móvil)"), 4, 0, 1, 2)
        self.txt_codigo = QLineEdit(generate_new_business_code("MOBIL"))
        self.txt_codigo.setPlaceholderText("Código único para tu teléfono")
        self.txt_codigo.setStyleSheet("font-weight: bold; letter-spacing: 1px; color: #1e3a8a;")
        grid.addWidget(self.txt_codigo, 5, 0, 1, 2)

        # Fila 6: Ayuda / Tip
        hint = QLabel("💡 Escribe este mismo código en la app de tu teléfono Android para sincronizar.")
        hint.setStyleSheet("font-size: 11.5px; color: #64748b; font-weight: normal; background: transparent; border: none;")
        hint.setWordWrap(True)
        grid.addWidget(hint, 6, 0, 1, 2)

        main_layout.addWidget(card)

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 0)
        self.progress_bar.setFixedHeight(4)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setVisible(False)
        main_layout.addWidget(self.progress_bar)

        # Botón de Inicio
        self.btn_comenzar = QPushButton("🚀 Comenzar a Usar MobilDesk POS")
        self.btn_comenzar.setStyleSheet(
            "QPushButton { background: #16a34a; color: white; font-size: 15.5px; font-weight: bold; padding: 14px; border-radius: 11px; border: none; } "
            "QPushButton:hover { background: #15803d; } "
            "QPushButton:pressed { background: #166534; }"
        )
        self.btn_comenzar.clicked.connect(self.completar_configuracion)
        main_layout.addWidget(self.btn_comenzar)

    def completar_configuracion(self):
        nombre_negocio = self.txt_negocio.text().strip()
        admin_user = self.txt_admin_user.text().strip().lower()
        admin_pass = self.txt_admin_pass.text().strip()
        business_code = self.txt_codigo.text().strip().upper()

        if not nombre_negocio:
            QMessageBox.warning(self, "Aviso", "Por favor ingresa el nombre de tu negocio.")
            self.txt_negocio.setFocus()
            return

        if not admin_user or not admin_pass:
            QMessageBox.warning(self, "Aviso", "Ingresa un usuario y una contraseña para el administrador.")
            self.txt_admin_pass.setFocus()
            return

        if not business_code:
            business_code = generate_new_business_code(nombre_negocio)

        self.btn_comenzar.setEnabled(False)
        self.btn_comenzar.setText("Iniciando MobilDesk POS...")
        self.progress_bar.setVisible(True)

        self.worker = InitialSetupWorker(
            nombre_negocio=nombre_negocio,
            admin_nombre="Administrador",
            admin_user=admin_user,
            admin_pass=admin_pass,
            business_code=business_code,
        )
        self.worker.finished_signal.connect(self._on_setup_success)
        self.worker.error_signal.connect(self._on_setup_error)
        self.worker.start()

    def _on_setup_success(self):
        set_user(self.worker.user_obj)
        self.configurado_exitosamente = True
        self.accept()

    def _on_setup_error(self, err_msg):
        self.btn_comenzar.setEnabled(True)
        self.btn_comenzar.setText("🚀 Comenzar a Usar MobilDesk POS")
        self.progress_bar.setVisible(False)
        QMessageBox.critical(self, "Error", f"No se pudo completar la configuración: {err_msg}")
