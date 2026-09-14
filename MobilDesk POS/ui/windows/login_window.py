from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget,
    QLabel,
    QLineEdit,
    QComboBox,
    QPushButton,
    QVBoxLayout,
    QHBoxLayout,
    QFrame,
)
from modules.usuarios.user_service import authenticate, get_users
from modules.usuarios.session import set_user
from modules.configuracion.business_service import get_business_settings
from ui.windows.dashboard_window import DashboardWindow


class LoginWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.dashboard = None
        self.biz_settings = get_business_settings()
        self.nombre_negocio = self.biz_settings.get("nombre_negocio", "MobilDesk")
        self.setWindowTitle(f"{self.nombre_negocio} - Acceso al Sistema")
        self.setFixedSize(470, 620)
        self.crear_interfaz()

    def crear_interfaz(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(40, 28, 40, 28)
        outer.setSpacing(8)

        # Avatar con inicial del negocio
        inicial = (self.nombre_negocio.strip()[:1] or "M").upper()
        avatar = QLabel(inicial)
        avatar.setAlignment(Qt.AlignCenter)
        avatar.setStyleSheet(
            "background-color: #0B0F1A; color: #FFFFFF; font-size: 24px; font-weight: 800;"
            "border-radius: 28px; min-width: 56px; min-height: 56px; max-width: 56px; max-height: 56px;"
        )
        avatar_row = QHBoxLayout()
        avatar_row.addStretch()
        avatar_row.addWidget(avatar)
        avatar_row.addStretch()
        outer.addLayout(avatar_row)

        title = QLabel(self.nombre_negocio.upper())
        title.setObjectName("pageTitle")
        title.setAlignment(Qt.AlignCenter)

        subtitle = QLabel("MobilDesk · Punto de Venta e Inventario")
        subtitle.setObjectName("pageSubtitle")
        subtitle.setAlignment(Qt.AlignCenter)

        outer.addWidget(title)
        outer.addWidget(subtitle)
        outer.addSpacing(8)

        card = QFrame()
        card.setObjectName("card")
        form = QVBoxLayout(card)
        form.setContentsMargins(28, 24, 28, 24)
        form.setSpacing(8)

        lbl_u = QLabel("USUARIO")
        lbl_u.setObjectName("sectionLabel")
        form.addWidget(lbl_u)
        # Desplegable con los usuarios registrados: solo se elige
        # y se escribe la contraseña (respaldo a texto si no hay lista).
        self.combo_usuario = QComboBox()
        self.combo_usuario.setToolTip("Elige tu usuario para entrar")
        self.txt_usuario_libre = QLineEdit()
        self.txt_usuario_libre.setPlaceholderText("Ingresa tu usuario")
        self.txt_usuario_libre.setMinimumHeight(46)
        self.txt_usuario_libre.setVisible(False)
        try:
            usuarios = [dict(r) for r in (get_users() or [])]
        except Exception:
            usuarios = []
        if usuarios:
            for u in usuarios:
                nombre = str(u.get("nombre") or "").strip()
                uname = str(u.get("username") or "").strip()
                # Solo el nombre a la vista; el username queda oculto en el dato.
                self.combo_usuario.addItem(nombre or uname, uname)
            self.combo_usuario.activated.connect(lambda: self.password.setFocus())
            form.addWidget(self.combo_usuario)
        else:
            self.txt_usuario_libre.setVisible(True)
        form.addWidget(self.txt_usuario_libre)

        lbl_p = QLabel("CONTRASEÑA")
        lbl_p.setObjectName("sectionLabel")
        form.addWidget(lbl_p)
        pass_row = QHBoxLayout()
        pass_row.setSpacing(8)
        self.password = QLineEdit()
        self.password.setPlaceholderText("Escribe tu contraseña")
        self.password.setEchoMode(QLineEdit.Password)
        self.password.setMinimumHeight(46)
        self.password.returnPressed.connect(self.iniciar_sesion)
        pass_row.addWidget(self.password, 1)
        self.btn_ver_clave = QPushButton("Mostrar")
        self.btn_ver_clave.setProperty("variant", "ghost")
        self.btn_ver_clave.setFixedWidth(92)
        self.btn_ver_clave.setToolTip("Mostrar u ocultar la contraseña")
        self.btn_ver_clave.clicked.connect(self._alternar_clave)
        pass_row.addWidget(self.btn_ver_clave)
        form.addLayout(pass_row)

        self.lbl_error = QLabel("")
        self.lbl_error.setWordWrap(True)
        self.lbl_error.setStyleSheet("color: #DC2626; font-size: 12.5px; font-weight: 600;")
        form.addWidget(self.lbl_error)

        form.addSpacing(4)
        button = QPushButton("Ingresar al Sistema")
        button.setMinimumHeight(48)
        button.setToolTip("Iniciar sesión con tu usuario y contraseña")
        button.clicked.connect(self.iniciar_sesion)
        form.addWidget(button)

        hint = QLabel("¿Problemas para entrar? Pide ayuda al administrador.")
        hint.setObjectName("pageSubtitle")
        hint.setAlignment(Qt.AlignCenter)
        hint.setWordWrap(True)
        form.addWidget(hint)

        outer.addWidget(card)
        outer.addStretch()
        self.password.setFocus()

    def _alternar_clave(self):
        if self.password.echoMode() == QLineEdit.Password:
            self.password.setEchoMode(QLineEdit.Normal)
            self.btn_ver_clave.setText("Ocultar")
        else:
            self.password.setEchoMode(QLineEdit.Password)
            self.btn_ver_clave.setText("Mostrar")

    def _usuario_seleccionado(self):
        if self.combo_usuario.count() > 0:
            return str(self.combo_usuario.currentData() or "").strip()
        return self.txt_usuario_libre.text().strip()

    def iniciar_sesion(self):
        username = self._usuario_seleccionado()
        user = authenticate(username, self.password.text()) if username else None
        if not user:
            self.lbl_error.setText("Usuario o contraseña incorrectos. Inténtalo de nuevo.")
            self.password.clear()
            self.password.setFocus()
            return
        self.lbl_error.setText("")

        set_user(user)

        # Verificación rápida de actualización al iniciar sesión
        try:
            from modules.actualizador.update_service import check_remote_version
            from ui.windows.update_dialog import AutoUpdateModalDialog
            from PySide6.QtWidgets import QDialog

            info = check_remote_version()
            if info and info.get("download_url"):
                dialog = AutoUpdateModalDialog(
                    version=info["version"],
                    download_url=info["download_url"],
                    changelog=info.get("changelog", ""),
                    parent=self,
                )
                # Si se ejecuta la actualización, dialog.exec() cerrará la app para reiniciar
                dialog.exec()
        except Exception as e:
            print(f"Aviso en verificación de actualización: {e}")

        self.dashboard = DashboardWindow()
        self.dashboard.show()
        self.close()
