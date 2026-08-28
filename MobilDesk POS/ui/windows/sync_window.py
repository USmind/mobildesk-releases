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
    QApplication,
    QProgressBar,
)
from modules.sync.sync_service import (
    set_business_code,
    get_business_id,
    sync_now,
    get_sync_status_info,
)


class SyncWorker(QThread):
    """Hilo secundario para sincronizar sin bloquear la interfaz."""
    finished_signal = Signal(dict)
    error_signal = Signal(str)

    def run(self):
        try:
            res = sync_now()
            self.finished_signal.emit(res)
        except Exception as e:
            self.error_signal.emit(str(e))


class SyncWindow(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Sincronización en la Nube")
        self.resize(560, 500)
        self.setMinimumSize(480, 420)
        self.sync_worker = None
        self.crear_interfaz()
        self.actualizar_estado()

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
        layout.setContentsMargins(28, 28, 28, 28)
        layout.setSpacing(16)

        # Header
        h_box = QVBoxLayout()
        h_box.setSpacing(3)
        header = QLabel("☁️ Sincronización en la Nube")
        header.setStyleSheet("font-size: 20px; font-weight: 800; color: #0f172a; border: none;")
        sub = QLabel("Enlaza esta computadora con la app móvil de MobilDesk.")
        sub.setStyleSheet("font-size: 13px; color: #64748b; border: none;")
        h_box.addWidget(header)
        h_box.addWidget(sub)
        layout.addLayout(h_box)

        # Card de Código de Negocio (Clean, sin rayas duras)
        card_code = QFrame()
        card_code.setStyleSheet(
            "QFrame { background: #f8fafc; border: none; border-radius: 14px; } "
            "QLabel { background: transparent; }"
        )
        cc_layout = QVBoxLayout(card_code)
        cc_layout.setContentsMargins(20, 18, 20, 18)
        cc_layout.setSpacing(10)

        lbl_title = QLabel("CÓDIGO DE ENLACE DE TU NEGOCIO")
        lbl_title.setStyleSheet("font-size: 11.5px; font-weight: 700; color: #64748b; letter-spacing: 0.5px;")
        cc_layout.addWidget(lbl_title)

        code_row = QHBoxLayout()
        self.lbl_codigo_display = QLabel("MOBILDESK-0000")
        self.lbl_codigo_display.setStyleSheet("font-size: 24px; font-weight: 900; color: #1e3a8a; letter-spacing: 1px;")

        self.btn_copiar = QPushButton("📋 Copiar Código")
        self.btn_copiar.setStyleSheet(
            "QPushButton { background: white; color: #1e293b; border: 1px solid #e2e8f0; font-weight: bold; padding: 8px 14px; border-radius: 8px; } "
            "QPushButton:hover { background: #f1f5f9; }"
        )
        self.btn_copiar.clicked.connect(self.copiar_codigo)

        code_row.addWidget(self.lbl_codigo_display)
        code_row.addStretch()
        code_row.addWidget(self.btn_copiar)
        cc_layout.addLayout(code_row)

        desc = QLabel("💡 Escribe este código en la app de tu teléfono Android para sincronizar productos, precios, tasa del dólar, inventario y ventas en tiempo real.")
        desc.setWordWrap(True)
        desc.setStyleSheet("font-size: 12px; color: #475569;")
        cc_layout.addWidget(desc)

        layout.addWidget(card_code)

        # Personalizar Código (Opcional)
        custom_box = QHBoxLayout()
        self.txt_codigo_custom = QLineEdit()
        self.txt_codigo_custom.setPlaceholderText("Personalizar código (ej: BODEGA-EXITO)")
        self.txt_codigo_custom.setStyleSheet(
            "QLineEdit { background: white; border: 1px solid #e2e8f0; border-radius: 8px; padding: 8px 12px; font-size: 13px; } "
            "QLineEdit:focus { border: 2px solid #2563eb; }"
        )
        self.btn_guardar_codigo = QPushButton("Guardar")
        self.btn_guardar_codigo.setStyleSheet(
            "QPushButton { background: #0f766e; color: white; font-weight: bold; padding: 8px 14px; border-radius: 8px; border: none; } "
            "QPushButton:hover { background: #115e59; }"
        )
        self.btn_guardar_codigo.clicked.connect(self.guardar_codigo_personalizado)
        custom_box.addWidget(self.txt_codigo_custom)
        custom_box.addWidget(self.btn_guardar_codigo)
        layout.addLayout(custom_box)

        # Estado de Sincronización
        status_box = QHBoxLayout()
        self.lbl_status = QLabel("✅ En línea · Sincronizado")
        self.lbl_status.setStyleSheet("color: #16a34a; font-weight: bold; font-size: 13px;")

        self.lbl_ultimo = QLabel("Última vez: —")
        self.lbl_ultimo.setStyleSheet("color: #64748b; font-size: 12px;")

        status_box.addWidget(self.lbl_status)
        status_box.addStretch()
        status_box.addWidget(self.lbl_ultimo)
        layout.addLayout(status_box)

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 0)
        self.progress_bar.setFixedHeight(4)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)

        # Botón Principal Sincronizar
        self.btn_sync = QPushButton("🔄 Sincronizar Todo Ahora")
        self.btn_sync.setStyleSheet(
            "QPushButton { background: #2563eb; color: white; font-size: 15px; font-weight: bold; padding: 13px; border-radius: 10px; border: none; } "
            "QPushButton:hover { background: #1d4ed8; } "
            "QPushButton:pressed { background: #1e40af; }"
        )
        self.btn_sync.clicked.connect(self.ejecutar_sincronizacion)
        layout.addWidget(self.btn_sync)

    def actualizar_estado(self):
        info = get_sync_status_info()
        bid = info["business_id"]
        self.lbl_codigo_display.setText(bid)
        self.txt_codigo_custom.setText(bid)
        self.lbl_ultimo.setText(f"Última vez: {info['last_sync']}")

        if info.get("last_error"):
            self.lbl_status.setText("⚠️ Pendiente por reconectar")
            self.lbl_status.setStyleSheet("color: #d97706; font-weight: bold; font-size: 13px;")
        else:
            self.lbl_status.setText("✅ En línea y sincronizado")
            self.lbl_status.setStyleSheet("color: #16a34a; font-weight: bold; font-size: 13px;")

    def copiar_codigo(self):
        info = get_sync_status_info()
        QApplication.clipboard().setText(info["business_id"])
        QMessageBox.information(self, "Copiado", f"Código copiado al portapapeles:\n\n{info['business_id']}\n\nIngresa este código en la app de tu teléfono.")

    def guardar_codigo_personalizado(self):
        nuevo = self.txt_codigo_custom.text().strip().upper()
        if not nuevo:
            QMessageBox.warning(self, "Aviso", "Escribe un código válido.")
            return
        try:
            set_business_code(nuevo)
            self.actualizar_estado()
            QMessageBox.information(self, "Código Guardado", f"✅ Código de Negocio actualizado a:\n{nuevo}\n\nIngresa este mismo código en tu teléfono.")
            self.ejecutar_sincronizacion()
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))

    def ejecutar_sincronizacion(self):
        if self.sync_worker and self.sync_worker.isRunning():
            return
        self.btn_sync.setEnabled(False)
        self.btn_sync.setText("Sincronizando...")
        self.progress_bar.setVisible(True)

        self.sync_worker = SyncWorker()
        self.sync_worker.finished_signal.connect(self._on_sync_success)
        self.sync_worker.error_signal.connect(self._on_sync_error)
        self.sync_worker.start()

    def _on_sync_success(self, res):
        self.btn_sync.setEnabled(True)
        self.btn_sync.setText("🔄 Sincronizar Todo Ahora")
        self.progress_bar.setVisible(False)
        self.actualizar_estado()
        QMessageBox.information(
            self,
            "Sincronizado",
            f"✅ Sincronización exitosa:\n\n"
            f"• Cambios locales enviados: {res['sent']}\n"
            f"• Cambios recibidos del teléfono: {res['received']}",
        )

    def _on_sync_error(self, err_msg):
        self.btn_sync.setEnabled(True)
        self.btn_sync.setText("🔄 Sincronizar Todo Ahora")
        self.progress_bar.setVisible(False)
        self.actualizar_estado()
        QMessageBox.critical(self, "Aviso de Sincronización", err_msg)

