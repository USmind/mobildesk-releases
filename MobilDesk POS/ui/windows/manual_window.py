from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QFrame,
    QLineEdit,
    QTabWidget
)
from PySide6.QtCore import Qt
from ui.windows.welcome_tour_dialog import WelcomeTourDialog


class ManualWindow(QWidget):
    def __init__(self, parent=None, nombre_negocio="MobilDesk"):
        super().__init__(parent)
        self.nombre_negocio = nombre_negocio
        self.setWindowTitle("Manual de Usuario y Centro de Ayuda - MobilDesk POS")
        self.crear_interfaz()

    def crear_interfaz(self):
        self.setStyleSheet("""
            QWidget {
                font-family: 'Segoe UI', sans-serif;
                background-color: transparent;
            }
            QLabel {
                color: #1e293b;
                border: none;
                background: transparent;
            }
            QScrollArea {
                border: none;
                background: transparent;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 18, 20, 18)
        layout.setSpacing(14)

        # Header superior del Centro de Ayuda
        header_card = QFrame()
        header_card.setStyleSheet("""
            QFrame {
                background-color: #1e3a8a;
                border-radius: 14px;
                border: none;
            }
        """)
        h_layout = QHBoxLayout(header_card)
        h_layout.setContentsMargins(24, 18, 24, 18)
        h_layout.setSpacing(16)

        t_col = QVBoxLayout()
        t_col.setSpacing(4)
        lbl_t = QLabel("📖 Manual de Usuario y Guía Interactiva")
        lbl_t.setStyleSheet("font-size: 22px; font-weight: 800; color: #ffffff; background: transparent; border: none;")
        lbl_sub = QLabel(f"Centro de ayuda oficial de {self.nombre_negocio} POS: aprende a dominar cada función en minutos.")
        lbl_sub.setStyleSheet("font-size: 13.5px; color: #dbeafe; background: transparent; border: none; font-weight: 500;")
        t_col.addWidget(lbl_t)
        t_col.addWidget(lbl_sub)
        h_layout.addLayout(t_col, 1)

        btn_tour = QPushButton("▶️ Ver Introducción Guiada (Tour)")
        btn_tour.setStyleSheet("""
            QPushButton {
                background: #ffffff;
                color: #1e3a8a;
                font-size: 13.5px;
                font-weight: 700;
                padding: 10px 20px;
                border-radius: 8px;
                border: none;
            }
            QPushButton:hover {
                background: #f1f5f9;
            }
        """)
        btn_tour.clicked.connect(self.abrir_tour_bienvenida)
        h_layout.addWidget(btn_tour)

        layout.addWidget(header_card)

        # Tabs de Categorías
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #cbd5e1;
                border-radius: 12px;
                background: #ffffff;
                top: -1px;
            }
            QTabBar::tab {
                background: #f1f5f9;
                color: #475569;
                font-weight: 700;
                font-size: 13.5px;
                padding: 10px 18px;
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
                margin-right: 4px;
                border: 1px solid #cbd5e1;
                border-bottom: none;
            }
            QTabBar::tab:selected {
                background: #ffffff;
                color: #2563eb;
                border-bottom: 2px solid #2563eb;
            }
            QTabBar::tab:hover:!selected {
                background: #e2e8f0;
                color: #1e293b;
            }
        """)

        self.tabs.addTab(self._tab_ventas(), "🛒 Punto de Venta")
        self.tabs.addTab(self._tab_inventario(), "📦 Inventario y Precios")
        self.tabs.addTab(self._tab_tasa(), "💲 Tasa USD/Bs")
        self.tabs.addTab(self._tab_fiados(), "👥 Fiados y Créditos")
        self.tabs.addTab(self._tab_usuarios(), "👤 Usuarios y Roles")
        self.tabs.addTab(self._tab_caja_reportes(), "💵 Caja y Reportes")
        self.tabs.addTab(self._tab_movil(), "📱 App Móvil y Multi-Teléfonos")
        self.tabs.addTab(self._tab_actualizaciones(), "🚀 Actualizaciones Automáticas")

        layout.addWidget(self.tabs, 1)

    def abrir_tour_bienvenida(self):
        tour = WelcomeTourDialog(self, self.nombre_negocio)
        tour.exec()

    def _crear_scroll_tab(self, widgets_list):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        container = QWidget()
        c_layout = QVBoxLayout(container)
        c_layout.setContentsMargins(24, 20, 24, 20)
        c_layout.setSpacing(16)

        for w in widgets_list:
            c_layout.addWidget(w)

        c_layout.addStretch()
        scroll.setWidget(container)
        return scroll

    def _crear_card_seccion(self, titulo, descripcion, pasos):
        card = QFrame()
        card.setStyleSheet("QFrame { background: #f8fafc; border: 1.5px solid #e2e8f0; border-radius: 12px; }")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(10)

        t_lbl = QLabel(titulo)
        t_lbl.setStyleSheet("font-size: 16px; font-weight: 800; color: #1e3a8a; border: none;")
        layout.addWidget(t_lbl)

        if descripcion:
            d_lbl = QLabel(descripcion)
            d_lbl.setStyleSheet("font-size: 13.5px; color: #475569; border: none;")
            d_lbl.setWordWrap(True)
            layout.addWidget(d_lbl)

        for num, texto in pasos:
            row = QHBoxLayout()
            row.setSpacing(10)
            n_lbl = QLabel(f"•")
            n_lbl.setStyleSheet("font-size: 16px; font-weight: 800; color: #2563eb; border: none;")
            tx_lbl = QLabel(f"<b>{num}:</b> {texto}" if num else texto)
            tx_lbl.setStyleSheet("font-size: 13.5px; color: #1e293b; border: none;")
            tx_lbl.setWordWrap(True)
            row.addWidget(n_lbl)
            row.addWidget(tx_lbl, 1)
            layout.addLayout(row)

        return card

    def _tab_ventas(self):
        return self._crear_scroll_tab([
            self._crear_card_seccion(
                "🛒 ¿Cómo realizar una venta rápida?",
                "El punto de venta está optimizado para cobrar con teclado o lector de código de barras.",
                [
                    ("1. Buscar Producto", "Escribe el nombre o código de barras en el campo 'Producto'. Al escribir verás sugerencias automáticas con su precio en Bolívares y en Dólares entre paréntesis (ej: <code>P000001 - Chocolate · 300.00 Bs. (1.50$)</code>)."),
                    ("2. Cantidad", "Indica cuántas unidades desea el cliente y pulsa <b>'Agregar Producto'</b> o presiona <b>Enter</b>."),
                    ("3. Método de Pago", "Selecciona Efectivo, Divisas ($ USD), Pago Móvil, Tarjeta / Débito, Fiado o <b>Pago Mixto / Fraccionado</b>."),
                    ("4. Cálculo de Vuelto", "Al cobrar en Efectivo o Divisas, escribe el monto entregado por el cliente y el sistema calculará el vuelto exacto automáticamente."),
                    ("5. Finalizar Venta", "Pulsa <b>'✅ Registrar Venta'</b>. Al instante podrás ver o imprimir el ticket térmico (58mm o 80mm).")
                ]
            ),
            self._crear_card_seccion(
                "🔀 ¿Cómo usar Pagos Mixtos y Fraccionados?",
                "Permite cobrar una sola venta combinando diferentes formas de pago (ej: una parte en divisas, otra en pago móvil y otra en efectivo):",
                [
                    ("Seleccionar Método", "Elige en el menú de pago la opción <b>'🔀 Pago Mixto / Fraccionado'</b>."),
                    ("Configurar Desglose", "Pulsa <b>'⚙️ Configurar Desglose'</b> o directamente <b>'Registrar Venta'</b> para abrir la ventana de pago."),
                    ("Ingresar Montos", "Escribe los montos entregados en cada forma de pago (Divisas $, Efectivo Bs, Pago Móvil, Tarjeta o Fiado). El sistema convertirá las divisas a Bolívares al instante según la tasa actual."),
                    ("Indicador en Tiempo Real", "La pantalla te mostrará el Total Abonado, el Restante por Cobrar y el Vuelto exacto si entregaron de más."),
                    ("Confirmar", "Pulsa <b>'✅ Confirmar Pago Mixto'</b>. En el ticket impreso y en los reportes de caja saldrá el desglose exacto de cada forma de pago.")
                ]
            ),
            self._crear_card_seccion(
                "⚡ Atajos y Consejos de Facturación",
                "",
                [
                    ("Lectores de Barra", "Si tienes un lector USB o inalámbrico, simplemente escanea el código del producto y se agregará de inmediato."),
                    ("Eliminar Producto", "Si el cliente se arrepiente de llevar un artículo, selecciónalo en la tabla y pulsa <b>'🗑️ Eliminar Producto'</b>.")
                ]
            )
        ])

    def _tab_inventario(self):
        return self._crear_scroll_tab([
            self._crear_card_seccion(
                "📦 Gestión de Productos y Catálogo",
                "Administra todo tu inventario en un solo lugar con cálculo de stock en tiempo real.",
                [
                    ("➕ Nuevo Producto", "Registra un producto indicando Nombre, Marca, Unidad, Costo en USD y Margen de Ganancia (o Precio de Venta directo)."),
                    ("✏️ Modificar", "Edita el precio, nombre o datos de cualquier producto haciendo doble clic en la tabla o pulsando 'Modificar'."),
                    ("📥 Entrada de Stock", "Cuando recibas mercancía de proveedores, pulsa '📥 Entrada Stock', selecciona el producto y escribe la cantidad recibida para sumarla."),
                    ("⚖️ Ajuste de Stock", "Para registrar productos vencidos, dañados o cuadres de inventario, utiliza '⚖️ Ajuste Stock'. Permite sumar o restar existencias."),
                    ("📋 Historial", "Consulta el historial completo de entradas y salidas con fecha, hora, usuario responsable y motivo.")
                ]
            ),
            self._crear_card_seccion(
                "💡 Calculadora Inteligente de Precios y Ganancia",
                "El sistema te permite fijar tus precios con base en el costo y margen de ganancia:",
                [
                    ("Cálculo Automático", "Si compras un producto en $1.00 USD y seleccionas 30% de ganancia, el sistema fija automáticamente el precio en $1.30 USD y calcula su equivalente exacto en Bolívares según la tasa del día.")
                ]
            )
        ])

    def _tab_tasa(self):
        return self._crear_scroll_tab([
            self._crear_card_seccion(
                "💲 Configuración de la Tasa USD / Bs",
                "MobilDesk opera en modalidad multimoneda nativa (Dólares y Bolívares):",
                [
                    ("⚡ Recálculo Automático", "Al actualizar la tasa del dólar, <b>todos los precios de los productos y subtotales se recalculan al instante</b> en todo el sistema."),
                    ("💲 Actualizar Tasa", "Ingresa al módulo '💲 Tasa USD/Bs', escribe el nuevo valor (ej: <code>770.00</code>) y pulsa 'Guardar Tasa'."),
                    ("🪙 Botón Redondear", "Usa el botón 'Redondear' para ajustar la tasa a valores sin decimales si lo deseas."),
                    ("📱 Cambio desde el Teléfono", "También puedes tocar la tarjeta de tasa en la App Android para cambiarla desde tu celular en 3 segundos.")
                ]
            )
        ])

    def _tab_fiados(self):
        return self._crear_scroll_tab([
            self._crear_card_seccion(
                "👥 Control de Fiados y Cuentas por Cobrar",
                "Lleva el control de créditos a clientes sin libretas ni hojas sueltas:",
                [
                    ("1. Registrar Venta Fiada", "En el Punto de Venta, elige método <b>'Fiado / Crédito'</b>, escribe el nombre del cliente y su teléfono, y pulsa Registrar Venta."),
                    ("2. Consultar Deudores", "Entra al módulo <b>'👥 Fiados / Créditos'</b> para ver la lista de clientes con deuda, total adeudado y fecha."),
                    ("3. Registrar Abonos / Pagos", "Selecciona el cliente y pulsa el botón verde <b>'💵 Registrar Abono / Pago'</b>. Puedes usar los botones rápidos <b>[Pagar Todo 100%]</b>, <b>[Pagar la Mitad 50%]</b> o ingresar el monto exacto entregado."),
                    ("4. Historial de Abonos", "Pulsa '📋 Ver Historial de Abonos' para ver cada pago anterior con fecha y monto.")
                ]
            )
        ])

    def _tab_usuarios(self):
        return self._crear_scroll_tab([
            self._crear_card_seccion(
                "👤 Gestión de Usuarios y Permisos",
                "Controla quién tiene acceso a cada parte del sistema:",
                [
                    ("👑 Rol Administrador", "Acceso total a todos los módulos: Inventario, Configuración de Negocio, Tasa, Usuarios, Reportes y Licencias."),
                    ("🛒 Rol Vendedor / Cajero", "Acceso enfocado y restringido: solo puede Facturar (Ventas), consultar su Caja Chica y registrar Fiados."),
                    ("💾 Recordar Usuario", "Marca la casilla <b>'Recordar usuario'</b> en la pantalla de inicio de sesión para que el sistema recuerde tu usuario y puedas ingresar más rápido solo con tu clave."),
                    ("✏️ Editar Usuario", "Selecciona un usuario en la tabla para modificar su nombre, usuario de login, rol o cambiar su contraseña."),
                    ("🗑️ Eliminar Usuario", "Elimina cuentas que ya no trabajen en el negocio con confirmación de seguridad. El sistema protege al último Administrador para que nunca quede bloqueado.")
                ]
            )
        ])

    def _tab_caja_reportes(self):
        return self._crear_scroll_tab([
            self._crear_card_seccion(
                "💵 Caja Chica y Cierre de Turnos",
                "Monitorea el dinero en efectivo y movimientos de caja por turno:",
                [
                    ("Apertura de Caja", "Ingresa el monto inicial con el que comienza el cajero (fondo de caja para dar vuelto)."),
                    ("Ingresos y Retiros", "Registra salidas menores de dinero (ej: pago de botellón de agua, flete) para que cuadre exactamente al final del día."),
                    ("Arqueo y Cierre", "Al finalizar la jornada, realiza el cierre de caja para comparar el dinero físico esperado contra el registrado.")
                ]
            ),
            self._crear_card_seccion(
                "📊 Reportes Financieros y Ganancias",
                "",
                [
                    ("Desglose por Métodos", "Visualiza cuánto se cobró en Efectivo, Divisas, Pago Móvil, Tarjeta, Fiados y Pagos Mixtos."),
                    ("Ganancia Real Estimada", "El sistema calcula tu utilidad neta restando el costo en USD de los productos vendidos.")
                ]
            )
        ])

    def _tab_movil(self):
        return self._crear_scroll_tab([
            self._crear_card_seccion(
                "📱 App Móvil Android (MobilDesk Móvil)",
                "Lleva el control de tu negocio en tu bolsillo desde cualquier lugar:",
                [
                    ("1. Instalar la App", "Copia el archivo <code>mobildesk-movil.apk</code> a tu teléfono Android y pulsa Instalar."),
                    ("2. Enlace en 1 Toque", "Abre la App y escribe el <b>Código de Negocio</b> (el mismo que aparece en tu PC en 'Configurar Negocio')."),
                    ("3. Varios Teléfonos al Mismo Tiempo", "<b>¡Totalmente soportado!</b> Puedes instalar la app en todos los teléfonos de tu equipo (dueño, cajero, repartidor, almacén) con el mismo Código de Negocio."),
                    ("4. Consulta en Vivo", "Revisa tus ventas del día, el dinero en caja y tus existencias desde la calle."),
                    ("5. Ventas en Pasillo", "Factura directamente desde el teléfono mientras atiendes clientes en el local o almacén."),
                    ("6. Funciona sin Internet (Offline-First)", "Si un teléfono pierde la señal momentáneamente, puede seguir vendiendo. Al conectarse sube todo automáticamente.")
                ]
            )
        ])

    def _tab_actualizaciones(self):
        return self._crear_scroll_tab([
            self._crear_card_seccion(
                "🚀 Actualizaciones Remotas en Segundo Plano",
                "MobilDesk POS se mantiene siempre actualizado con las últimas mejoras sin interrumpir tu trabajo:",
                [
                    ("Detección Silenciosa", "Cada vez que abres el sistema conectado a internet, busca en segundo plano si existe una versión más reciente."),
                    ("Descarga sin Bloquear", "El instalador se descarga en segundo plano mientras continúas vendiendo con total normalidad."),
                    ("Botón de Aviso", "Cuando la descarga finaliza, aparece en la parte superior el botón verde: <b>'🚀 ¡Actualización vX.X lista!'</b>."),
                    ("Instalación en 10 Segundos", "Al hacer clic en el botón, el sistema se cierra, se actualiza automáticamente y <b>se vuelve a abrir solo</b> con todas las mejoras listas."),
                    ("Protección Total de Datos", "Tus ventas, productos, clientes, tasas y cajas se mantienen 100% intactos durante cualquier actualización.")
                ]
            )
        ])
