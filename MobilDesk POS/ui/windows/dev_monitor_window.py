import re
import json
import hashlib
import urllib.request
import urllib.error
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QTableWidget, QTableWidgetItem, QHeaderView,
    QMessageBox, QFrame, QInputDialog
)
from config import SUPABASE_URL, SUPABASE_KEY

def _to_uuid(text: str) -> str:
    t = text.strip().lower()
    if re.match(r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$', t):
        return t
    d = hashlib.md5(t.encode('utf-8')).hexdigest()
    return f"{d[0:8]}-{d[8:12]}-{d[12:16]}-{d[16:20]}-{d[20:32]}"

class DevMonitorWindow(QDialog):
    """Monitor privado solo para dueño: ver bodegas y borrar prueba por código."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Monitor de Desarrollador — MobilDesk (Solo Lectura)")
        self.setMinimumSize(720, 520)
        self.resize(780, 560)
        self._construir()

    def _construir(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(20, 16, 20, 16)

        title = QLabel("Monitor Privado — Bodegas")
        title.setObjectName("pageTitle")
        sub = QLabel("Solo para dueño. Busca un código (ej: MOBIL-6541) para ver info y —si es de prueba— borrar sus datos de la nube. No toca el bot de licencias.")
        sub.setObjectName("pageSubtitle")
        sub.setWordWrap(True)
        layout.addWidget(title)
        layout.addWidget(sub)

        # Buscador
        row = QHBoxLayout()
        self.input_codigo = QLineEdit()
        self.input_codigo.setPlaceholderText("Código de bodega, ej: MOBIL-6541")
        self.input_codigo.returnPressed.connect(self.buscar)
        btn_buscar = QPushButton("Buscar")
        btn_buscar.setProperty("variant", "soft")
        btn_buscar.clicked.connect(self.buscar)
        row.addWidget(self.input_codigo)
        row.addWidget(btn_buscar)
        layout.addLayout(row)

        self.lbl_info = QLabel("Escribe un código y pulsa Buscar. Se consultará solo lectura en Supabase.")
        self.lbl_info.setWordWrap(True)
        self.lbl_info.setObjectName("pageSubtitle")
        layout.addWidget(self.lbl_info)

        # Tabla de eventos recientes (solo lectura)
        self.tabla = QTableWidget()
        self.tabla.setColumnCount(3)
        self.tabla.setHorizontalHeaderLabels(["Fecha", "Tipo", "Resumen"])
        self.tabla.verticalHeader().setVisible(False)
        self.tabla.setEditTriggers(QTableWidget.NoEditTriggers)
        self.tabla.setSelectionBehavior(QTableWidget.SelectRows)
        self.tabla.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.tabla.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.tabla.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        layout.addWidget(self.tabla)

        # Botón borrar
        self.btn_borrar = QPushButton("Eliminar bodega de prueba (este código)")
        self.btn_borrar.setProperty("variant", "danger")
        self.btn_borrar.setEnabled(False)
        self.btn_borrar.setToolTip("Borra solo los datos de este código en la nube. Pide doble confirmación.")
        self.btn_borrar.clicked.connect(self.confirmar_borrado)
        layout.addWidget(self.btn_borrar)

        hint = QLabel("Nota: El borrado es por `negocio_id` derivado del código. Otras bodegas no se tocan. No se modifica el bot de Telegram.")
        hint.setObjectName("pageSubtitle")
        hint.setWordWrap(True)
        layout.addWidget(hint)

    def buscar(self):
        codigo = self.input_codigo.text().strip()
        if not codigo:
            QMessageBox.warning(self, "Código requerido", "Escribe un código, ej: MOBIL-6541")
            return
        uuid = _to_uuid(codigo)
        self.lbl_info.setText(f"Buscando: {codigo} → {uuid} ...")
        self.tabla.setRowCount(0)
        try:
            # Contar eventos y traer últimos 5
            url = f"{SUPABASE_URL}/rest/v1/kiosko_sync_events?negocio_id=eq.{uuid}&select=id,tipo,creado_en,datos&order=creado_en.desc&limit=5"
            req = urllib.request.Request(url, headers={
                "apikey": SUPABASE_KEY,
                "Authorization": f"Bearer {SUPABASE_KEY}",
                "Accept": "application/json"
            })
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read().decode("utf-8"))
            if not data:
                self.lbl_info.setText(f"Sin datos para {codigo} ({uuid}). Puede ser código inexistente o sin sincronización.")
                self.btn_borrar.setEnabled(True)
                self.btn_borrar.setProperty("codigo_actual", codigo)
                self.btn_borrar.setProperty("uuid_actual", uuid)
                return
            self.lbl_info.setText(f"Encontrados {len(data)} eventos recientes para {codigo}. Total en esta vista: {len(data)} (muestra 5).")
            for row in data:
                r = self.tabla.rowCount()
                self.tabla.insertRow(r)
                self.tabla.setItem(r, 0, QTableWidgetItem(str(row.get("creado_en",""))[:19]))
                self.tabla.setItem(r, 1, QTableWidgetItem(str(row.get("tipo",""))))
                datos = row.get("datos")
                if isinstance(datos, dict):
                    resumen = datos.get("nombre_negocio") or datos.get("numero_factura") or str(datos)[:60]
                else:
                    resumen = str(datos)[:60]
                self.tabla.setItem(r, 2, QTableWidgetItem(resumen))
            self.btn_borrar.setEnabled(True)
            self.btn_borrar.setProperty("codigo_actual", codigo)
            self.btn_borrar.setProperty("uuid_actual", uuid)
        except urllib.error.HTTPError as e:
            body = e.read().decode("utf-8", errors="ignore")[:300] if hasattr(e, 'read') else str(e)
            self.lbl_info.setText(f"Error consultando Supabase ({e.code}): {body}. Verifica SUPABASE_URL/KEY en .env")
            self.btn_borrar.setEnabled(False)
        except Exception as e:
            self.lbl_info.setText(f"Error: {e}")
            self.btn_borrar.setEnabled(False)

    def confirmar_borrado(self):
        codigo = self.btn_borrar.property("codigo_actual") or self.input_codigo.text().strip()
        uuid = self.btn_borrar.property("uuid_actual") or _to_uuid(codigo)
        if not codigo:
            return
        # Doble confirmación
        ok1 = QMessageBox.warning(self, "Confirmar borrado", f"¿Seguro que quieres borrar TODOS los datos de la bodega de prueba\n\n{codigo} → {uuid}\n\nEsto borrará sus eventos de sincronización en la nube. Otras bodegas NO se tocan.", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if ok1 != QMessageBox.Yes:
            return
        texto, ok = QInputDialog.getText(self, "Escribe el código para confirmar", f"Escribe exactamente: {codigo}")
        if not ok or texto.strip() != codigo:
            QMessageBox.information(self, "Cancelado", "El código no coincide. No se borró nada.")
            return
        # Intentar borrado remoto
        try:
            url = f"{SUPABASE_URL}/rest/v1/kiosko_sync_events?negocio_id=eq.{uuid}"
            req = urllib.request.Request(url, method="DELETE", headers={
                "apikey": SUPABASE_KEY,
                "Authorization": f"Bearer {SUPABASE_KEY}",
            })
            with urllib.request.urlopen(req, timeout=15) as resp:
                pass
            QMessageBox.information(self, "Borrado solicitado", f"Se envió el borrado de {codigo} a Supabase.\n\nSi tu clave es publishable y RLS lo permite, ya no aparecerá. Si RLS lo bloqueó, borra manual en Supabase Dashboard > kiosko_sync_events con negocio_id = {uuid}\n\nNo se tocó el bot de licencias.")
            self.tabla.setRowCount(0)
            self.lbl_info.setText(f"Borrado solicitado para {codigo}. Verifica buscando de nuevo.")
        except urllib.error.HTTPError as e:
            body = e.read().decode("utf-8", errors="ignore")[:400] if hasattr(e, 'read') else str(e)
            QMessageBox.critical(self, "No se pudo borrar remoto", f"Supabase respondió {e.code}:\n{body}\n\nPosible causa: RLS bloquea DELETE con clave publishable. Borra manual en Supabase Dashboard con:\nDELETE FROM kiosko_sync_events WHERE negocio_id = '{uuid}';\n\nNo se dañó ninguna otra bodega.")
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))
