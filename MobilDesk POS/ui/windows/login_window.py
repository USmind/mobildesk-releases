import os
import json
from pathlib import Path
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QHBoxLayout,
    QMessageBox,
    QFrame,
    QCheckBox,
)
from modules.usuarios.user_service import authenticate
from modules.usuarios.session import set_user
from modules.configuracion.business_service import get_business_settings
from ui.windows.dashboard_window import DashboardWindow

PREFS_FILE = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local")) / "MobilDesk" / "login_prefs.json"


class LoginWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.dashboard = None
        self.biz_settings = get_business_settings()
        self.nombre_negocio = self.biz_settings.get("nombre_negocio", "MobilDesk")
        self.setWindowTitle(f"{self.nombre_negocio} - Acceso al Sistema")
        self.setFixedSize(440, 450)
        self.crear_interfaz()
        self.cargar_preferencias()

    def crear_interfaz(self):
        self.setStyleSheet("""
            QWidget { background-color: #f8fafc; font-family: 'Segoe UI', sans-serif; }
            QLabel { color: #334155; font-size: 13px; font-weight: 600; border: none; background: transparent; }
            QLineEdit { background: white; border: 1.5px solid #cbd5e1; border-radius: 8px; padding: 10px 12px; font-size: 14px; min-height: 22px; color: #0f172a; }
            QLineEdit:focus { border: 2px solid #2563eb; }
            QCheckBox { color: #475569; font-size: 13px; font-weight: 600; spacing: 6px; }
            QCheckBox::indicator { width: 17px; height: 17px; border-radius: 4px; border: 1.5px solid #cbd5e1; background: white; }
            QCheckBox::indicator:checked { background: #2563eb; border-color: #2563eb; }
            QPushButton { background: #2563eb; color: white; border: none; border-radius: 8px; font-size: 15px; font-weight: 700; padding: 11px; }
            QPushButton:hover { background: #1d4ed8; }
        """)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(36, 26, 36, 26)
        outer.setSpacing(10)
        outer.addStretch()

        title = QLabel(self.nombre_negocio.upper())
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 24px; font-weight: 800; color: #0f172a; border: none;")

        subtitle = QLabel("MobilDesk · Punto de Venta e Inventario")
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setStyleSheet("color: #64748b; font-size: 13px; font-weight: 500; margin-bottom: 6px; border: none;")

        outer.addWidget(title)
        outer.addWidget(subtitle)

        card = QFrame()
        card.setObjectName("loginCard")
        card.setStyleSheet("QFrame#loginCard { background: white; border: 1px solid #cbd5e1; border-radius: 14px; } QLabel { border: none; background: transparent; }")
        form = QVBoxLayout(card)
        form.setContentsMargins(24, 20, 24, 20)
        form.setSpacing(10)

        lbl_u = QLabel("Usuario:")
        lbl_u.setStyleSheet("border: none; background: transparent; font-weight: 600; color: #334155;")
        form.addWidget(lbl_u)
        self.usuario = QLineEdit()
        self.usuario.setPlaceholderText("Ingresa tu usuario")
        form.addWidget(self.usuario)

        lbl_p = QLabel("Contraseña:")
        lbl_p.setStyleSheet("border: none; background: transparent; font-weight: 600; color: #334155;")
        form.addWidget(lbl_p)
        self.password = QLineEdit()
        self.password.setPlaceholderText("••••••••")
        self.password.setEchoMode(QLineEdit.Password)
        self.password.returnPressed.connect(self.iniciar_sesion)
        form.addWidget(self.password)

        # Checkbox Recordar Usuario
        self.chk_recordar = QCheckBox("Recordar usuario")
        form.addWidget(self.chk_recordar)

        form.addSpacing(4)
        button = QPushButton("🚀 Ingresar al Sistema")
        button.setMinimumHeight(44)
        button.clicked.connect(self.iniciar_sesion)
        form.addWidget(button)

        outer.addWidget(card)
        outer.addStretch()

    def cargar_preferencias(self):
        try:
            if PREFS_FILE.exists():
                with open(PREFS_FILE, "r", encoding="utf-8") as f:
                    prefs = json.load(f)
                    if prefs.get("recordar", False) and prefs.get("usuario"):
                        self.usuario.setText(prefs["usuario"])
                        self.chk_recordar.setChecked(True)
                        self.password.setFocus()
                        return
        except Exception:
            pass
        self.usuario.setFocus()

    def guardar_preferencias(self, username):
        try:
            PREFS_FILE.parent.mkdir(parents=True, exist_ok=True)
            data = {
                "recordar": self.chk_recordar.isChecked(),
                "usuario": username if self.chk_recordar.isChecked() else "",
            }
            with open(PREFS_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    def iniciar_sesion(self):
        user = authenticate(self.usuario.text(), self.password.text())
        if not user:
            QMessageBox.warning(self, "Acceso Incorrecto", "Usuario o contraseña incorrectos.")
            return

        self.guardar_preferencias(self.usuario.text().strip())
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
