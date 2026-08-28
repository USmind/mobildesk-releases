#!/usr/bin/env python3
"""
=============================================================================
🤖 MOBILDESK POS - BOT DE LICENCIAS TELEGRAM (EDICIÓN CLOUD 24/7 PARA RENDER)
=============================================================================
Servicio optimizado para Render.com, Railway, PythonAnywhere y VPS.
Incluye servidor HTTP integrado de salud para el plan gratuito de Render.
=============================================================================
"""

import os
import sys
import json
import time
import hmac
import hashlib
import threading
import urllib.request
import urllib.parse
from datetime import datetime, timedelta
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

# Configurar soporte de codificación UTF-8
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

# Clave secreta maestra del sistema MobilDesk POS
MASTER_SECRET = b"KIOSKO_POS_PROTECTED_MASTER_SECRET_2026_V1"

# Configuración (Soporta Variables de Entorno de Render y archivo local)
BOT_TOKEN = os.environ.get("BOT_TOKEN", "8423198089:AAE88-5Er5Isjlu4_dGGnfsYboqRgv6613k").strip()
PASSWORD_AUTORIZACION = os.environ.get("PASSWORD_AUTORIZACION", "mobiladmin2026").strip()
ADMIN_USER_IDS = []

# Cargar IDs guardados si existen
env_admins = os.environ.get("ADMIN_USER_IDS", "")
if env_admins:
    try:
        ADMIN_USER_IDS = [int(x.strip()) for x in env_admins.split(",") if x.strip().isdigit()]
    except Exception:
        pass


def generate_license_key(machine_id: str, plan: str, days: int = 365) -> str:
    """Genera una clave criptográfica de activación idéntica al sistema MobilDesk."""
    clean_mid = machine_id.strip().upper()
    plan_code = plan.upper()

    if plan_code == "V":  # Vitalicio / Permanente
        expiry_ts = 0
    else:
        expiry_date = datetime.now() + timedelta(days=days)
        expiry_ts = int(expiry_date.timestamp())

    expiry_hex = f"{expiry_ts:08X}"
    payload = f"{clean_mid}|{plan_code}|{expiry_hex}"
    signature = hmac.new(MASTER_SECRET, payload.encode("utf-8"), hashlib.sha256).hexdigest().upper()[:8]

    return f"KP-{plan_code}-{expiry_hex}-{signature}"


def validate_license_key(machine_id: str, key: str) -> tuple:
    """
    Valida una clave de activación contra el Machine ID (SOLO SERVIDOR).
    El secreto maestro NUNCA se distribuye en el instalador del cliente.
    Retorna (estado, mensaje, detalles) donde estado es:
    'valida' | 'invalida'
    """
    try:
        parts = key.strip().upper().split("-")
        if len(parts) != 4 or parts[0] != "KP":
            return "invalida", "Formato de clave de activación no válido.", {}

        plan_code = parts[1]
        expiry_hex = parts[2]
        received_sig = parts[3]

        if plan_code not in ("M", "A", "V", "D"):
            return "invalida", "Tipo de plan desconocido en la clave.", {}

        clean_mid = machine_id.strip().upper()
        payload = f"{clean_mid}|{plan_code}|{expiry_hex}"
        expected_sig = hmac.new(MASTER_SECRET, payload.encode("utf-8"), hashlib.sha256).hexdigest().upper()[:8]

        if not hmac.compare_digest(received_sig, expected_sig):
            return "invalida", "La clave ingresada no corresponde a este equipo.", {}

        if plan_code == "V":
            return "valida", "Clave válida", {
                "plan_codigo": plan_code,
                "plan_nombre": "Plan Vitalicio / Permanente",
                "fecha_expiracion": "Permanente (Sin Vencimiento)",
                "fecha_expiracion_iso": "9999-12-31T23:59:59",
                "dias_restantes": 99999
            }

        expiry_ts = int(expiry_hex, 16)
        expiry_date = datetime.fromtimestamp(expiry_ts)
        now = datetime.now()
        if expiry_date < now:
            return "invalida", f"Esta clave de activación expiró el {expiry_date.strftime('%d/%m/%Y')}.", {}

        dias_restantes = max(0, (expiry_date - now).days)
        plan_nombres = {
            "M": "Plan Mensual (30 Días)",
            "A": "Plan Anual (365 Días)",
            "D": "Demo de Prueba Extendida"
        }
        return "valida", "Clave válida", {
            "plan_codigo": plan_code,
            "plan_nombre": plan_nombres.get(plan_code, "Plan Activo"),
            "fecha_expiracion": expiry_date.strftime("%d/%m/%Y"),
            "fecha_expiracion_iso": expiry_date.isoformat(),
            "dias_restantes": dias_restantes
        }
    except Exception as err:
        return "invalida", f"Error al procesar la clave: {err}", {}


class TelegramBot:
    def __init__(self, token: str):
        self.token = token.strip()
        self.api_url = f"https://api.telegram.org/bot{self.token}"
        self.offset = 0

    def call_api(self, method: str, data: dict = None) -> dict:
        url = f"{self.api_url}/{method}"
        try:
            if data:
                json_data = json.dumps(data).encode("utf-8")
                req = urllib.request.Request(
                    url,
                    data=json_data,
                    headers={"Content-Type": "application/json"}
                )
            else:
                req = urllib.request.Request(url)

            with urllib.request.urlopen(req, timeout=30) as response:
                return json.loads(response.read().decode("utf-8"))
        except Exception as e:
            print(f"Error API Telegram: {e}")
            return {"ok": False, "description": str(e)}

    def get_updates(self) -> list:
        res = self.call_api("getUpdates", {"offset": self.offset, "timeout": 20})
        if res.get("ok"):
            return res.get("result", [])
        return []

    def send_message(self, chat_id: int, text: str, reply_markup: dict = None, parse_mode: str = "HTML"):
        payload = {
            "chat_id": chat_id,
            "text": text,
            "parse_mode": parse_mode
        }
        if reply_markup:
            payload["reply_markup"] = reply_markup
        return self.call_api("sendMessage", payload)

    def answer_callback_query(self, callback_query_id: str, text: str = None):
        payload = {"callback_query_id": callback_query_id}
        if text:
            payload["text"] = text
        return self.call_api("answerCallbackQuery", payload)


def handle_message(bot: TelegramBot, msg: dict):
    global ADMIN_USER_IDS
    chat = msg.get("chat", {})
    chat_id = chat.get("id")
    user = msg.get("from", {})
    user_id = user.get("id")
    text = (msg.get("text") or "").strip()

    # Autorización con contraseña
    if text.startswith("/auth ") or text.startswith("/login "):
        parts = text.split(" ", 1)
        pwd = parts[1].strip() if len(parts) > 1 else ""
        if pwd == PASSWORD_AUTORIZACION:
            if user_id not in ADMIN_USER_IDS:
                ADMIN_USER_IDS.append(user_id)
            bot.send_message(
                chat_id,
                f"✅ <b>¡Acceso Autorizado!</b>\n\nTu ID de Telegram (<code>{user_id}</code>) ha sido registrado como Administrador Oficial de MobilDesk POS."
            )
            return
        else:
            bot.send_message(chat_id, "❌ <b>Contraseña incorrecta.</b>")
            return

    # Verificar si es administrador
    if ADMIN_USER_IDS and user_id not in ADMIN_USER_IDS:
        bot.send_message(
            chat_id,
            f"⛔ <b>Acceso Restringido</b>\n\nEste es el bot privado de licencias de MobilDesk POS.\n"
            f"Si eres el dueño, escribe:\n<code>/auth TU_CONTRASEÑA</code>\n\nTu User ID: <code>{user_id}</code>"
        )
        return

    # Si es primera vez y no hay admins
    if not ADMIN_USER_IDS:
        ADMIN_USER_IDS.append(user_id)
        bot.send_message(
            chat_id,
            f"👑 <b>¡Bienvenido, Dueño de MobilDesk!</b>\n\nHas sido registrado automáticamente como Administrador Principal (ID: <code>{user_id}</code>)."
        )

    # Menú de inicio
    if text in ("/start", "/help", "/inicio"):
        bot.send_message(
            chat_id,
            "👋 <b>Bienvenido al Generador de Licencias MobilDesk POS (Cloud 24/7)</b>\n\n"
            "📱 <b>¿Cómo generar una clave para un cliente?</b>\n"
            "Solo <b>envíame el Código de Computadora (Machine ID)</b> que te mandó el cliente por WhatsApp (ejemplo: <code>KP-89FA-31BC-10D2</code>).\n\n"
            "Te mostraré los planes para elegir con un solo toque y te entregaré el mensaje listo para reenviarle."
        )
        return

    # Procesar Machine ID
    clean_text = text.upper().replace(" ", "").replace("\n", "")
    if clean_text.startswith("KP-") or len(clean_text) >= 8:
        machine_id = clean_text

        keyboard = {
            "inline_keyboard": [
                [
                    {"text": "💎 Vitalicio (Permanente - $15)", "callback_data": f"gen:V:{machine_id}"}
                ],
                [
                    {"text": "📅 Anual (365 Días - $10)", "callback_data": f"gen:A:{machine_id}"},
                    {"text": "⏳ Mensual (30 Días - $5)", "callback_data": f"gen:M:{machine_id}"}
                ],
                [
                    {"text": "🎁 Demo Extendida (15 Días)", "callback_data": f"gen:D:{machine_id}"}
                ]
            ]
        }

        bot.send_message(
            chat_id,
            f"💻 <b>Código de Computadora detectado:</b>\n<code>{machine_id}</code>\n\n"
            "👇 <b>Selecciona el plan que compró el cliente:</b>",
            reply_markup=keyboard
        )
    else:
        bot.send_message(
            chat_id,
            "⚠️ <b>Formato no reconocido</b>\n\nPor favor envía el Código de Computadora del cliente (ejemplo: <code>KP-A1B2-C3D4-E5F6</code>)."
        )


def handle_callback_query(bot: TelegramBot, cb: dict):
    global ADMIN_USER_IDS
    cb_id = cb.get("id")
    chat = cb.get("message", {}).get("chat", {})
    chat_id = chat.get("id")
    user_id = cb.get("from", {}).get("id")
    data = cb.get("data", "")

    if ADMIN_USER_IDS and user_id not in ADMIN_USER_IDS:
        bot.answer_callback_query(cb_id, "Acceso no autorizado.")
        return

    if data.startswith("gen:"):
        parts = data.split(":")
        plan_code = parts[1]
        machine_id = parts[2]

        plan_dias = {"V": 0, "A": 365, "M": 30, "D": 15}
        plan_nombres = {
            "V": "Vitalicio / Permanente (Sin Vencimiento)",
            "A": "Plan Anual (1 Año - 365 Días)",
            "M": "Plan Mensual (30 Días)",
            "D": "Demo de Prueba Extendida (15 Días)"
        }

        dias = plan_dias.get(plan_code, 365)
        nombre_plan = plan_nombres.get(plan_code, "Plan Activo")

        clave = generate_license_key(machine_id, plan_code, dias)
        bot.answer_callback_query(cb_id, "¡Clave generada!")

        msg_whatsapp = (
            f"¡Hola! Gracias por tu compra.\n\n"
            f"Aquí tienes tu clave de activación oficial para *MobilDesk POS*:\n\n"
            f"🔑 *Clave:* {clave}\n"
            f"📦 *Plan:* {nombre_plan}\n"
            f"💻 *Equipo:* {machine_id}\n\n"
            f"👉 *Pasos para activar:*\n"
            f"1. Abre MobilDesk POS en tu computadora.\n"
            f"2. Ingresa al menú *'Activar Licencia'* en la barra lateral.\n"
            f"3. Pega la clave y presiona *'Activar Licencia'*.\n\n"
            f"¡Tu sistema quedará 100% desbloqueado!"
        )

        respuesta = (
            f"✅ <b>¡LICENCIA GENERADA CON ÉXITO!</b>\n\n"
            f"📦 <b>Plan:</b> {nombre_plan}\n"
            f"💻 <b>Equipo:</b> <code>{machine_id}</code>\n\n"
            f"🔑 <b>Clave de Activación (Toca para copiar):</b>\n"
            f"<code>{clave}</code>\n\n"
            f"➖➖➖➖➖➖➖➖➖➖➖➖\n"
            f"📲 <b>Mensaje listo para reenviar a WhatsApp:</b>\n\n"
            f"<pre>{msg_whatsapp}</pre>"
        )

        bot.send_message(chat_id, respuesta)


# =============================================================================
# SERVIDOR HTTP PARA RENDER.COM
# - GET /         -> Página de estado (para UptimeRobot / pings)
# - GET /activar  -> Validación de claves de licencia (el secreto vive SOLO aquí)
# =============================================================================
class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path == "/activar":
            self.handle_activar(parse_qs(parsed.query))
        else:
            self.handle_health()

    def _send_json(self, obj, status=200):
        body = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def handle_activar(self, params):
        machine_id = (params.get("machine_id", [""])[0] or "").strip()
        clave = (params.get("clave", [""])[0] or "").strip()

        if not machine_id or not clave:
            self._send_json({"ok": False, "error": "Faltan parámetros: machine_id y clave."}, status=400)
            return

        estado, mensaje, detalles = validate_license_key(machine_id, clave)

        if estado != "valida":
            print(f"⛔ Activación rechazada | Equipo: {machine_id} | Motivo: {mensaje}")
            self._send_json({"ok": False, "error": mensaje})
            return

        print(f"✅ Activación válida | Equipo: {machine_id} | Plan: {detalles['plan_nombre']}")
        respuesta = {"ok": True}
        respuesta.update(detalles)
        self._send_json(respuesta)

    def handle_health(self):
        self.send_response(200)
        self.send_header("Content-type", "text/html; charset=utf-8")
        self.end_headers()
        html = """
        <!DOCTYPE html>
        <html>
        <head><title>MobilDesk KeyBot Cloud</title></head>
        <body style="font-family:sans-serif; text-align:center; padding:50px; background:#0f172a; color:white;">
            <h1>🤖 MobilDesk KeyBot 24/7 Activo</h1>
            <p style="color:#22c55e; font-size:18px;"><b>Estado: ONLINE y Escuchando Telegram</b></p>
            <p>Servidor en la nube para generación remota de licencias MobilDesk POS.</p>
            <p style="color:#64748b; font-size:13px;">Endpoint de activación: <code>/activar?machine_id=...&amp;clave=...</code></p>
        </body>
        </html>
        """
        self.wfile.write(html.encode("utf-8"))

    def log_message(self, format, *args):
        pass  # Silenciar logs http en consola


def run_health_server():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(("0.0.0.0", port), HealthHandler)
    print(f"🌐 Servidor HTTP de salud activo en el puerto {port}")
    server.serve_forever()


def main():
    print("=" * 65)
    print("🤖 MOBILDESK POS - BOT DE LICENCIAS CLOUD (RENDER 24/7)")
    print("=" * 65)

    # Iniciar servidor HTTP en segundo plano para que Render no suspenda el servicio
    http_thread = threading.Thread(target=run_health_server, daemon=True)
    http_thread.start()

    bot = TelegramBot(BOT_TOKEN)
    me = bot.call_api("getMe")
    if not me.get("ok"):
        print(f"❌ Error al conectar bot: {me.get('description')}")
        return

    bot_info = me.get("result", {})
    print(f"✅ Bot Conectado: @{bot_info.get('username')} ({bot_info.get('first_name')})")
    print("🚀 Escuchando mensajes en la nube 24/7...")

    while True:
        try:
            updates = bot.get_updates()
            for u in updates:
                bot.offset = u["update_id"] + 1
                if "message" in u:
                    handle_message(bot, u["message"])
                elif "callback_query" in u:
                    handle_callback_query(bot, u["callback_query"])
            time.sleep(0.5)
        except Exception as e:
            print(f"⚠️ Error en ciclo bot: {e}")
            time.sleep(2)


if __name__ == "__main__":
    main()
