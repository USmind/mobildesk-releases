"""Inputs globales del sistema — tema v2 (ui/theme.py).

Trigger de 44px (task: inputs 44px+), focus azul 2px por QSS global,
popup con hover #F3F4F6 / seleccionado #EFF4FF/#2563EB, maximo 5
visibles con scroll sutil. Buscador (editable + completer) solo si hay
mas de 8 opciones. Cierre inteligente: nativo de Qt.
"""
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QComboBox, QCompleter, QLineEdit


def make_system_input(placeholder: str = "", parent=None) -> QLineEdit:
    box = QLineEdit(parent)
    if placeholder:
        box.setPlaceholderText(placeholder)
    box.setMinimumHeight(44)
    return box


def make_system_combo(
    items=None,
    parent=None,
    searchable: bool | None = None,
    max_visible: int = 5,
) -> QComboBox:
    """QComboBox estandar. `items` lista de str o tuplas (texto, data)."""
    box = QComboBox(parent)
    box.setMinimumHeight(44)
    box.setMaxVisibleItems(max_visible)
    box.view().setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)

    count = len(items or [])
    if searchable is None:
        searchable = count > 8
    box.setEditable(bool(searchable))
    if searchable:
        box.setInsertPolicy(QComboBox.NoInsert)
        completer = QCompleter([t if isinstance(t, str) else t[0] for t in (items or [])], box)
        completer.setCaseSensitivity(Qt.CaseInsensitive)
        completer.setFilterMode(Qt.MatchContains)
        box.setCompleter(completer)

    if items:
        for entry in items:
            if isinstance(entry, (tuple, list)):
                box.addItem(str(entry[0]), entry[1] if len(entry) > 1 else None)
            else:
                box.addItem(str(entry))
    return box
