"""Componentes UI reutilizables para MobilDesk POS (tema v2).

Aqui solo fabricas que asignan objectName/propiedades dinamicas del
tema (ui/theme.py). Sin logica de negocio, sin QSS local.
"""
from .cards import make_button, make_card, make_page_header, make_kpi
from .inputs import make_system_combo, make_system_input

__all__ = [
    "make_button",
    "make_card",
    "make_page_header",
    "make_kpi",
    "make_system_combo",
    "make_system_input",
]
