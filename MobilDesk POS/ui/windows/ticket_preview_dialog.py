from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QTextEdit,
    QPushButton,
    QLabel,
    QFileDialog,
    QMessageBox,
)
from PySide6.QtGui import QFont, QTextDocument
from PySide6.QtPrintSupport import QPrinter, QPrintDialog
from modules.ventas.ticket_service import generate_sale_ticket_text, generate_ticket_html


class TicketPreviewDialog(QDialog):
    def __init__(self, sale_id_or_invoice, parent=None):
        super().__init__(parent)
        self.sale_id_or_invoice = sale_id_or_invoice
        self.setWindowTitle("Comprobante de Venta")
        self.resize(460, 620)
        self.setMinimumSize(400, 500)
        self.ticket_text = ""
        self.ticket_html = ""
        self.crear_interfaz()
        self.cargar_ticket()

    def crear_interfaz(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(12)

        titulo = QLabel("VISTA PREVIA DEL TICKET")
        titulo.setObjectName("pageTitle")
        layout.addWidget(titulo)
        sub = QLabel("Revisa el comprobante antes de imprimirlo o guardarlo.")
        sub.setObjectName("pageSubtitle")
        layout.addWidget(sub)

        self.visor = QTextEdit()
        self.visor.setReadOnly(True)
        font = QFont("Courier New", 10)
        self.visor.setFont(font)
        layout.addWidget(self.visor)

        acciones = QHBoxLayout()

        btn_imprimir = QPushButton("Imprimir Ticket")
        btn_imprimir.setToolTip("Enviar el ticket a la impresora")
        btn_imprimir.clicked.connect(self.imprimir)

        btn_guardar = QPushButton("Guardar TXT")
        btn_guardar.setProperty("variant", "soft")
        btn_guardar.setToolTip("Guardar el ticket en un archivo de texto")
        btn_guardar.clicked.connect(self.guardar_txt)

        btn_cerrar = QPushButton("Cerrar")
        btn_cerrar.setProperty("variant", "ghost")
        btn_cerrar.setToolTip("Cerrar la vista previa")
        btn_cerrar.clicked.connect(self.accept)

        acciones.addWidget(btn_imprimir)
        acciones.addWidget(btn_guardar)
        acciones.addStretch()
        acciones.addWidget(btn_cerrar)

        layout.addLayout(acciones)

    def cargar_ticket(self):
        try:
            self.ticket_text = generate_sale_ticket_text(self.sale_id_or_invoice)
            self.ticket_html = generate_ticket_html(self.sale_id_or_invoice)
            self.visor.setPlainText(self.ticket_text)
        except Exception as error:
            self.visor.setPlainText(f"Error al generar el ticket:\n{error}")

    def imprimir(self):
        printer = QPrinter(QPrinter.HighResolution)
        dialogo = QPrintDialog(printer, self)
        dialogo.setWindowTitle("Imprimir Ticket de Venta")
        if dialogo.exec() == QPrintDialog.Accepted:
            documento = QTextDocument()
            documento.setHtml(self.ticket_html)
            documento.print_(printer)
            QMessageBox.information(self, "Impresión", "Documento enviado a la impresora.")

    def guardar_txt(self):
        archivo, _ = QFileDialog.getSaveFileName(
            self,
            "Guardar Ticket",
            f"Ticket_Factura_{self.sale_id_or_invoice}.txt",
            "Archivos de texto (*.txt)",
        )
        if archivo:
            try:
                with open(archivo, "w", encoding="utf-8") as f:
                    f.write(self.ticket_text)
                QMessageBox.information(self, "Ticket", "Ticket guardado exitosamente.")
            except Exception as error:
                QMessageBox.critical(self, "Error", f"No se pudo guardar el archivo:\n{error}")
