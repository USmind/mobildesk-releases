import os
import sys
from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QProgressBar,
    QPushButton,
    QFrame,
    QApplication,
)
from modules.actualizador.update_service import (
    DownloadAndApplyWorker,
    apply_update_and_restart,
)


class AutoUpdateModalDialog(QDialog):
    def __init__(self, version, download_url, changelog="", parent=None):
        super().__init__(parent)
        self.version = version
        self.download_url = download_url
        self.changelog = changelog
        self.installer_path = None

        self.setWindowTitle(f"🚀 Actualización v{version} - MobilDesk POS")
        self.setFixedSize(480, 260)
        self.setWindowFlags(Qt.Dialog | Qt.CustomizeWindowHint | Qt.WindowTitleHint)
        self.crear_interfaz()
        self.iniciar_descarga()

    def crear_interfaz(self):
        self.setStyleSheet("""
            QDialog {
                background-color: #ffffff;
                font-family: 'Segoe UI', sans-serif;
            }
            QLabel {
                color: #0f172a;
            }
            QProgressBar {
                border: 1.5px solid #cbd5e1;
                border-radius: 8px;
                text-align: center;
                background-color: #f1f5f9;
                font-weight: 700;
                font-size: 13px;
                color: #1e3a8a;
                height: 26px;
            }
            QProgressBar::chunk {
                background: qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:0, stop:0 #2563eb, stop:1 #16a34a);
                border-radius: 6px;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(26, 24, 26, 24)
        layout.setSpacing(14)

        # Encabezado
        self.lbl_title = QLabel(f"🚀 Actualizando a MobilDesk POS v{self.version}")
        self.lbl_title.setStyleSheet("font-size: 17px; font-weight: 800; color: #1e3a8a;")
        layout.addWidget(self.lbl_title)

        self.lbl_sub = QLabel("Se ha detectado una nueva versión oficial con mejoras. Aplicando automáticamente...")
        self.lbl_sub.setStyleSheet("font-size: 13px; color: #475569;")
        self.lbl_sub.setWordWrap(True)
        layout.addWidget(self.lbl_sub)

        # Barra de Progreso
        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        self.progress.setValue(0)
        layout.addWidget(self.progress)

        # Estado dinámico
        self.lbl_status = QLabel("Conectando con el servidor de actualizaciones...")
        self.lbl_status.setStyleSheet("font-size: 12.5px; color: #64748b; font-weight: 600;")
        layout.addWidget(self.lbl_status)

        layout.addStretch()

        # Nota al pie
        lbl_footer = QLabel("🔒 Tus productos, ventas y datos permanecerán 100% intactos.")
        lbl_footer.setStyleSheet("font-size: 11.5px; color: #16a34a; font-weight: 700;")
        layout.addWidget(lbl_footer)

    def iniciar_descarga(self):
        self.worker = DownloadAndApplyWorker(self.download_url, self.version)
        self.worker.progress_signal.connect(self.on_progress)
        self.worker.status_signal.connect(self.on_status)
        self.worker.finished_signal.connect(self.on_finished)
        self.worker.start()

    def on_progress(self, percent):
        self.progress.setValue(percent)

    def on_status(self, text):
        self.lbl_status.setText(text)

    def on_finished(self, success, result_path):
        if success and result_path and os.path.exists(result_path):
            self.installer_path = result_path
            self.lbl_status.setText("✅ ¡Descarga completada! Instalando y reiniciando...")
            self.lbl_status.setStyleSheet("font-size: 13px; color: #16a34a; font-weight: 700;")
            self.progress.setValue(100)
            
            # Ejecutar instalador y cerrar la app en 1 segundo
            QTimer.singleShot(1000, self.ejecutar_instalador_y_salir)
        else:
            # Si falla la descarga, continuar normalmente sin bloquear
            self.lbl_status.setText("Aviso: No se pudo completar la descarga. Iniciando sistema...")
            QTimer.singleShot(1500, self.reject)

    def ejecutar_instalador_y_salir(self):
        if self.installer_path:
            apply_update_and_restart(self.installer_path)
            QApplication.quit()
            sys.exit(0)
        else:
            self.reject()
