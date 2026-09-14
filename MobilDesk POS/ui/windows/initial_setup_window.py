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
        self.resize(540, 700)
        self.setMinimumSize(480, 580)
        self.configurado_exitosamente = False
        self.worker = None
        self.crear_interfaz()

    def crear_interfaz(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(32, 24, 32, 24)
        main_layout.setSpacing(14)

        # Header Minimalista
        h_box = QVBoxLayout()
        h_box.setSpacing(4)
        h_box.setAlignment(Qt.AlignCenter)

        icon_label = QLabel("")
        icon_label.setAlignment(Qt.AlignCenter)
        icon_label.setVisible(False)
        h_box.addWidget(icon_label)

        title = QLabel("Bienvenido a MobilDesk POS")
        title.setObjectName("pageTitle")
        title.setAlignment(Qt.AlignCenter)
        h_box.addWidget(title)

        subtitle = QLabel("Configura tu comercio y tu acceso en 1 minuto")
        subtitle.setObjectName("pageSubtitle")
        subtitle.setAlignment(Qt.AlignCenter)
        h_box.addWidget(subtitle)
        main_layout.addLayout(h_box)

        # Card Principal (Espaciosa, limpia, sin solapamientos)
        card = QFrame()
        card.setObjectName("card")
        grid = QGridLayout(card)
        grid.setContentsMargins(24, 20, 24, 20)
        grid.setHorizontalSpacing(12)
        grid.setVerticalSpacing(12)

        # Fila 0: Nombre del Negocio
        lbl_negocio = QLabel("NOMBRE DE TU COMERCIO")
        lbl_negocio.setObjectName("sectionLabel")
        grid.addWidget(lbl_negocio, 0, 0, 1, 2)
        self.txt_negocio = QLineEdit("Mi Comercio")
        self.txt_negocio.setPlaceholderText("Ej: Bodega San José, Minimarket Central...")
        grid.addWidget(self.txt_negocio, 1, 0, 1, 2)

        # Fila 2: Tu Nombre (el admin se crea con este nombre)
        lbl_nombre = QLabel("TU NOMBRE")
        lbl_nombre.setObjectName("sectionLabel")
        grid.addWidget(lbl_nombre, 2, 0, 1, 2)
        self.txt_admin_nombre = QLineEdit()
        self.txt_admin_nombre.setPlaceholderText("Ej: María Pérez")
        grid.addWidget(self.txt_admin_nombre, 3, 0, 1, 2)

        # Fila 4: Usuario y Contraseña (Lado a lado ordenado)
        lbl_user = QLabel("USUARIO ADMIN")
        lbl_user.setObjectName("sectionLabel")
        grid.addWidget(lbl_user, 4, 0)
        lbl_pass = QLabel("CONTRASEÑA")
        lbl_pass.setObjectName("sectionLabel")
        grid.addWidget(lbl_pass, 4, 1)

        self.txt_admin_user = QLineEdit("admin")
        self.txt_admin_user.setPlaceholderText("admin")
        grid.addWidget(self.txt_admin_user, 5, 0)

        self.txt_admin_pass = QLineEdit()
        self.txt_admin_pass.setEchoMode(QLineEdit.Password)
        self.txt_admin_pass.setPlaceholderText("Contraseña")
        grid.addWidget(self.txt_admin_pass, 5, 1)

        # Fila 6: Código de Negocio para App Móvil
        lbl_codigo = QLabel("CÓDIGO DE NEGOCIO (PARA LA APP MÓVIL)")
        lbl_codigo.setObjectName("sectionLabel")
        grid.addWidget(lbl_codigo, 6, 0, 1, 2)
        self.txt_codigo = QLineEdit(generate_new_business_code("MOBIL"))
        self.txt_codigo.setPlaceholderText("Código único para tu teléfono")
        self.txt_codigo.setStyleSheet("font-weight: 700; letter-spacing: 1px;")
        grid.addWidget(self.txt_codigo, 7, 0, 1, 2)

        # Fila 8: Ayuda / Tip
        hint = QLabel("Escribe este mismo código en la app de tu teléfono Android para sincronizar.")
        hint.setObjectName("pageSubtitle")
        hint.setWordWrap(True)
        grid.addWidget(hint, 8, 0, 1, 2)

        main_layout.addWidget(card)

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 0)
        self.progress_bar.setFixedHeight(4)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setVisible(False)
        main_layout.addWidget(self.progress_bar)

        # Botón de Inicio
        self.btn_comenzar = QPushButton("Comenzar a Usar MobilDesk POS")
        self.btn_comenzar.setProperty("variant", "success")
        self.btn_comenzar.setToolTip("Guardar la configuración y entrar al sistema")
        self.btn_comenzar.clicked.connect(self.completar_configuracion)
        main_layout.addWidget(self.btn_comenzar)

    def completar_configuracion(self):
        nombre_negocio = self.txt_negocio.text().strip()
        admin_nombre = self.txt_admin_nombre.text().strip()
        admin_user = self.txt_admin_user.text().strip().lower()
        admin_pass = self.txt_admin_pass.text().strip()
        business_code = self.txt_codigo.text().strip().upper()

        if not nombre_negocio:
            QMessageBox.warning(self, "Aviso", "Por favor ingresa el nombre de tu negocio.")
            self.txt_negocio.setFocus()
            return

        if not admin_nombre:
            admin_nombre = admin_user.capitalize() if admin_user else "Administrador"

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
            admin_nombre=admin_nombre,
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
        self.btn_comenzar.setText("Comenzar a Usar MobilDesk POS")
        self.progress_bar.setVisible(False)
        QMessageBox.critical(self, "Error", f"No se pudo completar la configuración: {err_msg}")
