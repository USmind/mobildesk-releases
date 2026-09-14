from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QStackedWidget,
    QWidget,
    QFrame
)
from PySide6.QtCore import Qt


class WelcomeTourDialog(QDialog):
    def __init__(self, parent=None, nombre_negocio="MobilDesk"):
        super().__init__(parent)
        self.nombre_negocio = nombre_negocio
        self.setWindowTitle(f"Bienvenido a {self.nombre_negocio} POS - Guía Rápida")
        self.setFixedSize(680, 520)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)

        self.current_step = 0
        self.total_steps = 5

        self.crear_interfaz()
        self.actualizar_paso()

    def crear_interfaz(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(24, 20, 24, 20)
        main_layout.setSpacing(14)

        # Header con barra de progreso superior
        self.header_layout = QHBoxLayout()
        self.step_label = QLabel("PASO 1 DE 5")
        self.step_label.setObjectName("sectionLabel")
        self.header_layout.addWidget(self.step_label)
        self.header_layout.addStretch()

        self.btn_skip = QPushButton("Saltar Guía")
        self.btn_skip.setProperty("variant", "ghost")
        self.btn_skip.setToolTip("Cerrar la guía y entrar al sistema")
        self.btn_skip.clicked.connect(self.accept)
        self.header_layout.addWidget(self.btn_skip)
        main_layout.addLayout(self.header_layout)

        # Slides (QStackedWidget)
        self.slides = QStackedWidget()

        self.slides.addWidget(self._crear_slide_1())
        self.slides.addWidget(self._crear_slide_2())
        self.slides.addWidget(self._crear_slide_3())
        self.slides.addWidget(self._crear_slide_4())
        self.slides.addWidget(self._crear_slide_5())

        main_layout.addWidget(self.slides, 1)

        # Footer con botones de navegación
        footer_layout = QHBoxLayout()
        footer_layout.setSpacing(12)

        self.btn_prev = QPushButton("◀ Anterior")
        self.btn_prev.setProperty("variant", "ghost")
        self.btn_prev.setToolTip("Volver al paso anterior")
        self.btn_prev.clicked.connect(self.paso_anterior)
        footer_layout.addWidget(self.btn_prev)

        footer_layout.addStretch()

        # Indicadores de puntos (Dots)
        self.dots_layout = QHBoxLayout()
        self.dots_layout.setSpacing(8)
        self.dot_labels = []
        for i in range(self.total_steps):
            dot = QLabel("●")
            self.dot_labels.append(dot)
            self.dots_layout.addWidget(dot)
        footer_layout.addLayout(self.dots_layout)

        footer_layout.addStretch()

        self.btn_next = QPushButton("Siguiente ▶")
        self.btn_next.setToolTip("Avanzar al siguiente paso")
        self.btn_next.clicked.connect(self.paso_siguiente)
        footer_layout.addWidget(self.btn_next)

        main_layout.addLayout(footer_layout)

    def _crear_card_slide(self, icono, titulo, subtitulo, puntos):
        slide = QWidget()
        layout = QVBoxLayout(slide)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(14)

        # Header del slide
        h_layout = QHBoxLayout()
        h_layout.setSpacing(16)

        ico_lbl = QLabel(icono)
        ico_lbl.setStyleSheet("font-size: 32px;")
        ico_lbl.setAlignment(Qt.AlignCenter)
        h_layout.addWidget(ico_lbl)

        t_layout = QVBoxLayout()
        t_layout.setSpacing(4)
        t_lbl = QLabel(titulo)
        t_lbl.setObjectName("pageTitle")
        t_lbl.setWordWrap(True)
        sub_lbl = QLabel(subtitulo)
        sub_lbl.setObjectName("pageSubtitle")
        sub_lbl.setWordWrap(True)
        t_layout.addWidget(t_lbl)
        t_layout.addWidget(sub_lbl)

        h_layout.addLayout(t_layout, 1)
        layout.addLayout(h_layout)

        # Contenedor de puntos destacados
        card = QFrame()
        card.setObjectName("card")
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(20, 16, 20, 16)
        card_layout.setSpacing(12)

        for p_ico, p_tit, p_desc in puntos:
            row = QHBoxLayout()
            row.setSpacing(12)
            p_ico_lbl = QLabel(p_ico)
            row.addWidget(p_ico_lbl)

            col = QVBoxLayout()
            col.setSpacing(2)
            pt_lbl = QLabel(p_tit)
            pd_lbl = QLabel(p_desc)
            pd_lbl.setWordWrap(True)
            col.addWidget(pt_lbl)
            col.addWidget(pd_lbl)

            row.addLayout(col, 1)
            card_layout.addLayout(row)

        layout.addWidget(card, 1)
        return slide

    def _crear_slide_1(self):
        return self._crear_card_slide(
            "👋",
            f"¡Bienvenido a {self.nombre_negocio} POS!",
            "Tu nuevo sistema de Punto de Venta y Control Integral para tu comercio.",
            [
                ("⚡", "Velocidad y Facilidad Total", "Diseñado para que cualquier persona o cajero pueda facturar y atender clientes en segundos."),
                ("🔌", "Funciona 100% Sin Internet", "Si se cae la red o el WiFi, nunca dejas de vender. Todo queda guardado de forma segura en tu equipo."),
                ("📱", "Tu Negocio en tu Celular", "Consulta ventas, inventario y cambia la tasa en vivo desde la aplicación móvil de Android.")
            ]
        )

    def _crear_slide_2(self):
        return self._crear_card_slide(
            "💲",
            "Cobro Multimoneda (Bolívares y Dólares)",
            "Maneja divisas y moneda nacional con recálculo automático y vuelto exacto.",
            [
                ("🔄", "Cambio de Tasa Instantáneo", "Al actualizar la tasa del día en la PC o teléfono, todos los precios de los productos se actualizan al segundo."),
                ("🔍", "Búsqueda con Precio Dual", "Al buscar cualquier producto verás su precio en Bs y en USD entre paréntesis (ej: 300 Bs. ($1.50))."),
                ("🪙", "Calculadora de Vueltos", "Ingresa el monto que te entrega el cliente en Efectivo o Dólares y el sistema calcula el vuelto exacto.")
            ]
        )

    def _crear_slide_3(self):
        return self._crear_card_slide(
            "📦",
            "Inventario, Entradas y Margen de Ganancia",
            "Controla existencias en tiempo real y calcula tu rentabilidad automáticamente.",
            [
                ("📥", "Entradas y Ajustes de Stock", "Suma existencias al recibir compras o registra ajustes por mermas y productos dañados."),
                ("📈", "Calculadora de Precios Inteligente", "Define tu costo en Dólares y tu margen de ganancia (15%, 30%, 50%) para calcular el precio de venta sugerido."),
                ("📋", "Historial Completo de Movimientos", "Monitorea cada entrada y salida con fecha, hora, usuario responsable y motivo.")
            ]
        )

    def _crear_slide_4(self):
        return self._crear_card_slide(
            "👥",
            "Control de Fiados y Cuentas por Cobrar",
            "Dile adiós a los cuadernos y hojas sueltas: cero pérdidas en ventas a crédito.",
            [
                ("📝", "Registro Directo de Fiados", "Selecciona el método 'Fiado / Crédito' en el cobro, escribe el nombre del cliente y listo."),
                ("💵", "Cobro y Abonos Flexibles", "Registra pagos totales (100%), abonos parciales (50%) o montos personalizados en 2 toques."),
                ("📊", "Estado de Cuenta en Vivo", "Conoce con exactitud cuánto dinero tienes por cobrar en la calle en cualquier momento.")
            ]
        )

    def _crear_slide_5(self):
        return self._crear_card_slide(
            "🚀",
            "¡Todo Listo para Empezar!",
            "Tienes todo lo necesario para comenzar a facturar y hacer crecer tu negocio.",
            [
                ("❓", "Manual y Ayuda Integrado", "Si tienes dudas, pulsa el botón '📖 Manual y Ayuda' en la barra lateral para ver la guía completa."),
                ("👤", "Módulo de Usuarios", "Crea cajeros con permisos restringidos y mantén el control total como Administrador."),
                ("🖨️", "Tickets de Venta", "Imprime recibos en impresoras térmicas de 58mm y 80mm o guárdalos en PDF.")
            ]
        )

    def actualizar_paso(self):
        self.slides.setCurrentIndex(self.current_step)
        self.step_label.setText(f"PASO {self.current_step + 1} DE {self.total_steps}")

        # Botón anterior visible solo si > 0
        self.btn_prev.setVisible(self.current_step > 0)

        # Botón siguiente cambia a 'Comenzar' en el último paso
        if self.current_step == self.total_steps - 1:
            self.btn_next.setText("¡Comenzar a Usar!")
            self.btn_next.setProperty("variant", "success")
        else:
            self.btn_next.setText("Siguiente ▶")
            self.btn_next.setProperty("variant", None)
        self.btn_next.style().unpolish(self.btn_next)
        self.btn_next.style().polish(self.btn_next)
        self.btn_next.update()

        # Actualizar dots
        for idx, dot in enumerate(self.dot_labels):
            if idx == self.current_step:
                dot.setStyleSheet("font-size: 16px; color: #2563EB;")
            else:
                dot.setStyleSheet("font-size: 14px; color: #E4E7EC;")

    def paso_siguiente(self):
        if self.current_step < self.total_steps - 1:
            self.current_step += 1
            self.actualizar_paso()
        else:
            self.accept()

    def paso_anterior(self):
        if self.current_step > 0:
            self.current_step -= 1
            self.actualizar_paso()
