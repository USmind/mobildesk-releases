import sys
import os
import hashlib
import hmac
from datetime import datetime, timedelta

from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QComboBox,
    QMessageBox,
    QFrame
)
from PySide6.QtCore import Qt

MASTER_SECRET = b"KIOSKO_POS_PROTECTED_MASTER_SECRET_2026_V1"

APP_STYLE = """
QWidget {
    background-color: #f8fafc;
    color: #1e293b;
    font-family: 'Segoe UI', sans-serif;
    font-size: 13.5px;
}
QMainWindow {
    background-color: #f8fafc;
}
QLabel {
    background: transparent;
    border: none;
    color: #334155;
    font-size: 13.5px;
}
QLineEdit, QComboBox {
    background-color: #ffffff;
    border: 1.5px solid #cbd5e1;
    border-radius: 8px;
    padding: 9px 12px;
    font-size: 14px;
    min-height: 24px;
    color: #0f172a;
}
QLineEdit:focus, QComboBox:focus {
    border: 2px solid #2563eb;
}
QComboBox::drop-down {
    border: none;
    width: 24px;
}
QPushButton {
    background-color: #2563eb;
    color: #ffffff;
    border: none;
    border-radius: 8px;
    padding: 10px 16px;
    font-weight: 700;
    font-size: 14px;
}
QPushButton:hover {
    background-color: #1d4ed8;
}
QPushButton:pressed {
    background-color: #1e40af;
}
QFrame#form_card, QFrame#res_card {
    background-color: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 12px;
}
"""


def generate_key(machine_id: str, plan: str, days: int = 365) -> str:
    clean_mid = machine_id.strip().upper()
    plan_code = plan.upper()

    if plan_code == "V":
        expiry_ts = 0
    else:
        expiry_date = datetime.now() + timedelta(days=days)
        expiry_ts = int(expiry_date.timestamp())

    expiry_hex = f"{expiry_ts:08X}"
    payload = f"{clean_mid}|{plan_code}|{expiry_hex}"
    signature = hmac.new(MASTER_SECRET, payload.encode("utf-8"), hashlib.sha256).hexdigest().upper()[:8]
    return f"KP-{plan_code}-{expiry_hex}-{signature}"


class LicenseGeneratorWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Generador Privado de Licencias - MobilDesk POS")
        self.resize(620, 560)
        self.setMinimumSize(560, 500)
        self.crear_interfaz()

    def crear_interfaz(self):
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setSpacing(14)
        layout.setContentsMargins(26, 22, 26, 22)

        # Encabezado
        title = QLabel("🏢 GENERADOR PRIVADO DE LICENCIAS")
        title.setStyleSheet("font-size: 20px; font-weight: 800; color: #0f172a;")
        layout.addWidget(title)

        sub = QLabel("Herramienta exclusiva del administrador para generar claves de activación.")
        sub.setStyleSheet("color: #64748b; font-size: 13.5px; padding-bottom: 4px;")
        layout.addWidget(sub)

        # Formulario
        form_frame = QFrame()
        form_frame.setObjectName("form_card")
        form_layout = QVBoxLayout(form_frame)
        form_layout.setSpacing(10)
        form_layout.setContentsMargins(18, 16, 18, 16)

        lbl1 = QLabel("1. Nombre del Negocio / Cliente:")
        lbl1.setStyleSheet("font-weight: 700; color: #334155;")
        form_layout.addWidget(lbl1)
        self.txt_negocio = QLineEdit()
        self.txt_negocio.setPlaceholderText("Ej: Bodega La Bendición")
        form_layout.addWidget(self.txt_negocio)

        lbl2 = QLabel("2. Código de la Computadora del Cliente (Machine ID):")
        lbl2.setStyleSheet("font-weight: 700; color: #334155; margin-top: 4px;")
        form_layout.addWidget(lbl2)
        self.txt_machine_id = QLineEdit()
        self.txt_machine_id.setPlaceholderText("Ej: KP-2415-745E-043D")
        self.txt_machine_id.setStyleSheet("font-family: Consolas, monospace; font-weight: 700;")
        form_layout.addWidget(self.txt_machine_id)

        lbl3 = QLabel("3. Plan a Activar:")
        lbl3.setStyleSheet("font-weight: 700; color: #334155; margin-top: 4px;")
        form_layout.addWidget(lbl3)
        self.combo_plan = QComboBox()
        self.combo_plan.addItem("💎 Plan Vitalicio (Pago Único / Permanente)", ("V", 0))
        self.combo_plan.addItem("🎁 Prueba Extendida (15 Días)", ("D", 15))
        self.combo_plan.addItem("🏆 Plan Anual (365 Días)", ("A", 365))
        self.combo_plan.addItem("📅 Plan Mensual (30 Días)", ("M", 30))
        form_layout.addWidget(self.combo_plan)

        layout.addWidget(form_frame)

        # Botón Generar
        btn_generar = QPushButton("🔑 Generar Clave de Activación")
        btn_generar.setStyleSheet("background: #2563eb; color: white; padding: 12px; border-radius: 9px; font-weight: 800; font-size: 15px;")
        btn_generar.clicked.connect(self.generar_licencia)
        layout.addWidget(btn_generar)

        # Resultado
        res_frame = QFrame()
        res_frame.setObjectName("res_card")
        res_layout = QVBoxLayout(res_frame)
        res_layout.setSpacing(10)
        res_layout.setContentsMargins(18, 16, 18, 16)

        lbl_res = QLabel("Clave Generada:")
        lbl_res.setStyleSheet("font-weight: 700; color: #334155;")
        res_layout.addWidget(lbl_res)

        self.txt_clave_resultado = QLineEdit()
        self.txt_clave_resultado.setReadOnly(True)
        self.txt_clave_resultado.setStyleSheet("background-color: #f8fafc; font-family: Consolas, monospace; font-size: 16px; font-weight: 800; color: #15803d; border: 2px solid #86efac; padding: 10px;")
        res_layout.addWidget(self.txt_clave_resultado)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(10)

        btn_copiar_clave = QPushButton("📋 Copiar Clave")
        btn_copiar_clave.setStyleSheet("background: #f1f5f9; color: #1e293b; border: 1px solid #cbd5e1; font-weight: 700; padding: 9px;")
        btn_copiar_clave.clicked.connect(self.copiar_clave)
        btn_row.addWidget(btn_copiar_clave)

        btn_copiar_wsp = QPushButton("📲 Copiar Mensaje para WhatsApp")
        btn_copiar_wsp.setStyleSheet("background: #16a34a; color: white; font-weight: 700; padding: 9px;")
        btn_copiar_wsp.clicked.connect(self.copiar_mensaje_whatsapp)
        btn_row.addWidget(btn_copiar_wsp)

        res_layout.addLayout(btn_row)
        layout.addWidget(res_frame)

    def generar_licencia(self):
        mid = self.txt_machine_id.text().strip()
        negocio = self.txt_negocio.text().strip() or "Estimado Cliente"

        if not mid:
            QMessageBox.warning(self, "Aviso", "Debes ingresar el Machine ID de la computadora del cliente.")
            return

        plan_code, days = self.combo_plan.currentData()
        clave = generate_key(mid, plan_code, days)
        self.txt_clave_resultado.setText(clave)
        QMessageBox.information(
            self,
            "¡Clave Generada!",
            f"Clave generada con éxito para:\n\n"
            f"👤 Negocio: {negocio}\n"
            f"📦 Plan: {self.combo_plan.currentText()}\n"
            f"🔑 Clave: {clave}"
        )

    def copiar_clave(self):
        clave = self.txt_clave_resultado.text().strip()
        if clave:
            QApplication.clipboard().setText(clave)
            QMessageBox.information(self, "Copiado", "Clave copiada al portapapeles.")
        else:
            QMessageBox.warning(self, "Aviso", "Primero genera una clave.")

    def copiar_mensaje_whatsapp(self):
        clave = self.txt_clave_resultado.text().strip()
        if not clave:
            QMessageBox.warning(self, "Aviso", "Primero genera una clave.")
            return

        negocio = self.txt_negocio.text().strip() or "Estimado Cliente"
        plan_nombre = self.combo_plan.currentText()

        msg = (
            f"¡Hola {negocio}! 👋\n\n"
            f"Tu licencia de *MobilDesk POS* ha sido activada:\n\n"
            f"📦 *Plan:* {plan_nombre}\n"
            f"🔑 *Tu Clave de Activación:* `{clave}`\n\n"
            f"📋 *Pasos para activar:*\n"
            f"1. Abre el programa MobilDesk en tu computadora.\n"
            f"2. Haz clic en el botón *Activar* o ve a *🔑 Licencia y Plan*.\n"
            f"3. Pega tu clave de activación y presiona *✅ Activar Licencia*.\n\n"
            f"¡Gracias por confiar en MobilDesk POS! 🚀"
        )

        QApplication.clipboard().setText(msg)
        QMessageBox.information(self, "Mensaje Copiado", "Mensaje con instrucciones copiado al portapapeles.\n\n¡Ya puedes pegarlo directamente en WhatsApp!")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyleSheet(APP_STYLE)
    ventana = LicenseGeneratorWindow()
    ventana.show()
    sys.exit(app.exec())
