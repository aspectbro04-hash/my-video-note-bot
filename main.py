import os
import uuid
import subprocess
import telebot
from flask import Flask, request, abort

# ── Sozlamalar ──────────────────────────────────────────────────────────────
TOKEN    = os.environ.get("BOT_TOKEN", "8653825202:AAHnodl-HDT9R8R4jSd4AtbSU3xnVx8IzR0")
ADMIN_ID = int(os.environ.get("ADMIN_ID", "8049958379"))

# Render.com sizga bergan URL, masalan:
#   https://my-bot.onrender.com
APP_URL = os.environ.get("APP_URL", "").rstrip("/")

bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

# Fayllar uchun papka
os.makedirs("files", exist_ok=True)


# ── Yordamchi ────────────────────────────────────────────────────────────────
def is_admin(user_id: int) -> bool:
    return user_id == ADMIN_ID


# ── Handlers ─────────────────────────────────────────────────────────────────
@bot.message_handler(commands=["start"])
def cmd_start(message):
    if not is_admin(message.from_user.id):
        return
    bot.send_message(message.chat.id, "✅ Admin bot ishlayapti! (Webhook rejimi)")


@bot.message_handler(content_types=["document"])
def handle_file(message):
    if not is_admin(message.from_user.id):
        bot.reply_to(message, "⛔ Sizga ruxsat yo'q!")
        return

    if not message.document.file_name.endswith(".py"):
        bot.reply_to(message, "❌ Faqat .py fayl yubor!")
        return

    # Faylni yuklab olish
    file_info        = bot.get_file(message.document.file_id)
    downloaded_file  = bot.download_file(file_info.file_path)
    filename         = f"files/{uuid.uuid4()}.py"

    with open(filename, "wb") as f:
        f.write(downloaded_file)

    bot.reply_to(message, "🚀 Kod ishga tushyapti...")

    try:
        result = subprocess.run(
            ["python3", filename],
            capture_output=True,
            text=True,
            timeout=30          # Render free tier uchun 30s yetarli
        )
        output = (result.stdout + result.stderr).strip() or "Natija yo'q"
        bot.send_message(message.chat.id, f"📤 Natija:\n{output[:4000]}")

    except subprocess.TimeoutExpired:
        bot.send_message(message.chat.id, "⏱ Vaqt tugadi (30s limit)")

    except Exception as e:
        bot.send_message(message.chat.id, f"❌ Xatolik: {e}")

    finally:
        if os.path.exists(filename):
            os.remove(filename)


# ── Flask routes ──────────────────────────────────────────────────────────────
@app.route(f"/{TOKEN}", methods=["POST"])
def webhook():
    """Telegram bu URL-ga update yuboradi."""
    if request.headers.get("content-type") != "application/json":
        abort(400)
    json_str = request.get_data(as_text=True)
    update   = telebot.types.Update.de_json(json_str)
    bot.process_new_updates([update])
    return "OK", 200


@app.route("/set_webhook", methods=["GET"])
def set_webhook():
    """Birinchi marta yoki qayta ishga tushirganda webhook o'rnatadi."""
    if not APP_URL:
        return "APP_URL environment variable o'rnatilmagan!", 500
    url = f"{APP_URL}/{TOKEN}"
    result = bot.set_webhook(url=url)
    if result:
        return f"✅ Webhook o'rnatildi: {url}", 200
    return "❌ Webhook o'rnatishda xatolik", 500


@app.route("/", methods=["GET"])
def index():
    return "🤖 Bot ishlayapti!", 200


# ── Ishga tushirish ───────────────────────────────────────────────────────────
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
