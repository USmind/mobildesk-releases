"""Componentes tarjeta/KPI/cabecera/boton — tema v2 (ui/theme.py).

Solo ganchos del tema: QFrame#card, #cardFlat, #kpi; QLabel#pageTitle,
#pageSubtitle, #sectionLabel, #money, #kpiValue, #kpiLabel; y
QPushButton[variant=success|danger|ghost|soft] (primary = sin variant).
Paleta #F7F8FA/#FFFFFF/#131722/#6B7280/#E4E7EC/#2563EB/#16A34A/#DC2626,
radio 8 en controles, altura minima 44px en botones.
"""
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame, QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget,
)

_VALID_VARIANTS = ("primary", "success", "danger", "ghost", "soft")


def make_button(text: str, variant: str = "primary", parent=None) -> QPushButton:
    btn = QPushButton(text, parent)
    if variant not in _VALID_VARIANTS:
        variant = "primary"
    if variant != "primary":
        btn.setProperty("variant", variant)
    btn.setMinimumHeight(44)
    btn.setCursor(Qt.PointingHandCursor)
    return btn


def make_card(parent=None, flat: bool = False) -> tuple[QFrame, QVBoxLayout]:
    card = QFrame(parent)
    card.setObjectName("cardFlat" if flat else "card")
    layout = QVBoxLayout(card)
    layout.setContentsMargins(20, 18, 20, 18)
    layout.setSpacing(12)
    return card, layout


def make_page_header(title: str, subtitle: str = "", parent=None) -> QWidget:
    box = QWidget(parent)
    lay = QVBoxLayout(box)
    lay.setContentsMargins(0, 0, 0, 0)
    lay.setSpacing(4)
    t = QLabel(title, box)
    t.setObjectName("pageTitle")
    lay.addWidget(t)
    if subtitle:
        s = QLabel(subtitle, box)
        s.setObjectName("pageSubtitle")
        s.setWordWrap(True)
        lay.addWidget(s)
    return box


def make_kpi(icon: str, label: str, value: str = "—", sub: str = "", parent=None) -> QFrame:
    frame = QFrame(parent)
    frame.setObjectName("kpi")
    row = QHBoxLayout(frame)
    row.setContentsMargins(20, 16, 20, 16)
    row.setSpacing(16)
    ico = QLabel(icon, frame)
    # Sin objectName propio: el tema v2 no define #kpiIcon; hereda QLabel base.
    ico.setAlignment(Qt.AlignCenter)
    ico.setFixedSize(48, 48)
    row.addWidget(ico)
    col = QVBoxLayout()
    col.setSpacing(2)
    lbl = QLabel(label, frame)
    lbl.setObjectName("kpiLabel")
    val = QLabel(value, frame)
    val.setObjectName("kpiValue")
    col.addWidget(lbl)
    col.addWidget(val)
    if sub:
        s = QLabel(sub, frame)
        # El tema v2 no define #kpiSub: se reutiliza #pageSubtitle (gris 13px).
        s.setObjectName("pageSubtitle")
        s.setWordWrap(True)
        col.addWidget(s)
        frame.sub_label = s
    row.addLayout(col, 1)
    frame.val_label = val
    frame.lbl_label = lbl
    return frame
