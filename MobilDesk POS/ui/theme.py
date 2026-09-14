"""MobilDesk POS — Design System completo.

Fuente unica de verdad visual. Cubre TODOS los widgets Qt usados
(incluidos popups: calendario, dropdowns, autocompletado, menus).

Ganchos:
  Labels: pageTitle / pageSubtitle / sectionLabel / money /
          kpiValue (+accent=brand|success|danger) / kpiLabel
  Botones (propiedad variant): default primario, success, danger,
          ghost, soft
  Contenedores: QFrame#card / #cardFlat / #kpi / #banner / #bannerDark

Paleta:
  APP_BG  #F7F8FA   CARD #FFFFFF   INK #131722   MUTED #6B7280
  BORDER  #E4E7EC   BRAND #2563EB  SUCCESS #16A34A  DANGER #DC2626
"""

APP_BG = "#F7F8FA"
CARD = "#FFFFFF"
INK = "#131722"
MUTED = "#6B7280"
SUBTLE = "#9CA3AF"
BORDER = "#E4E7EC"
BORDER_DARK = "#C9CED6"
BRAND = "#2563EB"
BRAND_HOVER = "#1D4ED8"
BRAND_SOFT = "#EFF4FF"
SUCCESS = "#16A34A"
SUCCESS_HOVER = "#15803D"
SUCCESS_SOFT = "#EAF9F0"
DANGER = "#DC2626"
DANGER_HOVER = "#B91C1C"
DANGER_SOFT = "#FDECEC"
TRACK = "#EDF0F4"

import os as _os


def _asset_url(name):
    # Ruta absoluta con slashes (QSS no acepta backslashes). Funciona
    # en desarrollo y en el .exe (assets viaja con --add-data).
    try:
        from app_paths import resource_path
        return resource_path(_os.path.join("assets", name)).replace("\\", "/")
    except Exception:
        return "assets/" + name


CHECK_SVG = _asset_url("check.svg")
CHEVRON_SVG = _asset_url("chevron-down.svg")

GLOBAL_QSS = """
* { outline: none; }
*:focus { outline: none; }

/* ================= Base ================= */
QWidget {
    font-family: 'Segoe UI', sans-serif;
    color: #131722;
    font-size: 13.5px;
}
QMainWindow, QDialog { background-color: #F7F8FA; }

/* ================= Tipografia ================= */
QLabel { background: transparent; border: none; color: #131722; }
QLabel#pageTitle { font-size: 22px; font-weight: 700; color: #131722; }
QLabel#pageSubtitle { font-size: 13px; color: #6B7280; }
QLabel#sectionLabel { font-size: 11px; font-weight: 700; color: #6B7280; }
QLabel#money { font-size: 16px; font-weight: 700; color: #131722; }
QLabel#kpiValue { font-size: 20px; font-weight: 800; color: #131722; }
QLabel#kpiValue[accent="brand"] { color: #2563EB; }
QLabel#kpiValue[accent="success"] { color: #16A34A; }
QLabel#kpiValue[accent="danger"] { color: #DC2626; }
QLabel#kpiLabel { font-size: 11px; font-weight: 700; color: #6B7280; }

/* ================= Contenedores ================= */
QFrame#card {
    background-color: #FFFFFF;
    border: 1px solid #E4E7EC;
    border-radius: 10px;
}
QFrame#cardFlat { background-color: #FFFFFF; border: none; }
QFrame#kpi {
    background-color: #FFFFFF;
    border: 1px solid #E4E7EC;
    border-radius: 10px;
}
QFrame#banner { background-color: #2563EB; border-radius: 10px; }
QFrame#banner QLabel { color: #FFFFFF; }
QFrame#bannerDark { background-color: #0B0F1A; border-radius: 10px; }
QFrame#bannerDark QLabel { color: #FFFFFF; }

/* ================= Inputs de texto ================= */
QLineEdit, QTextEdit, QPlainTextEdit {
    background-color: #FFFFFF;
    border: 1.5px solid #E4E7EC;
    border-radius: 8px;
    padding: 8px 12px;
    color: #131722;
    selection-background-color: #2563EB;
    selection-color: #FFFFFF;
}
QLineEdit, QDateEdit, QDateTimeEdit, QTimeEdit { min-height: 28px; }
QLineEdit:hover, QTextEdit:hover, QPlainTextEdit:hover { border-color: #9CA3AF; }
QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus {
    border: 2px solid #2563EB;
    padding: 7px 11px;
}
QLineEdit:disabled, QTextEdit:disabled, QPlainTextEdit:disabled {
    background-color: #F7F8FA;
    color: #9CA3AF;
}

/* ================= SpinBox / fecha / hora ================= */
QSpinBox, QDoubleSpinBox, QDateEdit, QDateTimeEdit, QTimeEdit {
    background-color: #FFFFFF;
    border: 1.5px solid #E4E7EC;
    border-radius: 8px;
    padding: 8px 12px;
    color: #131722;
    selection-background-color: #2563EB;
    selection-color: #FFFFFF;
}
QSpinBox:hover, QDoubleSpinBox:hover, QDateEdit:hover,
QDateTimeEdit:hover, QTimeEdit:hover { border-color: #9CA3AF; }
QSpinBox:focus, QDoubleSpinBox:focus, QDateEdit:focus,
QDateTimeEdit:focus, QTimeEdit:focus { border: 2px solid #2563EB; }
QSpinBox:disabled, QDoubleSpinBox:disabled, QDateEdit:disabled {
    background-color: #F7F8FA;
    color: #9CA3AF;
}
QSpinBox::up-button, QDoubleSpinBox::up-button,
QDateEdit::up-button, QDateTimeEdit::up-button {
    subcontrol-origin: border;
    subcontrol-position: top right;
    width: 26px;
    border: none;
    border-left: 1px solid #E4E7EC;
    border-top-right-radius: 8px;
    background-color: #F7F8FA;
}
QSpinBox::down-button, QDoubleSpinBox::down-button,
QDateEdit::down-button, QDateTimeEdit::down-button {
    subcontrol-origin: border;
    subcontrol-position: bottom right;
    width: 26px;
    border: none;
    border-left: 1px solid #E4E7EC;
    border-bottom-right-radius: 8px;
    background-color: #F7F8FA;
}
QSpinBox::up-button:hover, QDoubleSpinBox::up-button:hover,
QSpinBox::down-button:hover, QDoubleSpinBox::down-button:hover,
QDateEdit::up-button:hover, QDateEdit::down-button:hover { background-color: #E9EBEF; }
QSpinBox::up-arrow, QDoubleSpinBox::up-arrow, QDateEdit::up-arrow {
    image: none;
    border-left: 4px solid transparent;
    border-right: 4px solid transparent;
    border-bottom: 5px solid #6B7280;
    width: 0; height: 0;
}
QSpinBox::down-arrow, QDoubleSpinBox::down-arrow, QDateEdit::down-arrow {
    image: none;
    border-left: 4px solid transparent;
    border-right: 4px solid transparent;
    border-top: 5px solid #6B7280;
    width: 0; height: 0;
}
QDateEdit::drop-down, QDateTimeEdit::drop-down {
    subcontrol-origin: padding;
    subcontrol-position: center right;
    width: 38px;
    border: none;
    border-left: 1px solid #E4E7EC;
}
QDateEdit::down-arrow, QDateTimeEdit::down-arrow {
    image: url(__CHEVRON_SVG__);
    width: 14px;
    height: 14px;
}

/* ================= ComboBox ================= */
QComboBox {
    background-color: #FFFFFF;
    border: 1.5px solid #E4E7EC;
    border-radius: 8px;
    padding: 8px 12px;
    min-height: 26px;
    color: #131722;
}
QComboBox:hover { border-color: #9CA3AF; }
QComboBox:focus { border: 2px solid #2563EB; padding: 7px 11px; }
QComboBox:disabled { background-color: #F7F8FA; color: #9CA3AF; }
QComboBox::drop-down {
    border: none;
    border-left: 1px solid #E4E7EC;
    width: 38px;
    background-color: transparent;
}
QComboBox::down-arrow {
    image: url(__CHEVRON_SVG__);
    width: 14px;
    height: 14px;
}
QComboBox QAbstractItemView {
    background-color: #FFFFFF;
    border: 1px solid #C9CED6;
    border-radius: 10px;
    outline: none;
    padding: 6px;
    selection-background-color: #2563EB;
    selection-color: #FFFFFF;
}
QComboBox QAbstractItemView::item {
    min-height: 40px;
    padding: 12px 14px;
    color: #131722;
    background-color: #FFFFFF;
    border: none;
    border-radius: 6px;
}
QComboBox QAbstractItemView::item:hover {
    background-color: #EFF4FF;
    color: #131722;
}
QComboBox QAbstractItemView::item:selected {
    background-color: #2563EB;
    color: #FFFFFF;
    font-weight: 700;
}
QComboBox QAbstractItemView::item:selected:!active {
    background-color: #DCE7FD;
    color: #1D4ED8;
}

/* ================= Listas (incl. autocompletado) ================= */
QListView, QListWidget {
    background-color: #FFFFFF;
    border: 1px solid #E4E7EC;
    border-radius: 8px;
    outline: none;
    padding: 4px;
    selection-background-color: #2563EB;
    selection-color: #FFFFFF;
}
QListView::item, QListWidget::item {
    min-height: 30px;
    padding: 8px 12px;
    color: #131722;
    border: none;
    border-radius: 6px;
}
QListView::item:hover, QListWidget::item:hover { background-color: #EFF4FF; }
QListView::item:selected, QListWidget::item:selected {
    background-color: #2563EB;
    color: #FFFFFF;
    font-weight: 700;
}
QListView::item:selected:!active, QListWidget::item:selected:!active {
    background-color: #DCE7FD;
    color: #1D4ED8;
}

/* ================= Calendario ================= */
QCalendarWidget {
    background-color: #FFFFFF;
    border: 1px solid #C9CED6;
}
QCalendarWidget QWidget { alternate-background-color: #F1F3F6; }
QCalendarWidget QAbstractItemView:enabled {
    background-color: #FFFFFF;
    color: #131722;
    selection-background-color: #2563EB;
    selection-color: #FFFFFF;
    selection-border-color: #2563EB;
    outline: none;
}
QCalendarWidget QAbstractItemView:disabled { color: #C9CED6; }
QCalendarWidget#qt_calendar_navigationbar, QWidget#qt_calendar_navigationbar {
    background-color: #FFFFFF;
    border: none;
    border-bottom: 1px solid #E4E7EC;
    min-height: 38px;
}
QToolButton#qt_calendar_prevmonth, QToolButton#qt_calendar_nextmonth {
    background-color: transparent;
    border: none;
    border-radius: 8px;
    width: 34px;
    height: 34px;
}
QToolButton#qt_calendar_prevmonth:hover, QToolButton#qt_calendar_nextmonth:hover {
    background-color: #EFF4FF;
}
QToolButton#qt_calendar_monthbutton, QToolButton#qt_calendar_yearbutton {
    background-color: transparent;
    border: none;
    color: #131722;
    font-size: 14px;
    font-weight: 800;
    padding: 6px 10px;
    border-radius: 8px;
}
QToolButton#qt_calendar_yearbutton { color: #6B7280; }
QToolButton#qt_calendar_monthbutton:hover, QToolButton#qt_calendar_yearbutton:hover {
    background-color: #EFF4FF;
    color: #2563EB;
}
QToolButton#qt_calendar_monthbutton::menu-indicator,
QToolButton#qt_calendar_yearbutton::menu-indicator { image: none; }
QSpinBox#qt_calendar_yearedit {
    background-color: #FFFFFF;
    border: 1.5px solid #E4E7EC;
    border-radius: 6px;
    color: #131722;
    selection-background-color: #2563EB;
    selection-color: #FFFFFF;
}
QTableView#qt_calendar_calendarview {
    background-color: #FFFFFF;
    alternate-background-color: #F7F8FA;
    border: none;
    selection-background-color: #2563EB;
    selection-color: #FFFFFF;
    outline: none;
    font-size: 13px;
}
/* Las celdas del calendario NO heredan el padding de las tablas:
   con 12px los numeros de dia no caben y Qt los recorta ("..."). */
QTableView#qt_calendar_calendarview::item {
    padding: 3px;
    border: none;
}
QTableView#qt_calendar_calendarview::item:hover {
    background-color: #EFF4FF;
    color: #131722;
}
QTableView#qt_calendar_calendarview::item:selected {
    background-color: #2563EB;
    color: #FFFFFF;
    font-weight: 700;
}

/* ================= Botones ================= */
QPushButton {
    background-color: #2563EB;
    color: #FFFFFF;
    border: none;
    border-radius: 8px;
    padding: 10px 20px;
    font-weight: 600;
    min-height: 28px;
}
QPushButton:hover { background-color: #1D4ED8; }
QPushButton:pressed { background-color: #1E40AF; }
QPushButton[variant="success"] { background-color: #16A34A; }
QPushButton[variant="success"]:hover { background-color: #15803D; }
QPushButton[variant="danger"] { background-color: #DC2626; }
QPushButton[variant="danger"]:hover { background-color: #B91C1C; }
QPushButton[variant="ghost"] {
    background-color: #FFFFFF;
    color: #131722;
    border: 1.5px solid #E4E7EC;
}
QPushButton[variant="ghost"]:hover { background-color: #F3F4F6; }
QPushButton[variant="soft"] { background-color: #EFF4FF; color: #2563EB; }
QPushButton[variant="soft"]:hover { background-color: #DCE7FD; }
QPushButton:disabled,
QPushButton[variant="success"]:disabled,
QPushButton[variant="danger"]:disabled,
QPushButton[variant="ghost"]:disabled,
QPushButton[variant="soft"]:disabled {
    background-color: #E9EBEF;
    color: #6B7280;
    border: 1px solid #E4E7EC;
}
QToolButton {
    background-color: transparent;
    border: none;
    border-radius: 6px;
    color: #131722;
    padding: 4px;
}
QToolButton:hover { background-color: #EFF4FF; }

/* ================= Tablas ================= */
QTableWidget, QTableView {
    background-color: #FFFFFF;
    alternate-background-color: #FFFFFF;
    border: 1px solid #E4E7EC;
    border-radius: 10px;
    gridline-color: transparent;
    selection-background-color: #EFF4FF;
    selection-color: #131722;
    outline: none;
}
QTableWidget::item, QTableView::item {
    padding: 12px 10px;
    border: none;
    border-bottom: 1px solid #F1F3F6;
    outline: none;
}
QTableWidget::item:selected, QTableView::item:selected {
    background-color: #EFF4FF;
    color: #1D4ED8;
    font-weight: 600;
    border: none;
    outline: none;
}
QHeaderView { background-color: transparent; border: none; }
QHeaderView::section {
    background-color: #F7F8FA;
    color: #6B7280;
    font-size: 11px;
    font-weight: 700;
    border: none;
    border-bottom: 1px solid #E4E7EC;
    padding: 10px;
}

/* ================= Tabs / grupos ================= */
QTabWidget::pane {
    background-color: #FFFFFF;
    border: 1px solid #E4E7EC;
    border-radius: 10px;
    top: -1px;
}
QTabBar::tab {
    background: transparent;
    color: #6B7280;
    font-weight: 600;
    padding: 10px 18px;
    border: none;
    border-bottom: 2px solid transparent;
}
QTabBar::tab:selected { color: #2563EB; border-bottom: 2px solid #2563EB; }
QTabBar::tab:hover { color: #131722; }
QGroupBox {
    background-color: #FFFFFF;
    border: 1px solid #E4E7EC;
    border-radius: 10px;
    margin-top: 14px;
    padding-top: 6px;
    font-weight: 700;
}
QGroupBox::title {
    subcontrol-origin: margin;
    left: 12px;
    padding: 0 6px;
    color: #6B7280;
    font-size: 11px;
}
QCheckBox, QRadioButton { spacing: 8px; background: transparent; }
QCheckBox::indicator {
    width: 18px; height: 18px;
    border: 1.5px solid #C9CED6;
    border-radius: 5px;
    background: #FFFFFF;
}
QCheckBox::indicator:hover { border-color: #2563EB; }
QCheckBox::indicator:checked {
    background-color: #2563EB;
    border-color: #2563EB;
    image: url(__CHECK_SVG__);
}
QCheckBox::indicator:checked:hover { background-color: #1D4ED8; }
QCheckBox::indicator:disabled { background-color: #EDF0F4; }
QRadioButton::indicator {
    width: 17px; height: 17px;
    border: 1.5px solid #C9CED6;
    border-radius: 9px;
    background: #FFFFFF;
}
QRadioButton::indicator:checked { background-color: #2563EB; border-color: #2563EB; }

/* ================= Progreso ================= */
QProgressBar {
    background-color: #EDF0F4;
    border: none;
    border-radius: 6px;
    text-align: center;
    color: #131722;
    font-size: 12px;
    font-weight: 600;
    min-height: 12px;
    max-height: 16px;
}
QProgressBar::chunk {
    background-color: #2563EB;
    border-radius: 6px;
}

/* ================= Deslizadores ================= */
QSlider::groove:horizontal {
    background-color: #EDF0F4;
    height: 6px;
    border-radius: 3px;
}
QSlider::handle:horizontal {
    background-color: #2563EB;
    width: 16px;
    height: 16px;
    margin: -5px 0;
    border-radius: 8px;
}
QSlider::groove:vertical {
    background-color: #EDF0F4;
    width: 6px;
    border-radius: 3px;
}
QSlider::handle:vertical {
    background-color: #2563EB;
    width: 16px;
    height: 16px;
    margin: 0 -5px;
    border-radius: 8px;
}
QSlider:disabled { background-color: transparent; }

/* ================= Scrollbars ================= */
QScrollBar:vertical { background: transparent; width: 8px; margin: 2px; }
QScrollBar::handle:vertical { background: #C9CED6; border-radius: 4px; min-height: 32px; }
QScrollBar::handle:vertical:hover { background: #9CA3AF; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
QScrollBar:horizontal { background: transparent; height: 8px; margin: 2px; }
QScrollBar::handle:horizontal { background: #C9CED6; border-radius: 4px; min-width: 32px; }
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal { width: 0; }

/* ================= Tooltip / menus ================= */
QToolTip {
    background-color: #131722;
    color: #F7F8FA;
    border: none;
    padding: 6px 10px;
    border-radius: 6px;
}
QMenuBar { background-color: #FFFFFF; border-bottom: 1px solid #E4E7EC; }
QMenuBar::item { padding: 6px 12px; background: transparent; border-radius: 4px; }
QMenuBar::item:selected { background-color: #EFF4FF; color: #2563EB; }
QMenu {
    background-color: #FFFFFF;
    border: 1px solid #E4E7EC;
    border-radius: 8px;
    padding: 4px;
}
QMenu::item {
    padding: 8px 24px 8px 12px;
    color: #131722;
    border-radius: 4px;
}
QMenu::item:selected { background-color: #EFF4FF; color: #2563EB; }
QMenu::item:disabled { color: #C9CED6; }
QMenu::separator { height: 1px; background-color: #E4E7EC; margin: 4px 8px; }

/* ================= Splitter ================= */
QSplitter::handle { background-color: #E4E7EC; }
QSplitter::handle:horizontal { width: 1px; }
QSplitter::handle:vertical { height: 1px; }
"""


def build_app_stylesheet() -> str:
    """Devuelve la hoja global. Un solo punto de cambio visual."""
    return GLOBAL_QSS.replace("__CHECK_SVG__", CHECK_SVG).replace("__CHEVRON_SVG__", CHEVRON_SVG)
