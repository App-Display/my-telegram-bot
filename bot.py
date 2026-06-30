import os
import telebot
from telebot import types
import yt_dlp
import threading
import http.server
import time

# --- الإعدادات ---
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = "000000000"  # ضع هنا الآيدي الخاص بك

if not BOT_TOKEN:
    print("❌ خطأ: لم يتم العثور على BOT_TOKEN في إعدادات Railway!")
    exit(1)

bot = telebot.TeleBot(BOT_TOKEN)

# --- قائمة الأزرار (كما طلبتها تماماً) ---
def get_main_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
    btn_video = types.KeyboardButton('رابط فيديو 🎥')
    btn_edit = types.KeyboardButton('رابط تعديل ✨')
    btn_download = types.KeyboardButton('تحميل فيديو 📥')
    btn_news = types.KeyboardButton('أخبار وبث مباشر 🌐')
    btn_link = types.KeyboardButton('تلقيم رابط 💣')
    btn_photo = types.KeyboardButton('رابط صور 🖼️')
    markup.add(btn_video, btn_edit, btn_download, btn_news, btn_link, btn_photo)
    return markup

# --- حفظ المستخدمين ---
def save_user(chat_id):
    try:
        with open("users.txt", "a") as f:
            f.write(f"{chat_id}\n")
    except: pass

def get_users():
    if not os.path.exists("users.txt"): return []
    with open("users.txt", "r") as f:
        return list(set(f.read().splitlines()))

# --- سيرفر للبقاء نشطاً ---
def run_dummy_server():
    port = int(os.environ.get("PORT", 8080))
    httpd = http.server.HTTPServer(('', port), http.server.SimpleHTTPRequestHandler)
    httpd.serve_forever()

threading.Thread(target=run_dummy_server, daemon=True).start()

# --- دالة التحميل ---
def download_video(url, chat_id):
    file_path = f'/tmp/video_{chat_id}.mp4'
    ydl_opts = {'format': 'best', 'outtmpl': file_path, 'quiet': True}
    try:
        if os.path.exists(file_path): os.remove(file_path)
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            return file_path, info.get('title', 'Video')
    except Exception as e:
        return None, str(e)

# --- الأوامر ---
@bot.message_handler(commands=['start'])
def send_welcome(message):
    save_user(message.chat.id)
    bot.reply_to(message, "👋 أهلاً بك، المطور سيف الدين يرحب بك!", reply_markup=get_main_menu())

@bot.message_handler(commands=['announce'])
def announce(message):
    if str(message.chat.id) != ADMIN_ID: return
    users = get_users()
    bot.reply_to(message, "📢 جاري الإرسال...")
    for uid in users:
        try: bot.send_message(uid, "✅ تم إصلاح البوت بنجاح!")
        except: continue
    bot.reply_to(message, "✅ تم الإرسال.")

@bot.message_handler(func=lambda m: True)
def handle_all(message):
    save_user(message.chat.id)
    text = message.text
    if text.startswith("http"):
        status = bot.reply_to(message, "⏳ جاري التحميل...")
        path, title = download_video(text, message.chat.id)
        if path and os.path.exists(path):
            with open(path, 'rb') as v: bot.send_video(message.chat.id, v, caption=title)
            bot.delete_message(message.chat.id, status.message_id)
            os.remove(path)
        else:
            bot.edit_message_text(f"❌ خطأ: {title}", message.chat.id, status.message_id)
    else:
        bot.reply_to(message, "الرجاء إرسال رابط فيديو.", reply_markup=get_main_menu())

print("🤖 البوت يعمل بكامل ميزاته...")
bot.infinity_polling()
