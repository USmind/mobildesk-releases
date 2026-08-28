from PySide6.QtCore import Qt, QTimer, QThread, Signal, QDateTime
from PySide6.QtWidgets import (
    QMainWindow,
    QWidget,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QHBoxLayout,
    QFrame,
    QMessageBox,
    QDialog,
    QTableWidget,
    QTableWidgetItem,
    QLineEdit,
    QComboBox,
    QFormLayout,
    QHeaderView,
    QGridLayout,
    QStackedWidget,
    QScrollArea,
)
from modules.usuarios.session import get_user
from modules.usuarios.user_service import get_users, create_user, user_exists, update_user, delete_user
from modules.inventario.inventory_service import get_low_stock_products
from modules.ventas.sales_service import get_sales_summary
from modules.configuracion.business_service import get_business_settings
from ui.windows.inventory_window import InventoryWindow, UnifiedInventoryWindow
from ui.windows.exchange_rate._window import ExchangeRateWindow
from ui.windows.sales_window import SalesWindow
from ui.windows.sync_window import SyncWindow
from ui.windows.cash_window import CashWindow
from ui.windows.reports_window import ReportsWindow
from ui.windows.business_settings_window import BusinessSettingsWindow
from ui.windows.fiados_window import FiadosWindow
from ui.windows.license_window import LicenseWindow
from ui.windows.manual_window import ManualWindow
from ui.windows.welcome_tour_dialog import WelcomeTourDialog
from modules.licencia.license_service import init_or_get_license_info
from modules.sync.sync_service import is_configured, sync_now
from modules.actualizador import BackgroundUpdateWorker, apply_update_and_restart, CURRENT_VERSION


class BackgroundSyncWorker(QThread):
    finished_signal = Signal(dict)

    def run(self):
        try:
            res = sync_now()
            self.finished_signal.emit(res)
        except Exception:
            pass


class DashboardWindow(QMainWindow):
    def __init__(self, mostrar_tour_inicial=False):
        super().__init__()
        self.usuario = get_user() or {"id": 1, "nombre": "Administrador", "username": "admin", "role": "admin"}
        self.biz_settings = get_business_settings()
        self.nombre_negocio = self.biz_settings.get("nombre_negocio", "MobilDesk")
        self.setWindowTitle(f"{self.nombre_negocio} - Sistema de Ventas e Inventario")
        self.resize(1400, 900)
        self.setMinimumSize(950, 600)
        self.bg_worker = None
        self.update_worker = None
        self.btn_update_badge = None
        self.module_views = {}
        self.sidebar_buttons = {}

        self.crear_interfaz()
        self.showMaximized()

        if mostrar_tour_inicial:
            QTimer.singleShot(500, lambda: WelcomeTourDialog(self, self.nombre_negocio).exec())

        # Iniciar comprobación silenciosa de actualizaciones en segundo plano
        QTimer.singleShot(7000, self.iniciar_verificacion_actualizacion)

        self.sync_timer = QTimer(self)
        self.sync_timer.setInterval(20000)
        self.sync_timer.timeout.connect(self.sincronizar_en_segundo_plano)
        self.sync_timer.start()

    def iniciar_verificacion_actualizacion(self):
        try:
            self.update_worker = BackgroundUpdateWorker()
            self.update_worker.update_ready_signal.connect(self._on_update_ready)
            self.update_worker.start()
        except Exception:
            pass

    def _on_update_ready(self, version, installer_path, changelog):
        if not hasattr(self, "header_pos") or not self.header_pos:
            return

        if self.btn_update_badge is not None:
            return

        self.btn_update_badge = QPushButton(f"🚀 ¡Actualización v{version} lista!")
        self.btn_update_badge.setStyleSheet("""
            QPushButton {
                background: #16a34a;
                color: #ffffff;
                font-size: 13px;
                font-weight: 800;
                padding: 6px 14px;
                border-radius: 8px;
                border: none;
            }
            QPushButton:hover {
                background: #15803d;
            }
        """)
        self.btn_update_badge.clicked.connect(lambda: self.preguntar_y_aplicar_actualizacion(version, installer_path, changelog))
        self.header_pos.insertWidget(self.header_pos.count() - 1, self.btn_update_badge)

    def preguntar_y_aplicar_actualizacion(self, version, installer_path, changelog):
        msg = QMessageBox(self)
        msg.setWindowTitle(f"Actualización Disponible (v{version})")
        msg.setIcon(QMessageBox.Information)
        msg.setText(
            f"<h3>🚀 ¡Nueva versión de MobilDesk POS lista para instalar!</h3>"
            f"<p><b>Versión disponible:</b> v{version} (Actual: v{CURRENT_VERSION})</p>"
            f"<p><b>Novedades / Mejoras:</b><br>{changelog}</p>"
            f"<hr>"
            f"<p>¿Deseas reiniciar y aplicar la actualización ahora mismo?<br>"
            f"El sistema se cerrará, se actualizará en 10 segundos y se volverá a abrir solo.<br>"
            f"<b>Todos tus productos, ventas y configuraciones se conservarán 100% intactos.</b></p>"
        )
        btn_si = msg.addButton("🚀 Sí, Actualizar Ahora (10s)", QMessageBox.YesRole)
        btn_si.setStyleSheet("background-color: #16a34a; color: white; font-weight: 800; padding: 9px 20px; border-radius: 8px; border: none;")
        btn_no = msg.addButton("Más Tarde", QMessageBox.NoRole)
        btn_no.setStyleSheet("background-color: #f1f5f9; color: #1e293b; border: 1.5px solid #cbd5e1; font-weight: 700; padding: 9px 18px; border-radius: 8px;")

        msg.exec()
        if msg.clickedButton() == btn_si:
            ok = apply_update_and_restart(installer_path)
            if ok:
                from PySide6.QtWidgets import QApplication
                QApplication.quit()

    def sincronizar_en_segundo_plano(self):
        if not is_configured():
            return
        if self.bg_worker and self.bg_worker.isRunning():
            return
        self.bg_worker = BackgroundSyncWorker()
        self.bg_worker.finished_signal.connect(self._on_bg_sync_completed)
        self.bg_worker.start()

    def _on_bg_sync_completed(self, result):
        if result and (result.get("received") or result.get("sent")):
            self.actualizar_pantalla_completa()

    def actualizar_pantalla_completa(self):
        biz = get_business_settings()
        if biz.get("nombre_negocio") and biz.get("nombre_negocio") != self.nombre_negocio:
            self.actualizar_nombre_negocio(biz.get("nombre_negocio"))
        self.actualizar_productos_venta()
        self.actualizar_resumen_header()

    def actualizar_nombre_negocio(self, nuevo_nombre):
        self.nombre_negocio = nuevo_nombre
        self.setWindowTitle(f"{self.nombre_negocio} - Sistema de Ventas e Inventario")
        self.brand_label.setText(f"{self.nombre_negocio.upper()}\n\n{self.usuario['nombre']}")

    def actualizar_resumen_header(self):
        if hasattr(self, "resumen_hoy_label") and self.resumen_hoy_label:
            summary = get_sales_summary(self.usuario["id"] if self.usuario["role"] == "vendedor" else None)
            self.resumen_hoy_label.setText(f"Hoy: {summary['cantidad_ventas']} ventas | Bs {float(summary['total_bs']):,.2f}")

    def crear_interfaz(self):
        # Estilo Global Limpio sin bordes en etiquetas
        self.setStyleSheet("""
            QMainWindow { background-color: #f8fafc; }
            QLabel { border: none; background: transparent; color: #1e293b; }
            QFrame { border: none; }
        """)

        root = QWidget()
        layout = QHBoxLayout(root)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # ----------------------------------------------------
        # SIDEBAR IZQUIERDA
        # ----------------------------------------------------
        self.menu_frame = QFrame()
        self.menu_frame.setFixedWidth(240)
        self.menu_frame.setStyleSheet("""
            QFrame { background-color: #0f172a; }
            QLabel { color: #ffffff; border: none; background: transparent; }
            QPushButton {
                background: transparent;
                color: #cbd5e1;
                text-align: left;
                border-radius: 9px;
                font-size: 13.5px;
                padding: 11px 14px;
                font-weight: 600;
                border: none;
            }
            QPushButton:hover {
                background: rgba(148, 163, 184, 0.12);
                color: #ffffff;
            }
            QPushButton[active="true"] {
                background: #2563eb;
                color: #ffffff;
                font-weight: 700;
            }
            QPushButton:focus { outline: none; }
        """)

        self.side_layout = QVBoxLayout(self.menu_frame)
        self.side_layout.setContentsMargins(12, 18, 12, 16)
        self.side_layout.setSpacing(4)

        self.brand_label = QLabel(f"{self.nombre_negocio.upper()}\n\n{self.usuario['nombre']}")
        self.brand_label.setAlignment(Qt.AlignCenter)
        self.brand_label.setStyleSheet("font-size: 14px; font-weight: 800; padding: 10px 8px 14px 8px; color: #ffffff; border: none; letter-spacing: 0.4px;")
        self.side_layout.addWidget(self.brand_label)

        separador_side = QFrame()
        separador_side.setFixedHeight(1)
        separador_side.setStyleSheet("background-color: rgba(148, 163, 184, 0.25); border: none;")
        self.side_layout.addWidget(separador_side)

        sep_spacer = QWidget()
        sep_spacer.setFixedHeight(8)
        sep_spacer.setStyleSheet("background: transparent;")
        self.side_layout.addWidget(sep_spacer)

        self.side_btn_container = QVBoxLayout()
        self.side_btn_container.setSpacing(6)
        self.side_layout.addLayout(self.side_btn_container)

        self.side_layout.addStretch()

        firma = QLabel("MobilDesk POS\nMulti-Dispositivo")
        firma.setAlignment(Qt.AlignCenter)
        firma.setStyleSheet("font-size: 11px; color: #64748b; padding: 8px; border: none;")
        self.side_layout.addWidget(firma)

        layout.addWidget(self.menu_frame)

        # ----------------------------------------------------
        # ÁREA CENTRAL (QStackedWidget para navegación integrada)
        # ----------------------------------------------------
        self.content_stack = QStackedWidget()
        self.content_stack.setStyleSheet("background-color: #f8fafc;")
        layout.addWidget(self.content_stack, 1)

        self.setCentralWidget(root)

        # Construir botones del sidebar y primera página (Inicio / POS)
        self.reconstruir_sidebar()
        self.crear_pagina_inicio()
        self.mostrar_inicio()

    def reconstruir_sidebar(self):
        # Limpiar botones anteriores
        while self.side_btn_container.count():
            item = self.side_btn_container.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        self.sidebar_buttons.clear()

        lic_info = init_or_get_license_info()
        es_vitalicio = (lic_info.get("estado") == "vitalicio" or lic_info.get("plan_activo") == "vitalicio")

        if self.usuario["role"] == "admin":
            buttons_def = [
                ("🏠 Inicio (Ventas)", "Inicio"),
                ("🧾 Historial de Ventas", "Historial"),
                ("📦 Inventario y Productos", "Inventario"),
                ("💵 Caja y Turnos", "Caja"),
                ("👥 Fiados / Créditos", "Fiados"),
                ("📊 Reportes Financieros", "Reportes"),
                ("👤 Usuarios y Roles", "Usuarios"),
                ("💲 Tasa USD/Bs", "Tasa USD/Bs"),
                ("⚙️ Configurar Negocio", "Configurar Negocio"),
                ("☁️ Sincronización", "Sincronización"),
                ("📖 Manual y Ayuda", "Manual"),
            ]
            if not es_vitalicio:
                buttons_def.append(("🔑 Activar Licencia", "Licencia"))
        else:
            buttons_def = [
                ("🏠 Inicio (Ventas)", "Inicio"),
                ("🧾 Historial de Ventas", "Historial"),
                ("💵 Mi Caja", "Caja"),
                ("👥 Fiados / Créditos", "Fiados"),
                ("📊 Mis Ventas", "Mis ventas"),
                ("📖 Manual y Ayuda", "Manual"),
            ]

        for label_text, mod_name in buttons_def:
            btn = QPushButton(label_text)
            btn.setMinimumHeight(40)
            btn.setProperty("active", "false")
            btn.clicked.connect(lambda checked=False, val=mod_name: self.abrir_modulo(val))
            self.side_btn_container.addWidget(btn)
            self.sidebar_buttons[mod_name] = btn

    def _set_active_sidebar_button(self, active_mod):
        for mod, btn in self.sidebar_buttons.items():
            is_active = (mod == active_mod)
            btn.setProperty("active", "true" if is_active else "false")
            btn.style().unpolish(btn)
            btn.style().polish(btn)

    def crear_pagina_inicio(self):
        self.page_pos = QWidget()
        page_layout = QVBoxLayout(self.page_pos)
        page_layout.setContentsMargins(24, 18, 24, 18)
        page_layout.setSpacing(12)

        # Header Superior del POS
        self.header_pos = QHBoxLayout()
        self.header_pos.setSpacing(10)

        self.pos_title_lbl = QLabel(f"Punto de Venta · {self.nombre_negocio}")
        self.pos_title_lbl.setStyleSheet("font-size: 22px; font-weight: 800; color: #0f172a; border: none;")
        self.header_pos.addWidget(self.pos_title_lbl)
        self.header_pos.addStretch()

        self.lic_badge_container = QHBoxLayout()
        self.header_pos.addLayout(self.lic_badge_container)

        self.resumen_hoy_label = QLabel("Hoy: 0 ventas | Bs 0.00")
        self.resumen_hoy_label.setStyleSheet("font-size: 14px; font-weight: 700; color: #1e3a8a; background: #dbeafe; padding: 6px 14px; border-radius: 8px; border: none;")
        self.resumen_hoy_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.header_pos.addWidget(self.resumen_hoy_label)

        # Reloj y Fecha en tiempo real
        self.lbl_reloj = QLabel()
        self.lbl_reloj.setStyleSheet("font-size: 13px; font-weight: 700; color: #0f766e; background: #ccfbf1; padding: 6px 12px; border-radius: 8px; border: 1px solid #99f6e4;")
        self.header_pos.addWidget(self.lbl_reloj)

        self.timer_reloj = QTimer(self)
        self.timer_reloj.timeout.connect(self._actualizar_reloj_header)
        self.timer_reloj.start(1000)
        self._actualizar_reloj_header()

        btn_ayuda = QPushButton("❓ Manual y Ayuda")
        btn_ayuda.setStyleSheet("""
            QPushButton {
                background: #ffffff;
                color: #1e3a8a;
                font-size: 13px;
                font-weight: 700;
                padding: 6px 14px;
                border-radius: 8px;
                border: 1.5px solid #cbd5e1;
            }
            QPushButton:hover {
                background: #f1f5f9;
                border-color: #2563eb;
            }
        """)
        btn_ayuda.clicked.connect(lambda: self.abrir_modulo("Manual"))
        self.header_pos.addWidget(btn_ayuda)

        page_layout.addLayout(self.header_pos)

        # Venta actual POS
        self.venta_actual = SalesWindow(self.usuario)
        self.venta_actual.sale_registered.connect(self.on_cambio_productos)
        self.venta_actual.setWindowFlags(Qt.Widget)
        page_layout.addWidget(self.venta_actual)

        self.content_stack.addWidget(self.page_pos)

    def _actualizar_reloj_header(self):
        if hasattr(self, "lbl_reloj") and self.lbl_reloj:
            ahora = QDateTime.currentDateTime()
            self.lbl_reloj.setText(f"🕒 {ahora.toString('hh:mm:ss ap · dd/MM/yyyy')}")

    def mostrar_inicio(self):
        lic_info = init_or_get_license_info()
        if lic_info.get("bloqueado", False):
            self.abrir_modulo("Licencia")
            return

        self._set_active_sidebar_button("Inicio")
        self.actualizar_resumen_header()

        # Actualizar badge de licencia si aplica
        while self.lic_badge_container.count():
            item = self.lic_badge_container.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if lic_info["estado"] == "demo":
            lbl_lic = QLabel(f"🎁 Demo ({lic_info['dias_restantes']}d restantes)")
            lbl_lic.setStyleSheet("background: #ffedd5; color: #c2410c; font-size: 12px; font-weight: 700; padding: 6px 12px; border-radius: 8px; border: none;")
            self.lic_badge_container.addWidget(lbl_lic)
            if self.usuario["role"] == "admin":
                btn_act = QPushButton("🔑 Activar")
                btn_act.setStyleSheet("background: #ea580c; color: white; font-size: 12px; padding: 6px 12px; border-radius: 8px; font-weight: 700; border: none;")
                btn_act.clicked.connect(lambda: self.abrir_modulo("Licencia"))
                self.lic_badge_container.addWidget(btn_act)

        self.content_stack.setCurrentWidget(self.page_pos)
        self.actualizar_productos_venta()

    def actualizar_productos_venta(self):
        if hasattr(self, "venta_actual") and self.venta_actual:
            self.venta_actual.cargar_productos()

    def on_cambio_productos(self):
        self.actualizar_pantalla_completa()
        self.sincronizar_en_segundo_plano()

    def on_licencia_actualizada(self):
        self.reconstruir_sidebar()
        self.mostrar_inicio()
        QMessageBox.information(self, "MobilDesk POS", "¡Licencia activada con éxito!")

    def abrir_modulo(self, name):
        lic_info = init_or_get_license_info()
        if lic_info.get("bloqueado", False) and name != "Licencia":
            QMessageBox.warning(
                self,
                "Período de Prueba Finalizado",
                "Tu período de prueba gratuita de 7 días ha finalizado.\n\n"
                "Para continuar utilizando MobilDesk POS, por favor ingresa tu clave de activación."
            )
            name = "Licencia"

        if name == "Inicio":
            self.mostrar_inicio()
            return

        self._set_active_sidebar_button(name)

        # Crear o actualizar vista embebida directa (sin barra superior redundante)
        if name not in self.module_views:
            child_widget = None
            if name in ("Inventario", "Productos"):
                child_widget = UnifiedInventoryWindow(self.usuario)
                child_widget.products_changed.connect(self.on_cambio_productos)
            elif name in ("Historial", "Historial de Ventas"):
                from ui.windows.sales_window import SalesHistoryWindow
                child_widget = SalesHistoryWindow(self)
            elif name == "Caja":
                child_widget = CashWindow(self.usuario)
            elif name == "Fiados":
                child_widget = FiadosWindow()
            elif name == "Reportes":
                child_widget = ReportsWindow(None)
            elif name == "Mis ventas":
                child_widget = ReportsWindow(self.usuario)
            elif name == "Usuarios":
                child_widget = UsersWindow()
            elif name == "Tasa USD/Bs":
                child_widget = ExchangeRateWindow(self.usuario)
                child_widget.rate_changed.connect(self.on_cambio_productos)
            elif name == "Configurar Negocio":
                child_widget = BusinessSettingsWindow()
                child_widget.settings_saved.connect(self.actualizar_pantalla_completa)
            elif name == "Sincronización":
                child_widget = SyncWindow()
            elif name == "Licencia":
                child_widget = LicenseWindow()
                child_widget.licencia_actualizada.connect(self.on_licencia_actualizada)
            elif name == "Manual":
                child_widget = ManualWindow(self, self.nombre_negocio)

            if child_widget:
                child_widget.setWindowFlags(Qt.Widget)
                self.module_views[name] = child_widget
                self.content_stack.addWidget(child_widget)

        child_widget = self.module_views.get(name)

        # Refrescar datos del módulo si tiene método de carga
        if child_widget:
            if hasattr(child_widget, "cargar_todo"):
                child_widget.cargar_todo()
            elif hasattr(child_widget, "actualizar_vista"):
                child_widget.actualizar_vista()
            elif hasattr(child_widget, "cargar_datos"):
                child_widget.cargar_datos()
            elif hasattr(child_widget, "cargar"):
                child_widget.cargar()

            self.content_stack.setCurrentWidget(child_widget)


class UsersWindow(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Gestión de Usuarios y Roles - MobilDesk")
        self.users_list = []
        self.crear_interfaz()
        self.cargar()

    def crear_interfaz(self):
        self.setStyleSheet("""
            QWidget { background: transparent; font-family: 'Segoe UI', sans-serif; }
            QLabel { color: #334155; font-size: 13px; font-weight: 600; border: none; background: transparent; }
            QLineEdit, QComboBox {
                background: white;
                border: 1.5px solid #cbd5e1;
                border-radius: 8px;
                padding: 8px 12px;
                font-size: 13.5px;
                min-height: 20px;
                color: #0f172a;
            }
            QLineEdit:focus, QComboBox:focus { border: 2px solid #2563eb; }
            QComboBox QAbstractItemView {
                background-color: #ffffff;
                color: #0f172a;
                selection-background-color: #2563eb;
                selection-color: #ffffff;
                border: 1.5px solid #cbd5e1;
                border-radius: 6px;
                padding: 4px;
                outline: none;
            }
            QComboBox QAbstractItemView::item {
                min-height: 28px;
                padding: 6px 10px;
                color: #0f172a;
                background-color: #ffffff;
            }
            QComboBox QAbstractItemView::item:selected, QComboBox QAbstractItemView::item:hover {
                background-color: #2563eb;
                color: #ffffff;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setSpacing(14)
        layout.setContentsMargins(10, 10, 10, 10)

        # Form Card (Crear Nuevo Usuario)
        card = QFrame()
        card.setStyleSheet("QFrame { background: transparent; border: none; }")
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(20, 18, 20, 18)
        card_layout.setSpacing(10)

        lbl_form = QLabel("Registrar Nuevo Usuario / Cajero:")
        lbl_form.setStyleSheet("font-size: 14px; font-weight: 700; color: #1e3a8a; border: none;")
        card_layout.addWidget(lbl_form)

        grid = QGridLayout()
        grid.setHorizontalSpacing(14)
        grid.setVerticalSpacing(8)

        # Fila 0 y 1: Nombre y Usuario
        lbl_n = QLabel("Nombre Completo:")
        grid.addWidget(lbl_n, 0, 0)
        self.name = QLineEdit()
        self.name.setPlaceholderText("Ej: Juan Pérez")
        grid.addWidget(self.name, 1, 0)

        lbl_u = QLabel("Nombre de Usuario (Login):")
        grid.addWidget(lbl_u, 0, 1)
        self.username = QLineEdit()
        self.username.setPlaceholderText("Ej: juan123")
        grid.addWidget(self.username, 1, 1)

        # Fila 2 y 3: Contraseña y Rol
        lbl_p = QLabel("Contraseña:")
        grid.addWidget(lbl_p, 2, 0)
        self.password = QLineEdit()
        self.password.setEchoMode(QLineEdit.Password)
        self.password.setPlaceholderText("••••••••")
        grid.addWidget(self.password, 3, 0)

        lbl_r = QLabel("Rol / Permisos:")
        grid.addWidget(lbl_r, 2, 1)
        self.role = QComboBox()
        self.role.addItem("Vendedor (Solo Ventas, Caja y Fiados)", "vendedor")
        self.role.addItem("Administrador (Control Total del Sistema)", "admin")
        grid.addWidget(self.role, 3, 1)

        card_layout.addLayout(grid)

        btn_save = QPushButton("➕ Crear Usuario")
        btn_save.setStyleSheet("""
            QPushButton {
                background: #2563eb;
                color: white;
                padding: 9px 20px;
                border-radius: 8px;
                font-weight: 700;
                border: none;
            }
            QPushButton:hover { background: #1d4ed8; }
        """)
        btn_save.clicked.connect(self.guardar)
        card_layout.addWidget(btn_save, 0, Qt.AlignRight)

        layout.addWidget(card)

        # Barra de Acciones para la Tabla
        acciones_layout = QHBoxLayout()
        acciones_layout.setSpacing(10)

        lbl_tabla_info = QLabel("Usuarios Registrados en el Sistema:")
        lbl_tabla_info.setStyleSheet("font-size: 14px; font-weight: 700; color: #0f172a;")
        acciones_layout.addWidget(lbl_tabla_info)
        acciones_layout.addStretch()

        btn_editar = QPushButton("✏️ Editar Usuario")
        btn_editar.setStyleSheet("""
            QPushButton {
                background: #f8fafc;
                color: #1e293b;
                border: 1.5px solid #cbd5e1;
                padding: 8px 16px;
                border-radius: 8px;
                font-weight: 700;
            }
            QPushButton:hover { background: #e2e8f0; }
        """)
        btn_editar.clicked.connect(self.editar_usuario)
        acciones_layout.addWidget(btn_editar)

        btn_eliminar = QPushButton("🗑️ Eliminar Usuario")
        btn_eliminar.setStyleSheet("""
            QPushButton {
                background: #fef2f2;
                color: #dc2626;
                border: 1.5px solid #fca5a5;
                padding: 8px 16px;
                border-radius: 8px;
                font-weight: 700;
            }
            QPushButton:hover { background: #fee2e2; }
        """)
        btn_eliminar.clicked.connect(self.eliminar_usuario)
        acciones_layout.addWidget(btn_eliminar)

        layout.addLayout(acciones_layout)

        # Tabla
        self.table = QTableWidget()
        self.table.verticalHeader().setVisible(False)
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["ID", "Nombre Completo", "Usuario", "Rol", "Fecha de Creación"])
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.SingleSelection)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setStyleSheet("""
            QTableWidget { background: white; border: 1px solid #cbd5e1; border-radius: 10px; gridline-color: #f1f5f9; }
            QHeaderView::section { background: #f8fafc; color: #475569; font-weight: 700; border: none; padding: 8px; }
        """)
        self.table.doubleClicked.connect(self.editar_usuario)
        layout.addWidget(self.table)

    def cargar(self):
        self.users_list = get_users()
        self.table.setRowCount(len(self.users_list))
        for row, user in enumerate(self.users_list):
            for column, value in enumerate([
                user["id"],
                user["nombre"],
                user["username"],
                "Administrador" if user["role"] == "admin" else "Vendedor",
                user["fecha_creacion"],
            ]):
                item = QTableWidgetItem(str(value))
                if column in (0, 3):
                    item.setTextAlignment(Qt.AlignCenter)
                self.table.setItem(row, column, item)

    def usuario_seleccionado(self):
        row = self.table.currentRow()
        if row < 0 or row >= len(self.users_list):
            QMessageBox.warning(self, "Aviso", "Seleccione un usuario de la tabla.")
            return None
        return self.users_list[row]

    def guardar(self):
        try:
            nombre = self.name.text().strip()
            username = self.username.text().strip()
            password = self.password.text().strip()
            rol = self.role.currentData() or "vendedor"

            if not nombre or not username or not password:
                raise ValueError("Todos los campos son obligatorios.")

            if user_exists(username):
                raise ValueError("Ese nombre de usuario ya está registrado.")

            create_user(nombre, username, password, rol)
            self.name.clear()
            self.username.clear()
            self.password.clear()
            self.cargar()
            QMessageBox.information(self, "Usuarios", f"Usuario '{nombre}' creado exitosamente.")
        except ValueError as error:
            QMessageBox.warning(self, "Usuarios", str(error))
        except Exception as error:
            QMessageBox.critical(self, "Usuarios", str(error))

    def editar_usuario(self):
        user = self.usuario_seleccionado()
        if not user:
            return

        dialog = QDialog(self)
        dialog.setWindowTitle(f"Editar Usuario: {user['nombre']}")
        dialog.resize(440, 360)
        dialog.setStyleSheet("""
            QDialog { background-color: #f8fafc; font-family: 'Segoe UI', sans-serif; }
            QLabel { color: #1e293b; font-weight: 600; font-size: 13px; }
            QLineEdit, QComboBox {
                background: white;
                border: 1.5px solid #cbd5e1;
                border-radius: 8px;
                padding: 8px 12px;
                font-size: 13.5px;
                color: #0f172a;
            }
            QLineEdit:focus, QComboBox:focus { border: 2px solid #2563eb; }
            QComboBox QAbstractItemView {
                background-color: #ffffff;
                color: #0f172a;
                selection-background-color: #2563eb;
                selection-color: #ffffff;
                border: 1.5px solid #cbd5e1;
                border-radius: 6px;
                padding: 4px;
                outline: none;
            }
            QComboBox QAbstractItemView::item {
                min-height: 28px;
                padding: 6px 10px;
                color: #0f172a;
                background-color: #ffffff;
            }
            QComboBox QAbstractItemView::item:selected, QComboBox QAbstractItemView::item:hover {
                background-color: #2563eb;
                color: #ffffff;
            }
        """)

        d_layout = QVBoxLayout(dialog)
        d_layout.setSpacing(12)
        d_layout.setContentsMargins(20, 20, 20, 20)

        lbl_t = QLabel(f"✏️ Modificar Datos de Cuenta")
        lbl_t.setStyleSheet("font-size: 16px; font-weight: 800; color: #1e3a8a;")
        d_layout.addWidget(lbl_t)

        form = QFormLayout()
        form.setSpacing(10)

        txt_nombre = QLineEdit(user["nombre"])
        txt_username = QLineEdit(user["username"])

        cb_role = QComboBox()
        cb_role.addItem("Vendedor (Solo Ventas, Caja y Fiados)", "vendedor")
        cb_role.addItem("Administrador (Control Total del Sistema)", "admin")
        if user["role"] == "admin":
            cb_role.setCurrentIndex(1)
        else:
            cb_role.setCurrentIndex(0)

        txt_password = QLineEdit()
        txt_password.setEchoMode(QLineEdit.Password)
        txt_password.setPlaceholderText("Dejar en blanco para no cambiarla")

        form.addRow("Nombre Completo:", txt_nombre)
        form.addRow("Nombre de Usuario:", txt_username)
        form.addRow("Rol / Permisos:", cb_role)
        form.addRow("Nueva Contraseña:", txt_password)

        d_layout.addLayout(form)
        d_layout.addSpacing(10)

        btn_box = QHBoxLayout()
        btn_box.setSpacing(10)

        btn_cancel = QPushButton("Cancelar")
        btn_cancel.setStyleSheet("""
            QPushButton {
                background: #f1f5f9;
                color: #334155;
                border: 1.5px solid #cbd5e1;
                padding: 8px 18px;
                border-radius: 8px;
                font-weight: 700;
            }
            QPushButton:hover { background: #e2e8f0; }
        """)
        btn_cancel.clicked.connect(dialog.reject)

        btn_ok = QPushButton("💾 Guardar Cambios")
        btn_ok.setStyleSheet("""
            QPushButton {
                background: #2563eb;
                color: white;
                padding: 8px 22px;
                border-radius: 8px;
                font-weight: 700;
                border: none;
            }
            QPushButton:hover { background: #1d4ed8; }
        """)

        def on_save():
            try:
                nom = txt_nombre.text().strip()
                usr = txt_username.text().strip()
                rol = cb_role.currentData()
                pwd = txt_password.text().strip()

                if not nom or not usr:
                    raise ValueError("Nombre y Usuario no pueden estar vacíos.")

                update_user(user["id"], nom, usr, rol, pwd if pwd else None)
                self.cargar()
                dialog.accept()
                QMessageBox.information(self, "Usuario Actualizado", f"Los datos de '{nom}' han sido actualizados exitosamente.")
            except ValueError as ve:
                QMessageBox.warning(dialog, "Aviso", str(ve))
            except Exception as ex:
                QMessageBox.critical(dialog, "Error", str(ex))

        btn_ok.clicked.connect(on_save)

        btn_box.addStretch()
        btn_box.addWidget(btn_cancel)
        btn_box.addWidget(btn_ok)
        d_layout.addLayout(btn_box)

        dialog.exec()

    def eliminar_usuario(self):
        user = self.usuario_seleccionado()
        if not user:
            return

        msg = QMessageBox(self)
        msg.setWindowTitle("Confirmar Eliminación de Usuario")
        msg.setIcon(QMessageBox.Warning)
        msg.setText(
            f"¿Está seguro de que desea eliminar al usuario:\n\n"
            f"• <b>Nombre:</b> {user['nombre']}\n"
            f"• <b>Usuario:</b> @{user['username']}\n"
            f"• <b>Rol:</b> {'Administrador' if user['role'] == 'admin' else 'Vendedor'}\n\n"
            f"Esta acción no se puede deshacer."
        )

        btn_eliminar = msg.addButton("🗑️ Sí, Eliminar", QMessageBox.YesRole)
        btn_eliminar.setStyleSheet("background-color: #dc2626; color: white; font-weight: 700; padding: 8px 18px; border-radius: 7px; border: none;")
        btn_cancelar = msg.addButton("Cancelar", QMessageBox.NoRole)
        btn_cancelar.setStyleSheet("background-color: #f1f5f9; color: #1e293b; border: 1.5px solid #cbd5e1; font-weight: 700; padding: 8px 18px; border-radius: 7px;")

        msg.exec()

        if msg.clickedButton() == btn_eliminar:
            try:
                delete_user(user["id"])
                self.cargar()
                QMessageBox.information(self, "Usuario Eliminado", f"El usuario '{user['nombre']}' fue eliminado exitosamente.")
            except ValueError as ve:
                QMessageBox.warning(self, "Aviso", str(ve))
            except Exception as ex:
                QMessageBox.critical(self, "Error", str(ex))
