import os
import json
import time
import requests
from flask import Flask, request
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

# ================= SOZLAMALAR =================
TOKEN = '8668437374:AAHTDJAo1w_5uO3lmur1FfcCCvc5NAj2uoI'
ADMIN_ID = 8049958379  # Sening ID raqaming
CHANNEL_USERNAME = '@omadkl'  # Majburiy obuna uchun kanal
APP_URL = 'URLF'  # Web service manzili

bot = telebot.TeleBot(TOKEN)
server = Flask(__name__)
DB_FILE = 'users.json'

# ================= BAZA BILAN ISHLASH =================
def load_users():
    if not os.path.exists(DB_FILE):
        with open(DB_FILE, 'w') as f:
            json.dump([], f)
    with open(DB_FILE, 'r') as f:
        return json.load(f)

def save_user(user_id):
    users = load_users()
    if user_id not in users:
        users.append(user_id)
        with open(DB_FILE, 'w') as f:
            json.dump(users, f)

# ================= MAJBURIY OBUNA =================
def check_sub(user_id):
    try:
        member = bot.get_chat_member(CHANNEL_USERNAME, user_id)
        return member.status in ['creator', 'administrator', 'member']
    except Exception as e:
        print(f"Obunani tekshirishda xatolik: {e}")
        return False

def sub_keyboard():
    markup = InlineKeyboardMarkup()
    btn = InlineKeyboardButton(text="📢 Kanalga obuna bo'lish", url=f"https://t.me/{CHANNEL_USERNAME.replace('@', '')}")
    check_btn = InlineKeyboardButton(text="✅ Tasdiqlash", callback_data="check_sub")
    markup.add(btn)
    markup.add(check_btn)
    return markup

# ================= INSTAGRAM API =================
# Diqqat: Bu yerda RapidAPI (Instagram Downloader) ishlatilgan. 
# Bepul API kalitini https://rapidapi.com dan olishing kerak.
def download_instagram_video(url):
    try:
        api_url = "https://instagram-downloader-download-instagram-videos-stories.p.rapidapi.com/index"
        querystring = {"url": url}
        headers = {
            "X-RapidAPI-Key": "SENING_RAPIDAPI_KALITING", # Kalitni shu yerga qo'y
            "X-RapidAPI-Host": "instagram-downloader-download-instagram-videos-stories.p.rapidapi.com"
        }
        response = requests.get(api_url, headers=headers, params=querystring)
        data = response.json()
        
        if 'media' in data:
            return data['media'] # Video manzili qaytadi
        return None
    except Exception as e:
        print(f"API xatolik: {e}")
        return None

# ================= BOT BUYRUQLARI =================
@bot.message_handler(commands=['start'])
def start_cmd(message):
    save_user(message.chat.id)
    if not check_sub(message.chat.id):
        bot.send_message(message.chat.id, 
                         "<b>Botdan foydalanish uchun kanalimizga obuna bo'ling!</b>", 
                         parse_mode="HTML", reply_markup=sub_keyboard())
        return
    bot.send_message(message.chat.id, "⚡️ <b>Tizim tayyor.</b>\nInstagram video havolasini yuboring:", parse_mode="HTML")

@bot.callback_query_handler(func=lambda call: call.data == "check_sub")
def check_sub_callback(call):
    if check_sub(call.message.chat.id):
        bot.delete_message(call.message.chat.id, call.message.message_id)
        bot.send_message(call.message.chat.id, "✅ <b>Obuna tasdiqlandi!</b>\nEndi havola yuborishingiz mumkin.", parse_mode="HTML")
    else:
        bot.answer_callback_query(call.id, "Hali obuna bo'lmadingiz!", show_alert=True)

# ================= ADMIN PANEL =================
@bot.message_handler(commands=['admin'])
def admin_panel(message):
    if message.chat.id == ADMIN_ID:
        users = load_users()
        text = (f"🛠 <b>Admin Panel</b>\n\n"
                f"👥 Umumiy foydalanuvchilar: <b>{len(users)}</b> ta\n\n"
                f"<i>Hammaga xabar yuborish uchun:</i>\n"
                f"<code>/send Xabaringiz</code>")
        bot.send_message(message.chat.id, text, parse_mode="HTML")

@bot.message_handler(commands=['send'])
def broadcast(message):
    if message.chat.id == ADMIN_ID:
        text = message.text.replace('/send ', '')
        if not text or text == '/send':
            bot.send_message(ADMIN_ID, "Xabar matnini kiriting. Masalan: <code>/send Salom hammaga!</code>", parse_mode="HTML")
            return
        
        users = load_users()
        success, fail = 0, 0
        bot.send_message(ADMIN_ID, "⏳ Xabar yuborilmoqda, kuting...")
        
        for user_id in users:
            try:
                bot.send_message(user_id, text, parse_mode="HTML")
                success += 1
                time.sleep(0.05) # Telegram limitiga tushmaslik uchun (Flood Control)
            except:
                fail += 1
                
        bot.send_message(ADMIN_ID, f"✅ <b>Yakunlandi!</b>\n\nYuborildi: {success}\nXato: {fail}", parse_mode="HTML")

# ================= XABARLARNI QABUL QILISH =================
@bot.message_handler(content_types=['text'])
def handle_text(message):
    if not check_sub(message.chat.id):
        bot.send_message(message.chat.id, "Oldin obuna bo'ling!", reply_markup=sub_keyboard())
        return

    text = message.text
    if 'instagram.com' in text:
        wait_msg = bot.send_message(message.chat.id, "⏳ <i>Video yuklanmoqda... Bunga bir necha soniya ketishi mumkin.</i>", parse_mode="HTML")
        
        video_url = download_instagram_video(text)
        
        bot.delete_message(message.chat.id, wait_msg.message_id)
        
        if video_url:
            try:
                bot.send_video(message.chat.id, video_url, caption="🔥 @senning_kanaling orqali yuklandi!")
            except Exception:
                bot.send_message(message.chat.id, "❌ Videoni yuborishda xatolik yuz berdi. Fayl hajmi juda katta bo'lishi mumkin.")
        else:
            bot.send_message(message.chat.id, "❌ Havoladan videoni topib bo'lmadi yoki yopiq profil.")
    else:
        bot.send_message(message.chat.id, "Iltimos, faqat Instagram havolasini yuboring.")

# ================= FLASK WEBHOOK =================
@server.route('/' + TOKEN, methods=['POST'])
def getMessage():
    json_string = request.get_data().decode('utf-8')
    update = telebot.types.Update.de_json(json_string)
    bot.process_new_updates([update])
    return "!", 200

@server.route("/")
def webhook():
    bot.remove_webhook()
    # Webhookni o'rnatish
    bot.set_webhook(url=APP_URL + '/' + TOKEN)
    return "Tizim faol va Webhook ulangan!", 200

if __name__ == "__main__":
    # Serverni ishga tushirish (Hosting uchun port 0.0.0.0 va muhit porti)
    server.run(host="0.0.0.0", port=int(os.environ.get('PORT', 5000)))
