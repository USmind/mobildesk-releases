import sys

from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QIcon
from app_paths import resource_path

from database.migrate import run_migrations
from modules.usuarios.user_service import has_users
from modules.usuarios.session import get_user
from ui.windows.login_window import LoginWindow
from ui.windows.dashboard_window import DashboardWindow
from ui.windows.initial_setup_window import InitialSetupWindow

# ============================================================
# TEMA GLOBAL MOBILDESK POS
# Paleta neutral profesional: fondos claros, un solo acento azul,
# tipografia jerarquica y controles discretos.
# ============================================================
APP_STYLE = """
* { outline: none; }
*:focus { outline: none; }

QWidget {
    font-family: 'Segoe UI', sans-serif;
    color: #0f172a;
    font-size: 13.5px;
}

QMainWindow, QDialog { background-color: #f8fafc; }

/* ---------- Etiquetas ---------- */
QLabel {
    background: transparent;
    border: none;
    color: #0f172a;
    outline: none;
}
QLabel:focus { background: transparent; border: none; outline: none; }

/* ---------- Campos de entrada ---------- */
QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox, QDateEdit, QTimeEdit, QDateTimeEdit {
    background-color: #ffffff;
    border: 1px solid #cbd5e1;
    border-radius: 8px;
    padding: 8px 11px;
    min-height: 22px;
    color: #0f172a;
    selection-background-color: #2563eb;
    selection-color: #ffffff;
}
QLineEdit:hover, QComboBox:hover, QSpinBox:hover, QDoubleSpinBox:hover,
QDateEdit:hover, QTimeEdit:hover, QDateTimeEdit:hover { border-color: #94a3b8; }
QLineEdit:focus, QComboBox:focus, QSpinBox:focus, QDoubleSpinBox:focus,
QDateEdit:focus, QTimeEdit:focus, QDateTimeEdit:focus { border: 2px solid #2563eb; padding: 7px 10px; }
QLineEdit:disabled, QComboBox:disabled { background-color: #f1f5f9; color: #94a3b8; }
QComboBox::drop-down { border: none; width: 26px; }
QComboBox QAbstractItemView {
    background-color: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 8px;
    selection-background-color: #eff6ff;
    selection-color: #1e3a8a;
    outline: none;
    padding: 4px;
}
QSpinBox::up-button, QDoubleSpinBox::up-button,
QSpinBox::down-button, QDoubleSpinBox::down-button {
    background: transparent; border: none; width: 18px;
}
QSpinBox::up-arrow, QDoubleSpinBox::up-arrow { image: none; border-left: 4px solid transparent; border-right: 4px solid transparent; border-bottom: 5px solid #94a3b8; width: 0; height: 0; }
QSpinBox::down-arrow, QDoubleSpinBox::down-arrow { image: none; border-left: 4px solid transparent; border-right: 4px solid transparent; border-top: 5px solid #94a3b8; width: 0; height: 0; }

/* ---------- Botones ---------- */
QPushButton {
    background-color: #2563eb;
    color: #ffffff;
    border: none;
    border-radius: 8px;
    padding: 8px 16px;
    font-weight: 600;
    min-height: 22px;
}
QPushButton:hover { background-color: #1d4ed8; }
QPushButton:pressed { background-color: #1e40af; }
QPushButton:disabled { background-color: #e2e8f0; color: #94a3b8; }
QPushButton:focus { border: 2px solid #93c5fd; padding: 7px 14px; }

/* ---------- Dialogos y mensajes ---------- */
QMessageBox { background-color: #ffffff; }
QMessageBox QLabel {
    color: #0f172a;
    font-size: 14px;
    font-weight: 600;
    background: transparent;
    border: none;
}
QMessageBox QPushButton, QDialogButtonBox QPushButton {
    background-color: #2563eb;
    color: #ffffff;
    border: none;
    border-radius: 8px;
    padding: 8px 18px;
    font-size: 13.5px;
    font-weight: 600;
    min-width: 84px;
    min-height: 28px;
}
QMessageBox QPushButton:hover, QDialogButtonBox QPushButton:hover { background-color: #1d4ed8; }
QMessageBox QPushButton:pressed, QDialogButtonBox QPushButton:pressed { background-color: #1e40af; }

/* ---------- Tablas ---------- */
QTableWidget, QTableView {
    background-color: #ffffff;
    alternate-background-color: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 10px;
    gridline-color: transparent;
    selection-background-color: #eff6ff;
    selection-color: #1e3a8a;
    outline: none;
}
QTableWidget::item, QTableView::item {
    padding: 9px 8px;
    border: none;
    border-bottom: 1px solid #f1f5f9;
    outline: none;
}
QTableWidget::item:focus, QTableView::item:focus {
    border: none;
    outline: none;
    background-color: #eff6ff;
    color: #1e3a8a;
}
QTableWidget::item:selected, QTableView::item:selected {
    background-color: #eff6ff;
    color: #1e3a8a;
    font-weight: 600;
    border: none;
    outline: none;
}
QTableWidget::item:hover:!selected, QTableView::item:hover:!selected { background-color: #f8fafc; }

QHeaderView { background-color: transparent; border: none; }
QHeaderView::section {
    background-color: #ffffff;
    color: #64748b;
    font-size: 12px;
    font-weight: 700;
    border: none;
    border-bottom: 1px solid #e2e8f0;
    padding: 10px 8px;
}
QTableCornerButton::section { background-color: #ffffff; border: none; }

/* ---------- Barras de desplazamiento ---------- */
QScrollBar:vertical {
    background: transparent;
    width: 10px;
    margin: 2px;
}
QScrollBar::handle:vertical {
    background: #cbd5e1;
    border-radius: 4px;
    min-height: 32px;
}
QScrollBar::handle:vertical:hover { background: #94a3b8; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical { background: transparent; }

QScrollBar:horizontal {
    background: transparent;
    height: 10px;
    margin: 2px;
}
QScrollBar::handle:horizontal {
    background: #cbd5e1;
    border-radius: 4px;
    min-width: 32px;
}
QScrollBar::handle:horizontal:hover { background: #94a3b8; }
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal { width: 0; }
QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal { background: transparent; }

/* ---------- Pestañas ---------- */
QTabWidget::pane {
    background-color: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 10px;
    top: -1px;
}
QTabBar::tab {
    background: transparent;
    color: #64748b;
    font-weight: 600;
    padding: 10px 18px;
    border: none;
    border-bottom: 2px solid transparent;
    margin-right: 2px;
}
QTabBar::tab:selected { color: #2563eb; border-bottom: 2px solid #2563eb; }
QTabBar::tab:hover:!selected { color: #334155; }
QTabBar::tab:focus { outline: none; }

/* ---------- Grupos y varios ---------- */
QGroupBox {
    background-color: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 10px;
    margin-top: 14px;
    padding-top: 6px;
    font-weight: 700;
}
QGroupBox::title {
    subcontrol-origin: margin;
    left: 12px;
    padding: 0 6px;
    color: #64748b;
    font-size: 12px;
}
QCheckBox, QRadioButton { spacing: 8px; background: transparent; }
QCheckBox::indicator, QRadioButton::indicator { width: 16px; height: 16px; }
QProgressBar {
    background-color: #eef2f7;
    border: none;
    border-radius: 6px;
    min-height: 10px;
    text-align: center;
    color: transparent;
}
QProgressBar::chunk { background-color: #2563eb; border-radius: 6px; }
QToolTip {
    background-color: #0f172a;
    color: #f8fafc;
    border: none;
    padding: 6px 10px;
    border-radius: 6px;
    font-size: 12.5px;
}
"""


def main():
    run_migrations()

    app = QApplication(sys.argv)
    app.setApplicationName("MobilDesk POS")
    app.setWindowIcon(QIcon(resource_path("assets/kiosko_logo.svg")))
    app.setStyleSheet(APP_STYLE)

    if not has_users():
        setup_dlg = InitialSetupWindow()
        setup_dlg.exec()
        if not setup_dlg.configurado_exitosamente:
            sys.exit(0)
        ventana = DashboardWindow(mostrar_tour_inicial=True)
    else:
        ventana = LoginWindow()

    ventana.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
