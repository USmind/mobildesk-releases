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
        self.setMinimumSize(460, 380)
        self.crear_interfaz()
        self.cargar_datos()

    def crear_interfaz(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(14)

        title = QLabel("DATOS DEL NEGOCIO")
        title.setObjectName("pageTitle")
        layout.addWidget(title)

        subtitle = QLabel(
            "Configura el nombre de tu comercio y los datos de contacto. "
            "Estos datos aparecerán en los tickets, comprobantes y encabezados de MobilDesk."
        )
        subtitle.setObjectName("pageSubtitle")
        subtitle.setWordWrap(True)
        layout.addWidget(subtitle)

        lbl_sec = QLabel("DATOS DEL COMERCIO")
        lbl_sec.setObjectName("sectionLabel")
        layout.addWidget(lbl_sec)

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
        btn_cancelar.setProperty("variant", "ghost")
        btn_cancelar.setToolTip("Cerrar sin guardar cambios")
        btn_cancelar.clicked.connect(self.reject)

        btn_guardar = QPushButton("Guardar Cambios")
        btn_guardar.setProperty("variant", "success")
        btn_guardar.setToolTip("Guardar los datos del negocio")
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
