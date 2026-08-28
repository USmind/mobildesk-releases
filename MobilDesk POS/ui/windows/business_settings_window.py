from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QFormLayout,
    QLineEdit,
    QPushButton,
    QLabel,
    QMessageBox,
    QTextEdit,
    QHBoxLayout,
)
from PySide6.QtCore import Signal
from modules.configuracion.business_service import (
    get_business_settings,
    save_business_settings,
)


class BusinessSettingsWindow(QDialog):
    settings_saved = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Configuración del Negocio")
        self.resize(520, 420)
        self.crear_interfaz()
        self.cargar_datos()

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
            QLineEdit, QTextEdit {
                background-color: #ffffff;
                border: 1.5px solid #cbd5e1;
                border-radius: 7px;
                padding: 7px 10px;
                color: #0f172a;
            }
            QLineEdit:focus, QTextEdit:focus { border: 2px solid #2563eb; }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 24, 28, 24)
        layout.setSpacing(14)

        title = QLabel("DATOS DEL NEGOCIO")
        title.setStyleSheet("font-size: 20px; font-weight: 800; color: #0f172a; border: none;")
        layout.addWidget(title)

        subtitle = QLabel(
            "Configura el nombre de tu comercio y los datos de contacto. "
            "Estos datos aparecerán en los tickets, comprobantes y encabezados de MobilDesk."
        )
        subtitle.setWordWrap(True)
        subtitle.setStyleSheet("color: #64748b; font-size: 13px; border: none;")
        layout.addWidget(subtitle)

        form = QFormLayout()
        form.setSpacing(10)

        self.campo_nombre = QLineEdit()
        self.campo_nombre.setPlaceholderText("Ej: Mi Bodega Express / Supermercado San José")

        self.campo_id = QLineEdit()
        self.campo_id.setPlaceholderText("Ej: J-12345678-9 o V-12345678")

        self.campo_telefono = QLineEdit()
        self.campo_telefono.setPlaceholderText("Ej: 0414-1234567")

        self.campo_direccion = QLineEdit()
        self.campo_direccion.setPlaceholderText("Ej: Av. Principal, Local 4, Centro")

        self.campo_mensaje = QTextEdit()
        self.campo_mensaje.setMaximumHeight(70)
        self.campo_mensaje.setPlaceholderText("Mensaje al final de los tickets impresos...")

        form.addRow("Nombre del Negocio *:", self.campo_nombre)
        form.addRow("RIF / Identificación:", self.campo_id)
        form.addRow("Teléfono de Contacto:", self.campo_telefono)
        form.addRow("Dirección Comercial:", self.campo_direccion)
        form.addRow("Mensaje del Ticket:", self.campo_mensaje)

        layout.addLayout(form)

        botones = QHBoxLayout()
        btn_cancelar = QPushButton("Cancelar")
        btn_cancelar.setStyleSheet("background: #e2e8f0; color: #334155; border: none; padding: 8px 16px; border-radius: 6px; font-weight: 600;")
        btn_cancelar.clicked.connect(self.reject)

        btn_guardar = QPushButton("💾 Guardar Cambios")
        btn_guardar.setStyleSheet("background: #2563eb; color: white; border: none; padding: 8px 20px; border-radius: 6px; font-weight: 700;")
        btn_guardar.clicked.connect(self.guardar)

        botones.addStretch()
        botones.addWidget(btn_cancelar)
        botones.addWidget(btn_guardar)

        layout.addLayout(botones)

    def cargar_datos(self):
        biz = get_business_settings()
        self.campo_nombre.setText(biz.get("nombre_negocio", "MobilDesk"))
        self.campo_id.setText(biz.get("identificacion", ""))
        self.campo_telefono.setText(biz.get("telefono", ""))
        self.campo_direccion.setText(biz.get("direccion", ""))
        self.campo_mensaje.setPlainText(biz.get("mensaje_ticket", "¡Gracias por su compra!"))

    def guardar(self):
        nombre = self.campo_nombre.text().strip()
        if not nombre:
            QMessageBox.warning(self, "Validación", "El nombre del negocio es obligatorio.")
            self.campo_nombre.setFocus()
            return

        try:
            save_business_settings(
                nombre_negocio=nombre,
                identificacion=self.campo_id.text().strip(),
                telefono=self.campo_telefono.text().strip(),
                direccion=self.campo_direccion.text().strip(),
                mensaje_ticket=self.campo_mensaje.toPlainText().strip(),
            )
            QMessageBox.information(
                self,
                "Configuración Guardada",
                f"Los datos de '{nombre}' se actualizaron correctamente.",
            )
            self.settings_saved.emit(nombre)
            self.accept()
        except ValueError as error:
            QMessageBox.warning(self, "Error", str(error))
        except Exception as error:
            QMessageBox.critical(self, "Error", f"No se pudo guardar la configuración.\n\n{error}")
