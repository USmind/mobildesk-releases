from datetime import date, timedelta
from PySide6.QtCore import Qt, QDate
from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QMessageBox,
    QComboBox,
    QDateEdit,
    QHeaderView,
    QFrame,
    QTabWidget,
    QWidget,
    QFileDialog,
)
from modules.reportes.reports_service import (
    get_sales_report,
    get_financial_kpis,
    get_top_selling_products,
    get_critical_stock_report,
    export_sales_to_csv,
)


class ReportsWindow(QDialog):
    def __init__(self, user=None, parent=None):
        super().__init__(parent)
        self.user = user
        self.setWindowTitle("Reportes y Estadísticas de Ventas")
        self.setWindowFlags(Qt.Window | Qt.WindowTitleHint | Qt.WindowSystemMenuHint | Qt.WindowMinMaxButtonsHint | Qt.WindowCloseButtonHint)
        self.resize(1080, 640)
        self.setMinimumSize(780, 460)
        self.crear_interfaz()
        self.establecer_periodo("hoy")

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
            QLineEdit, QComboBox, QDateEdit {
                background-color: #ffffff;
                border: 1.5px solid #cbd5e1;
                border-radius: 7px;
                padding: 7px 10px;
                color: #0f172a;
            }
            QLineEdit:focus, QComboBox:focus, QDateEdit:focus { border: 2px solid #2563eb; }
            QTableWidget {
                background-color: #ffffff;
                border: 1px solid #cbd5e1;
                border-radius: 8px;
                gridline-color: #f1f5f9;
            }
            QHeaderView::section {
                background-color: #f8fafc;
                color: #0f172a;
                font-weight: 700;
                border: none;
                border-bottom: 2px solid #cbd5e1;
                padding: 8px;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(22, 20, 22, 20)
        layout.setSpacing(14)

        # Header con filtros de fecha
        filtros_frame = QFrame()
        filtros_frame.setObjectName("filtrosCard")
        filtros_frame.setStyleSheet("""
            QFrame#filtrosCard {
                background-color: #ffffff;
                border: 1px solid #e2e8f0;
                border-radius: 10px;
            }
        """)
        f_layout = QHBoxLayout(filtros_frame)
        f_layout.setSpacing(10)

        f_layout.addWidget(QLabel("<b>Período:</b>"))
        self.combo_periodo = QComboBox()
        self.combo_periodo.addItem("Hoy", "hoy")
        self.combo_periodo.addItem("Ayer", "ayer")
        self.combo_periodo.addItem("Esta semana", "semana")
        self.combo_periodo.addItem("Este mes", "mes")
        self.combo_periodo.addItem("Rango personalizado", "custom")
        self.combo_periodo.currentIndexChanged.connect(self.al_cambiar_combo_periodo)
        f_layout.addWidget(self.combo_periodo)

        f_layout.addWidget(QLabel("Desde:"))
        self.date_desde = QDateEdit(QDate.currentDate())
        self.date_desde.setCalendarPopup(True)
        f_layout.addWidget(self.date_desde)

        f_layout.addWidget(QLabel("Hasta:"))
        self.date_hasta = QDateEdit(QDate.currentDate())
        self.date_hasta.setCalendarPopup(True)
        f_layout.addWidget(self.date_hasta)

        btn_filtrar = QPushButton("🔍 Filtrar")
        btn_filtrar.setStyleSheet("""
            QPushButton {
                background: #2563eb;
                color: white;
                font-weight: 700;
                padding: 7px 16px;
                border-radius: 6px;
                border: none;
            }
            QPushButton:hover { background: #1d4ed8; }
        """)
        btn_filtrar.clicked.connect(self.cargar_reporte)
        f_layout.addWidget(btn_filtrar)

        f_layout.addStretch()

        btn_exportar = QPushButton("📥 Exportar CSV / Excel")
        btn_exportar.setStyleSheet("""
            QPushButton {
                background: #f1f5f9;
                color: #334155;
                border: 1px solid #e2e8f0;
                font-weight: 600;
                padding: 7px 16px;
                border-radius: 8px;
            }
            QPushButton:hover { background: #e2e8f0; }
        """)
        btn_exportar.clicked.connect(self.exportar_csv)
        f_layout.addWidget(btn_exportar)

        layout.addWidget(filtros_frame)

        # Tarjetas de Resumen KPI
        kpi_layout = QHBoxLayout()
        kpi_layout.setSpacing(10)

        self.kpi_ventas = self.crear_kpi_card("TOTAL VENTAS", "Bs 0.00", "$0.00", "#1e3a8a")
        self.kpi_ganancia = self.crear_kpi_card("GANANCIA BRUTA EST.", "$0.00", "Margen positivo", "#15803d")
        self.kpi_transacciones = self.crear_kpi_card("TRANSACCIONES", "0 ventas", "Prom: Bs 0.00", "#475569")
        self.kpi_deudas = self.crear_kpi_card("FIADOS PENDIENTES", "Bs 0.00", "Cuentas por cobrar", "#b45309")

        kpi_layout.addWidget(self.kpi_ventas)
        kpi_layout.addWidget(self.kpi_ganancia)
        kpi_layout.addWidget(self.kpi_transacciones)
        kpi_layout.addWidget(self.kpi_deudas)
        layout.addLayout(kpi_layout)

        # Tabs de Contenido
        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)

        # Tab 1: Detalle de Ventas
        self.tab_ventas = QWidget()
        tv_layout = QVBoxLayout(self.tab_ventas)
        self.tabla_ventas = QTableWidget()
        self.tabla_ventas.verticalHeader().setVisible(False)
        self.tabla_ventas.setColumnCount(9)
        self.tabla_ventas.setHorizontalHeaderLabels([
            "Factura", "Fecha", "Vendedor", "Cliente", "Método", "Tasa", "Total USD", "Total Bs", "Estado"
        ])
        self.tabla_ventas.setEditTriggers(QTableWidget.NoEditTriggers)
        self.tabla_ventas.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        tv_layout.addWidget(self.tabla_ventas)
        self.tabs.addTab(self.tab_ventas, "Detalle de Ventas")

        # Tab 2: Métodos de Pago
        self.tab_metodos = QWidget()
        tm_layout = QVBoxLayout(self.tab_metodos)
        self.tabla_metodos = QTableWidget()
        self.tabla_metodos.verticalHeader().setVisible(False)
        self.tabla_metodos.setColumnCount(3)
        self.tabla_metodos.setHorizontalHeaderLabels(["Método de Pago", "Monto Recaudado", "Detalle"])
        self.tabla_metodos.setEditTriggers(QTableWidget.NoEditTriggers)
        self.tabla_metodos.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        tm_layout.addWidget(self.tabla_metodos)
        self.tabs.addTab(self.tab_metodos, "Ventas por Método de Pago")

        # Tab 3: Top Productos
        self.tab_top = QWidget()
        tt_layout = QVBoxLayout(self.tab_top)
        self.tabla_top = QTableWidget()
        self.tabla_top.verticalHeader().setVisible(False)
        self.tabla_top.setColumnCount(5)
        self.tabla_top.setHorizontalHeaderLabels(["Código", "Producto", "Unidad", "Unidades Vendidas", "Total USD"])
        self.tabla_top.setEditTriggers(QTableWidget.NoEditTriggers)
        self.tabla_top.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        tt_layout.addWidget(self.tabla_top)
        self.tabs.addTab(self.tab_top, "Top 10 Productos Más Vendidos")

        # Tab 4: Stock Crítico
        self.tab_critico = QWidget()
        tc_layout = QVBoxLayout(self.tab_critico)
        self.tabla_critico = QTableWidget()
        self.tabla_critico.verticalHeader().setVisible(False)
        self.tabla_critico.setColumnCount(5)
        self.tabla_critico.setHorizontalHeaderLabels(["Código", "Producto", "Unidad", "Stock Actual", "Stock Mínimo"])
        self.tabla_critico.setEditTriggers(QTableWidget.NoEditTriggers)
        self.tabla_critico.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        tc_layout.addWidget(self.tabla_critico)
        self.tabs.addTab(self.tab_critico, "Alertas de Stock Bajo")

    def crear_kpi_card(self, titulo, valor1, valor2, color=""):
        """Tarjeta metrica neutral: sin barras de color ni marcos internos."""
        frame = QFrame()
        frame.setObjectName("kpiCard")
        frame.setStyleSheet("""
            QFrame#kpiCard {
                background-color: #ffffff;
                border: 1px solid #e2e8f0;
                border-radius: 10px;
            }
        """)
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(14, 10, 14, 10)
        layout.setSpacing(3)

        t_lbl = QLabel(titulo)
        t_lbl.setStyleSheet("color: #64748b; font-size: 11px; font-weight: 700; letter-spacing: 0.5px; border: none; background: transparent;")
        v1_lbl = QLabel(valor1)
        v1_lbl.setStyleSheet("color: #0f172a; font-size: 18px; font-weight: 700; border: none; background: transparent;")
        v2_lbl = QLabel(valor2)
        v2_lbl.setStyleSheet("color: #64748b; font-size: 12px; border: none; background: transparent;")

        layout.addWidget(t_lbl)
        layout.addWidget(v1_lbl)
        layout.addWidget(v2_lbl)
        frame.v1_lbl = v1_lbl
        frame.v2_lbl = v2_lbl
        return frame

    def al_cambiar_combo_periodo(self):
        periodo = self.combo_periodo.currentData()
        if periodo != "custom":
            self.establecer_periodo(periodo)

    def establecer_periodo(self, tipo):
        hoy = date.today()
        if tipo == "hoy":
            d_inicio, d_fin = hoy, hoy
        elif tipo == "ayer":
            ayer = hoy - timedelta(days=1)
            d_inicio, d_fin = ayer, ayer
        elif tipo == "semana":
            d_inicio = hoy - timedelta(days=hoy.weekday())
            d_fin = hoy
        elif tipo == "mes":
            d_inicio = hoy.replace(day=1)
            d_fin = hoy
        else:
            return

        self.date_desde.setDate(QDate(d_inicio.year, d_inicio.month, d_inicio.day))
        self.date_hasta.setDate(QDate(d_fin.year, d_fin.month, d_fin.day))
        self.cargar_reporte()

    def obtener_rango_fechas(self):
        f_ini = self.date_desde.date().toString("yyyy-MM-dd")
        f_fin = self.date_hasta.date().toString("yyyy-MM-dd")
        return f_ini, f_fin

    def cargar_reporte(self):
        f_ini, f_fin = self.obtener_rango_fechas()
        u_id = self.user["id"] if (self.user and self.user["role"] == "vendedor") else None

        kpis = get_financial_kpis(f_ini, f_fin)
        self.kpi_ventas.v1_lbl.setText(f"Bs {kpis['total_ventas_bs']:,.2f}")
        self.kpi_ventas.v2_lbl.setText(f"${kpis['total_ventas_usd']:,.2f} USD")

        self.kpi_ganancia.v1_lbl.setText(f"${kpis['ganancia_bruta_usd']:,.2f} USD")
        self.kpi_ganancia.v2_lbl.setText(f"Costo: ${kpis['costo_total_usd']:,.2f}")

        self.kpi_transacciones.v1_lbl.setText(f"{kpis['total_transacciones']} ventas")
        self.kpi_transacciones.v2_lbl.setText(f"Ticket Prom: Bs {kpis['ticket_promedio_bs']:,.2f}")

        self.kpi_deudas.v1_lbl.setText(f"Bs {kpis['total_deudas_bs']:,.2f}")
        self.kpi_deudas.v2_lbl.setText("Deudas por cobrar")

        # Tab 1: Ventas
        ventas = get_sales_report(f_ini, f_fin, u_id)
        self.tabla_ventas.setRowCount(len(ventas))
        for r, v in enumerate(ventas):
            estado_txt = "FIADO (Deuda)" if v["es_fiada"] else "PAGADA"
            valores = [
                v["numero_factura"],
                v["fecha"],
                v["usuario_nombre"] or "",
                v["cliente_nombre"] or "Consumidor Final",
                v["metodo_pago"].replace("_", " ").title(),
                f"{float(v['tasa_utilizada']):,.2f}",
                f"${float(v['total_usd']):,.2f}",
                f"Bs {float(v['total_bs']):,.2f}",
                estado_txt,
            ]
            for c, val in enumerate(valores):
                item = QTableWidgetItem(str(val))
                if c in (0, 1, 5, 6, 7, 8):
                    item.setTextAlignment(Qt.AlignCenter)
                self.tabla_ventas.setItem(r, c, item)

        # Tab 2: Métodos de pago
        metodos = kpis["metodos_pago"]
        filas_m = [
            ("Efectivo Bolívares", f"Bs {metodos['efectivo']:,.2f}", "Efectivo directo en gaveta"),
            ("Divisas Dólares", f"${metodos['divisas_usd']:,.2f} (Bs {metodos['divisas_bs']:,.2f})", "Dólares en efectivo"),
            ("Pago Móvil", f"Bs {metodos['pago_movil']:,.2f}", "Transferencia bancaria / Pago móvil"),
            ("Tarjeta Débito/Crédito", f"Bs {metodos['tarjeta']:,.2f}", "Punto de venta bancario"),
            ("Ventas Fiadas / Crédito", f"Bs {metodos['fiado']:,.2f}", "Pendiente de cobro en clientes"),
        ]
        self.tabla_metodos.setRowCount(len(filas_m))
        for r, (m_nom, m_val, m_det) in enumerate(filas_m):
            self.tabla_metodos.setItem(r, 0, QTableWidgetItem(m_nom))
            self.tabla_metodos.setItem(r, 1, QTableWidgetItem(m_val))
            self.tabla_metodos.setItem(r, 2, QTableWidgetItem(m_det))

        # Tab 3: Top productos
        top_prods = get_top_selling_products(f_ini, f_fin)
        self.tabla_top.setRowCount(len(top_prods))
        for r, p in enumerate(top_prods):
            self.tabla_top.setItem(r, 0, QTableWidgetItem(p["codigo"]))
            self.tabla_top.setItem(r, 1, QTableWidgetItem(p["nombre"]))
            self.tabla_top.setItem(r, 2, QTableWidgetItem(p["unidad"]))
            self.tabla_top.setItem(r, 3, QTableWidgetItem(f"{float(p['unidades_vendidas']):g}"))
            self.tabla_top.setItem(r, 4, QTableWidgetItem(f"${float(p['total_usd']):,.2f}"))

        # Tab 4: Stock crítico
        criticos = get_critical_stock_report()
        self.tabla_critico.setRowCount(len(criticos))
        for r, p in enumerate(criticos):
            self.tabla_critico.setItem(r, 0, QTableWidgetItem(p["codigo"]))
            self.tabla_critico.setItem(r, 1, QTableWidgetItem(p["nombre"]))
            self.tabla_critico.setItem(r, 2, QTableWidgetItem(p["unidad"]))
            self.tabla_critico.setItem(r, 3, QTableWidgetItem(f"{float(p['stock_actual']):g}"))
            self.tabla_critico.setItem(r, 4, QTableWidgetItem(f"{float(p['stock_minimo']):g}"))

    def exportar_csv(self):
        f_ini, f_fin = self.obtener_rango_fechas()
        archivo, _ = QFileDialog.getSaveFileName(
            self,
            "Exportar Reporte de Ventas",
            f"Reporte_Ventas_{f_ini}_a_{f_fin}.csv",
            "Archivos CSV (*.csv)",
        )
        if archivo:
            try:
                export_sales_to_csv(archivo, f_ini, f_fin)
                QMessageBox.information(self, "Exportación Exitosa", f"Reporte guardado en:\n{archivo}")
            except Exception as error:
                QMessageBox.critical(self, "Error", f"No se pudo exportar el archivo:\n{error}")
