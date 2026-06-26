import os
import json
import telebot
from telebot import types
from PIL import Image, PngImagePlugin
import threading
import http.server
import yt_dlp

BOT_TOKEN = os.getenv("BOT_TOKEN", "8128965245:AAGolmLae3ALVga_kcloXCK2zsFRODK4BXc")
bot = telebot.TeleBot(BOT_TOKEN)

DB_FILE = "/tmp/voice_db.json"
user_states = {}

def run_dummy_server():
    try:
        port = int(os.environ.get("PORT", 8080))
        server = http.server.HTTPServer(('', port), http.server.SimpleHTTPRequestHandler)
        server.serve_forever()
    except: pass

def load_db():
    if not os.path.exists(DB_FILE): return {"girl_1": {}, "girl_2": {}}
    try:
        with open(DB_FILE, 'r', encoding='utf-8') as f: return json.load(f)
    except: return {"girl_1": {}, "girl_2": {}}

def save_db(db):
    try:
        with open(DB_FILE, 'w', encoding='utf-8') as f: json.dump(db, f, indent=4, ensure_ascii=False)
    except: pass

# --- دالة التحميل مع حماية من الانهيار ---
def download_video_sync(url, chat_id):
    try:
        ydl_opts = {'format': 'best[ext=mp4]/best', 'outtmpl': f'/tmp/vid_{chat_id}.mp4', 'quiet': True}
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            return f'/tmp/vid_{chat_id}.mp4', info.get('title', 'Video')
    except Exception as e: return None, str(e)

@bot.message_handler(commands=['start'])
def start(message):
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(types.InlineKeyboardButton("📥 تحميل فيديو", callback_data="dl_video"),
               types.InlineKeyboardButton("🎧 قسم الصوتيات", callback_data="voice_menu"))
    bot.send_message(message.chat.id, "مرحباً بك يا سيف:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: True)
def handle_query(call):
    chat_id = call.message.chat.id
    if call.data == "dl_video":
        user_states[chat_id] = "waiting_for_url"
        bot.edit_message_text("أرسل رابط الفيديو الآن:", chat_id, call.message.message_id)
    elif call.data == "voice_menu":
        markup = types.InlineKeyboardMarkup(row_width=1)
        markup.add(types.InlineKeyboardButton("الفتاة 1", callback_data="g1"), types.InlineKeyboardButton("الفتاة 2", callback_data="g2"))
        bot.edit_message_text("اختر المجلد:", chat_id, call.message.message_id, reply_markup=markup)
    elif call.data in ["g1", "g2"]:
        user_states[chat_id] = f"active_{call.data}"
        bot.answer_callback_query(call.id, "أرسل الفويس الآن ليتم حفظه.")
    bot.answer_callback_query(call.id)

@bot.message_handler(content_types=['text', 'voice'])
def handle_msg(message):
    chat_id = message.chat.id
    # معالجة التحميل
    if user_states.get(chat_id) == "waiting_for_url":
        status = bot.reply_to(message, "⏳ جاري التحميل...")
        path, title = download_video_sync(message.text, chat_id)
        if path:
            bot.send_video(chat_id, open(path, 'rb'), caption=title)
            bot.delete_message(chat_id, status.message_id)
            os.remove(path)
        else: bot.edit_message_text(f"❌ خطأ: {title}", chat_id, status.message_id)
        user_states[chat_id] = None
    # معالجة حفظ الصوت
    elif message.voice and "active_" in str(user_states.get(chat_id)):
        db = load_db()
        target = "girl_1" if "g1" in user_states[chat_id] else "girl_2"
        idx = len(db[target]) + 1
        db[target][f"مقطع {idx}"] = message.voice.file_id
        save_db(db)
        bot.reply_to(message, "✅ تم الحفظ بنجاح.")

if __name__ == '__main__':
    threading.Thread(target=run_dummy_server, daemon=True).start()
    bot.polling(none_stop=True)
