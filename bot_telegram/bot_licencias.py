#!/usr/bin/env python3
"""
=============================================================================
🤖 MOBILDESK POS - BOT DE LICENCIAS PARA TELEGRAM
=============================================================================
Genera claves de activación oficiales para tus clientes directamente desde
tu teléfono celular a través de Telegram.

No requiere librerías externas (funciona con la librería estándar de Python).
=============================================================================
"""

import os
import sys
import json
import time
import hmac
import hashlib
import urllib.request
import urllib.parse
from datetime import datetime, timedelta

# Asegurar soporte de caracteres y emojis en consola Windows
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

# Clave secreta maestra del sistema MobilDesk POS
MASTER_SECRET = b"KIOSKO_POS_PROTECTED_MASTER_SECRET_2026_V1"

CONFIG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")


def load_config():
    """Carga la configuración o crea una plantilla si no existe."""
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass

    default_config = {
        "BOT_TOKEN": "PEGA_AQUI_EL_TOKEN_DE_BOTFATHER",
        "ADMIN_USER_IDS": [],  # Ejemplo: [123456789] Tu ID de Telegram
        "PASSWORD_AUTORIZACION": "mobiladmin2026"  # Clave para autorizarte si no sabes tu ID
    }
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(default_config, f, indent=4)
    return default_config


def save_config(config):
    """Guarda la configuración actualizada."""
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=4)
    except Exception as e:
        print(f"Error al guardar config: {e}")


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


class TelegramBot:
    def __init__(self, token: str):
        self.token = token.strip()
        self.api_url = f"https://api.telegram.org/bot{self.token}"
        self.offset = 0

    def call_api(self, method: str, data: dict = None) -> dict:
        """Realiza una petición a la API de Telegram."""
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
        except urllib.error.HTTPError as e:
            err_body = e.read().decode("utf-8", errors="ignore")
            print(f"❌ Error HTTP Telegram ({e.code}): {err_body}")
            return {"ok": False, "description": err_body}
        except Exception as e:
            print(f"❌ Error de red: {e}")
            return {"ok": False, "description": str(e)}

    def get_updates(self) -> list:
        """Obtiene nuevos mensajes (long polling)."""
        res = self.call_api("getUpdates", {"offset": self.offset, "timeout": 20})
        if res.get("ok"):
            return res.get("result", [])
        return []

    def send_message(self, chat_id: int, text: str, reply_markup: dict = None, parse_mode: str = "HTML"):
        """Envía un mensaje formateado al usuario."""
        payload = {
            "chat_id": chat_id,
            "text": text,
            "parse_mode": parse_mode
        }
        if reply_markup:
            payload["reply_markup"] = reply_markup
        return self.call_api("sendMessage", payload)

    def answer_callback_query(self, callback_query_id: str, text: str = None):
        """Responde a un clic en un botón interactivo."""
        payload = {"callback_query_id": callback_query_id}
        if text:
            payload["text"] = text
        return self.call_api("answerCallbackQuery", payload)


def handle_message(bot: TelegramBot, msg: dict, config: dict):
    chat = msg.get("chat", {})
    chat_id = chat.get("id")
    user = msg.get("from", {})
    user_id = user.get("id")
    text = (msg.get("text") or "").strip()

    admin_ids = config.get("ADMIN_USER_IDS", [])
    auth_pass = config.get("PASSWORD_AUTORIZACION", "mobiladmin2026")

    # Autorización con contraseña
    if text.startswith("/auth ") or text.startswith("/login "):
        parts = text.split(" ", 1)
        pwd = parts[1].strip() if len(parts) > 1 else ""
        if pwd == auth_pass:
            if user_id not in admin_ids:
                admin_ids.append(user_id)
                config["ADMIN_USER_IDS"] = admin_ids
                save_config(config)
            bot.send_message(
                chat_id,
                f"✅ <b>¡Acceso Autorizado!</b>\n\nTu ID de Telegram (<code>{user_id}</code>) ha sido registrado como Administrador Oficial de MobilDesk POS."
            )
            return
        else:
            bot.send_message(chat_id, "❌ <b>Contraseña incorrecta.</b>")
            return

    # Verificar si el usuario es administrador
    if admin_ids and user_id not in admin_ids:
        bot.send_message(
            chat_id,
            f"⛔ <b>Acceso Restringido</b>\n\nEste es el bot privado de licencias de MobilDesk POS.\n"
            f"Si eres el dueño, escribe:\n<code>/auth TU_CONTRASEÑA</code>\n\nTu User ID: <code>{user_id}</code>"
        )
        return

    # Si es primera vez y no hay admins configurados
    if not admin_ids:
        admin_ids.append(user_id)
        config["ADMIN_USER_IDS"] = admin_ids
        save_config(config)
        bot.send_message(
            chat_id,
            f"👑 <b>¡Bienvenido, Dueño de MobilDesk!</b>\n\nHas sido registrado automáticamente como Administrador Principal (ID: <code>{user_id}</code>)."
        )

    # Comandos
    if text in ("/start", "/help", "/inicio"):
        bot.send_message(
            chat_id,
            "👋 <b>Bienvenido al Generador de Licencias MobilDesk POS</b>\n\n"
            "📱 <b>¿Cómo generar una clave para un cliente?</b>\n"
            "Solo <b>envíame el Código de Computadora (Machine ID)</b> que te mandó el cliente por WhatsApp (ejemplo: <code>KP-89FA-31BC-10D2</code>).\n\n"
            "Te mostraré los planes para elegir con un solo toque y te entregaré el mensaje listo para reenviarle."
        )
        return

    # Detectar Machine ID
    clean_text = text.upper().replace(" ", "").replace("\n", "")
    if clean_text.startswith("KP-") or len(clean_text) >= 8:
        machine_id = clean_text

        # Botones interactivos con los planes
        keyboard = {
            "inline_keyboard": [
                [
                    {"text": "💎 Vitalicio (Permanente)", "callback_data": f"gen:V:{machine_id}"}
                ],
                [
                    {"text": "📅 Anual (365 Días)", "callback_data": f"gen:A:{machine_id}"},
                    {"text": "⏳ Mensual (30 Días)", "callback_data": f"gen:M:{machine_id}"}
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


def handle_callback_query(bot: TelegramBot, cb: dict, config: dict):
    cb_id = cb.get("id")
    chat = cb.get("message", {}).get("chat", {})
    chat_id = chat.get("id")
    user_id = cb.get("from", {}).get("id")
    data = cb.get("data", "")

    admin_ids = config.get("ADMIN_USER_IDS", [])
    if admin_ids and user_id not in admin_ids:
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


def main():
    print("=" * 65)
    print("🤖 MOBILDESK POS - BOT DE LICENCIAS PARA TELEGRAM")
    print("=" * 65)

    config = load_config()
    token = config.get("BOT_TOKEN", "").strip()

    if not token or token == "PEGA_AQUI_EL_TOKEN_DE_BOTFATHER":
        print("\n⚠️ CONFIGURACIÓN INICIAL DEL BOT:")
        print("1. Abre Telegram y busca a @BotFather.")
        print("2. Envía /newbot, dale un nombre y copia el TOKEN HTTP API.")
        print("-" * 65)
        try:
            token = input("👉 Pega tu Token de Telegram aquí: ").strip()
            if token:
                config["BOT_TOKEN"] = token
                save_config(config)
            else:
                print("❌ No se ingresó token. Edita el archivo config.json.")
                return
        except (KeyboardInterrupt, EOFError):
            return

    bot = TelegramBot(token)

    # Probar conexión
    me = bot.call_api("getMe")
    if not me.get("ok"):
        print(f"\n❌ Error al conectar con Telegram: {me.get('description')}")
        print("Verifica que el token sea correcto en config.json.")
        return

    bot_info = me.get("result", {})
    print(f"\n✅ Bot Conectado Exitosamente: @{bot_info.get('username')} ({bot_info.get('first_name')})")
    print("🚀 El bot está escuchando mensajes en tiempo real...")
    print("👉 Abre Telegram en tu teléfono, busca a tu bot y envíale /start")
    print("Para salir presiona Ctrl + C.\n")

    while True:
        try:
            updates = bot.get_updates()
            for u in updates:
                bot.offset = u["update_id"] + 1

                if "message" in u:
                    handle_message(bot, u["message"], config)
                elif "callback_query" in u:
                    handle_callback_query(bot, u["callback_query"], config)

            time.sleep(0.5)
        except KeyboardInterrupt:
            print("\n🛑 Bot detenido.")
            break
        except Exception as e:
            print(f"⚠️ Error en bucle: {e}")
            time.sleep(2)


if __name__ == "__main__":
    main()
