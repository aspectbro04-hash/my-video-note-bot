
from flask import Flask, request
import telebot
import os
import subprocess
import uuid

TOKEN = os.environ.get("BOT_TOKEN")
ADMIN_ID = int(os.environ.get("ADMIN_ID", "123456789"))

bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

if not os.path.exists("files"):
    os.mkdir("files")

def is_admin(user_id):
    return user_id == ADMIN_ID

@bot.message_handler(commands=['start'])
def start(message):
    if not is_admin(message.from_user.id):
        return
    bot.send_message(message.chat.id, "✅ Admin bot ishlayapti (Flask Webhook)!")

@bot.message_handler(content_types=['document'])
def handle_file(message):
    if not is_admin(message.from_user.id):
        bot.reply_to(message, "⛔ Sizga ruxsat yo'q!")
        return

    if not message.document.file_name.endswith(".py"):
        bot.reply_to(message, "❌ Faqat .py fayl yubor!")
        return

    file_info = bot.get_file(message.document.file_id)
    downloaded_file = bot.download_file(file_info.file_path)

    filename = f"files/{uuid.uuid4()}.py"
    with open(filename, 'wb') as f:
        f.write(downloaded_file)

    bot.reply_to(message, "🚀 Kod ishga tushyapti...")

    try:
        result = subprocess.run(
            ["python", filename],
            capture_output=True,
            text=True,
            timeout=5
        )

        output = result.stdout + result.stderr
        if not output.strip():
            output = "Natija yo'q"

        bot.send_message(message.chat.id, f"📤 Natija:\n{output[:4000]}")

    except subprocess.TimeoutExpired:
        bot.send_message(message.chat.id, "⏱ Vaqt tugadi (5s limit)")

    except Exception as e:
        bot.send_message(message.chat.id, f"❌ Xatolik: {e}")

    finally:
        if os.path.exists(filename):
            os.remove(filename)

@app.route('/', methods=['GET'])
def home():
    return "Bot ishlayapti!"

@app.route(f"/{TOKEN}", methods=['POST'])
def webhook():
    json_str = request.get_data().decode('UTF-8')
    update = telebot.types.Update.de_json(json_str)
    bot.process_new_updates([update])
    return "ok", 200

if __name__ == "__main__":
    bot.remove_webhook()
    bot.set_webhook(url=f"https://YOUR-RENDER-URL.onrender.com/{TOKEN}")
    app.run(host="0.0.0.0", port=int(os.environ.get('PORT', 5000)))
