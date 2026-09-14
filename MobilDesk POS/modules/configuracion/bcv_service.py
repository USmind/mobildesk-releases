"""Servicio para obtener la tasa oficial del BCV automáticamente.

Fuente: https://bcv.today/api/v1/rate.json (gratis, sin API key)
La API retorna JSON con las tasas de todas las monedas: USD, EUR, CNY, TRY, RUB.
"""

import json
import urllib.request
import urllib.error
from datetime import datetime

BCV_API_URL = "https://bcv.today/api/v1/rate.json"
REQUEST_TIMEOUT = 15  # segundos


def fetch_bcv_rate():
    """Obtiene la tasa oficial USD/Bs del BCV.

    Returns:
        dict: {"rate": float, "date": str, "updated_at": str} o None si falla.
    """
    try:
        req = urllib.request.Request(
            BCV_API_URL,
            headers={
                "Accept": "application/json",
                "User-Agent": "MobilDesk-POS/1.2",
                "Cache-Control": "no-cache",
            },
        )
        with urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT) as resp:
            data = json.loads(resp.read().decode("utf-8"))

        usd_rate = data.get("USD")
        if usd_rate is None or float(usd_rate) <= 0:
            return None

        return {
            "rate": float(usd_rate),
            "date": data.get("date", ""),
            "updated_at": data.get("updated_at", ""),
            "effective_date": data.get("effective_date", ""),
        }
    except (urllib.error.URLError, json.JSONDecodeError, ValueError, OSError):
        return None


def fetch_and_apply_rate(usuario_id=None):
    """Obtiene la tasa BCV y la aplica al sistema.

    Returns:
        tuple: (bool_exito, str_mensaje)
    """
    from modules.configuracion.exchange_rate_service import set_exchange_rate

    result = fetch_bcv_rate()
    if result is None:
        return False, "No se pudo obtener la tasa del BCV. Verifica tu conexión a Internet."

    rate = result["rate"]
    try:
        set_exchange_rate(rate, usuario_id)
        fecha = result.get("date", datetime.now().strftime("%Y-%m-%d"))
        return True, f"Tasa BCV actualizada: 1 USD = Bs {rate:,.2f} (fecha: {fecha})"
    except Exception as e:
        return False, f"Error al guardar la tasa: {e}"
