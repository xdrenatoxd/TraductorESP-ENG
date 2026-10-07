import os
import threading
import warnings
from flask import Flask
from openai import OpenAI
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

warnings.filterwarnings("ignore")

# Carga segura de .env para pruebas locales
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# ================= CONFIGURACIÓN SEGURA =================
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
PORT = int(os.environ.get("PORT", 10000))

# Modelos elegidos para máxima velocidad y calidad
MODELOS_FALLBACK = [
    "nvidia/nemotron-3.5-lightning:free",
    "nvidia/nemotron-3-super-120b-a12b:free",
    "meta-llama/llama-3-8b-instruct:free"
]
# =======================================================

ai_client = OpenAI(
    api_key=OPENROUTER_API_KEY,
    base_url="https://openrouter.ai/api/v1",
)

# Micro-servidor web para mantener viva la app en Render
web_app = Flask(__name__)

@web_app.route("/")
def home():
    return "Bot Traductor Bidireccional activo y funcionando 🚀"

def run_web():
    web_app.run(host="0.0.0.0", port=PORT)

# ---------- COMANDOS TELEGRAM ----------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    saludo = (
        "🔄 **¡Hola! Soy tu Traductor Nativo Bidireccional** 🇺🇸/🇪🇸\n\n"
        "• Si me escribes en **Español**, lo traduciré a un Inglés natural y conversacional.\n"
        "• Si me escribes en **Inglés**, lo traduciré a un Español exacto y fluido.\n\n"
        "¡No tienes que usar comandos, solo envíame el texto!"
    )
    await update.message.reply_text(saludo, parse_mode="Markdown")

async def traducir_texto(update: Update, context: ContextTypes.DEFAULT_TYPE):
    texto_usuario = update.message.text.strip()
    if not texto_usuario:
        return

    # ⚡ OPTIMIZACIÓN DE VELOCIDAD 1: 
    # Muestra "Escribiendo..." en Telegram en vez de enviar un mensaje de texto previo.
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action='typing')

    prompt_sistema = (
        "Eres un traductor bilingüe nativo experto (Inglés y Español). "
        "Tu único trabajo es detectar el idioma del texto del usuario y traducirlo al otro idioma: "
        "1. Si el texto está en Español, tradúcelo a un Inglés conversacional, natural y fluido, adaptando jergas al contexto nativo. "
        "2. Si el texto está en Inglés, tradúcelo a un Español exacto, natural y fluido, evitando traducciones literales o robóticas. "
        "NO des explicaciones sobre el idioma detectado, NO agregues notas, NO pongas comillas. "
        "SOLO devuelve el texto final traducido listo para ser copiado."
    )

    try:
        response = ai_client.chat.completions.create(
            extra_body={"models": MODELOS_FALLBACK},
            model=MODELOS_FALLBACK[0],
            messages=[
                {"role": "system", "content": prompt_sistema},
                {"role": "user", "content": texto_usuario},
            ],
            temperature=0.3,
            max_tokens=1500,
        )

        traduccion = response.choices[0].message.content.strip()

        # ⚡ OPTIMIZACIÓN DE VELOCIDAD 2: 
        # Envía la respuesta final directamente (ahorra los segundos de editar el mensaje de espera).
        await update.message.reply_text(traduccion)

    except Exception as e:
        await update.message.reply_text(f"❌ Error al traducir: {str(e)}")

def main():
    threading.Thread(target=run_web, daemon=True).start()

    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), traducir_texto))

    print("🤖 Bot Traductor Bidireccional optimizado activo...")
    app.run_polling()

if __name__ == "__main__":
    main()
