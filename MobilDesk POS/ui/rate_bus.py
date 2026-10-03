"""
Bus de eventos de la tasa USD/Bs.

Problema que resuelve: al cambiar la tasa, solo el Dashboard recibia la senal
'rate_changed' (dashboard_window.py lo conectaba a la ventana del modulo Tasa).
Las ventanas de Fiados, Ventas, Ticket y Reportes ya abiertas NO se enteraban, asi
que seguian mostrando saldos y precios con la tasa anterior hasta que el usuario
pulsaba a mano "Actualizar" en cada pantalla.

Este modulo centraliza la notificacion. Cualquier ventana puede suscribirse con
suscribir(callback) y se le llama en cuanto la tasa cambia, sin importar desde
donde se cambio (campo manual, boton BCV o el movil por sincronizacion).
"""
from PySide6.QtCore import QObject, Signal

# Se crea una sola vez por proceso. Las ventanas se suscriben a esta senal global
# en vez de encadenar la senal de cada modulo.
_rate_bus = None


class _RateBus(QObject):
    """Emisor global de 'la tasa cambio'."""
    changed = Signal()


def get_rate_bus():
    """Devuelve el bus global de tasa, creandolo la primera vez."""
    global _rate_bus
    if _rate_bus is None:
        _rate_bus = _RateBus()
    return _rate_bus


def notificar_cambio_tasa():
    """Avisa a todas las ventanas suscritas que la tasa cambio.

    Se llama desde donde se guarde la tasa: la ventana Tasa USD/Bs (manual y
    boton BCV) y tambien el sincronizador cuando el movil manda una tasa nueva.
    """
    bus = get_rate_bus()
    try:
        bus.changed.emit()
    except RuntimeError:
        # La aplicacion se esta cerrando y el objeto ya no es valido.
        pass


def suscribir(callback, parent=None):
    """Registra un callback que se ejecutara en cada cambio de tasa.

    Devuelve True si quedo suscrito. Nunca lanza: si algo falla, el resto de las
    ventanas deben seguir actualizándose igual.
    """
    try:
        bus = get_rate_bus()
        bus.changed.connect(callback)
        if parent is not None:
            # Vincular al ciclo de vida del padre para no acumular conexiones
            # muertas al cerrar y reabrir modulos.
            try:
                parent.destroyed.connect(lambda *_: bus.changed.disconnect(callback))
            except Exception:
                pass
        return True
    except Exception:
        return False