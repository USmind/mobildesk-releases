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
    QFrame,
)
from PySide6.QtCore import Signal, Qt
from modules.configuracion.business_service import (
    get_business_settings,
    save_business_settings,
)
from modules.configuracion.wipe_service import (
    borrar_todos_los_datos,
    contar_datos,
)

PALABRA_CONFIRMACION = "BORRAR"


class BusinessSettingsWindow(QDialog):
    settings_saved = Signal(str)
    datos_borrados = Signal()

    def __init__(self, parent=None, usuario=None):
        super().__init__(parent)
        self.usuario = usuario or {}
        self.setWindowTitle("Configuración del Negocio")
        self.resize(520, 640)
        self.setMinimumSize(460, 420)
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
        layout.addWidget(self._crear_zona_peligro())

    def _crear_zona_peligro(self):
        """Zona de borrado total, separada del guardado normal."""
        contenedor = QFrame()
        contenedor.setObjectName("zonaPeligro")
        contenedor.setStyleSheet("""
            QFrame#zonaPeligro {
                background-color: #FEF2F2;
                border: 1px solid #FCA5A5;
                border-radius: 8px;
            }
        """)

        caja = QVBoxLayout(contenedor)
        caja.setContentsMargins(14, 12, 14, 12)
        caja.setSpacing(6)

        titulo = QLabel("Zona de riesgo")
        titulo.setStyleSheet("color: #B91C1C; font-weight: 700; font-size: 13px; border: none;")
        caja.addWidget(titulo)

        descripcion = QLabel(
            "Borra TODOS los datos del negocio: ventas, fiados, clientes, productos,\n"
            "inventario, caja y el código de sincronización con el móvil.\n"
            "Se crea un respaldo antes de borrar. Después tendrás que volver a\n"
            "configurar el negocio y activar la licencia."
        )
        descripcion.setWordWrap(True)
        descripcion.setStyleSheet("color: #7F1D1D; border: none; font-size: 11px;")
        caja.addWidget(descripcion)

        # Solo el admin puede borrar. El botón se oculta para los demás.
        if self.usuario.get("role") == "admin":
            self.btn_borrar = QPushButton("Borrar todos los datos")
            self.btn_borrar.setProperty("variant", "danger")
            self.btn_borrar.setCursor(Qt.PointingHandCursor)
            self.btn_borrar.clicked.connect(self.confirmar_borrado_total)
            caja.addWidget(self.btn_borrar)
        else:
            aviso = QLabel("Solo un administrador puede usar esta opción.")
            aviso.setStyleSheet("color: #7F1D1D; font-style: italic; border: none; font-size: 11px;")
            caja.addWidget(aviso)

        return contenedor

    def confirmar_borrado_total(self):
        """Muestra qué se va a borrar y pide escribir la palabra de confirmación."""
        try:
            resumen = contar_datos()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudieron contar los datos:\n\n{e}")
            return

        if not resumen:
            QMessageBox.information(
                self,
                "Nada que borrar",
                "No hay datos de negocio guardados. Todo está limpio.",
            )
            return

        filas = "\n".join(f"  · {t.replace('_', ' ')}: {n}" for t, n in sorted(resumen.items()))
        total = sum(resumen.values())

        # Primera confirmación: qué se borra.
        aviso = QMessageBox(self)
        aviso.setWindowTitle("Borrar todos los datos")
        aviso.setIcon(QMessageBox.Warning)
        aviso.setText(
            f"Se borrarán {total} registros de forma permanente:"
        )
        aviso.setInformativeText(
            f"{filas}\n\n"
            "También se borra la licencia: el programa quedará bloqueado hasta que\n"
            "vuelvas a activarla.\n\n"
            "Se guardará un respaldo antes de borrar."
        )
        btn_si = aviso.addButton("Sí, quiero borrarlo todo", QMessageBox.DestructiveRole)
        aviso.addButton("Cancelar", QMessageBox.RejectRole)
        aviso.exec()
        if aviso.clickedButton() is not btn_si:
            return

        # Segunda confirmación: escribir la palabra exacta.
        dialogo = QDialog(self)
        dialogo.setWindowTitle("Confirmación final")
        dialogo.setMinimumWidth(420)
        caja = QVBoxLayout(dialogo)
        caja.setContentsMargins(20, 18, 20, 18)
        caja.setSpacing(10)

        mensaje = QLabel(
            f"Para confirmar, escribe <b>{PALABRA_CONFIRMACION}</b> en mayúsculas\n"
            "y pulsa el botón. Esta es la última oportunidad para cancelar."
        )
        mensaje.setWordWrap(True)
        caja.addWidget(mensaje)

        campo = QLineEdit()
        campo.setPlaceholderText(PALABRA_CONFIRMACION)
        caja.addWidget(campo)

        botones = QHBoxLayout()
        botones.addStretch()
        btn_cancelar = QPushButton("Cancelar")
        btn_cancelar.setProperty("variant", "ghost")
        btn_cancelar.clicked.connect(dialogo.reject)
        btn_confirmar = QPushButton("Borrar definitivamente")
        btn_confirmar.setProperty("variant", "danger")
        btn_confirmar.setEnabled(False)
        btn_confirmar.clicked.connect(dialogo.accept)
        botones.addWidget(btn_cancelar)
        botones.addWidget(btn_confirmar)
        caja.addLayout(botones)

        # El botón solo se habilita con la palabra exacta.
        def _validar(texto):
            correcto = texto.strip().upper() == PALABRA_CONFIRMACION
            btn_confirmar.setEnabled(correcto)
            btn_confirmar.setText("Borrar definitivamente" if correcto else "Escribe BORRAR")

        campo.textChanged.connect(_validar)
        campo.setFocus()

        if dialogo.exec() != QDialog.Accepted:
            return

        self._ejecutar_borrado()

    def _ejecutar_borrado(self):
        try:
            resultado = borrar_todos_los_datos(
                incluir_sistema=True,
                usuario_rol=self.usuario.get("role", "admin"),
            )
        except Exception as e:
            QMessageBox.critical(
                self,
                "No se pudo borrar",
                f"Ocurrió un error y no se borró nada:\n\n{e}",
            )
            return

        total = sum(resultado["eliminadas"].values())
        filas = "\n".join(f"  · {t.replace('_', ' ')}: {n}" for t, n in sorted(resultado["eliminadas"].items()))

        QMessageBox.information(
            self,
            "Datos borrados",
            f"Se borraron {total} registros:\n{filas}\n\n"
            f"<b>Respaldo guardado en:</b>\n{resultado['respaldo']}\n\n"
            "El programa se reiniciará y mostrará la pantalla de\n"
            "Configuración Inicial para que crees el negocio y elijas\n"
            "tu usuario y tu contraseña.\n\n"
            "También tendrás que volver a activar la licencia.",
        )
        self.datos_borrados.emit()

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
