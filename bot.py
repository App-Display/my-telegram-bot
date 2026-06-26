import os
import json
import urllib3
import telebot
from telebot import types
import threading
import http.server
import yt_dlp
import google.generativeai as genai
import PIL.Image
import io

# إعدادات
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
BOT_TOKEN = os.getenv("BOT_TOKEN", "8446745973:AAGRD2tFbSrzB2OFoByvYRHCY1Hp6nluHf0")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
bot = telebot.TeleBot(BOT_TOKEN)
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-1.5-flash")

user_states = {}
user_histories = {}

def run_dummy_server():
    try: http.server.HTTPServer(('', int(os.environ.get("PORT", 8080))), http.server.SimpleHTTPRequestHandler).serve_forever()
    except: pass
threading.Thread(target=run_dummy_server, daemon=True).start()

# --- وظائف الخدمات ---
def download_video_sync(url, chat_id):
    try:
        path = f'/tmp/vid_{chat_id}.mp4'
        ydl_opts = {'format': 'best', 'outtmpl': path}
        with yt_dlp.YoutubeDL(ydl_opts) as ydl: ydl.download([url])
        return path
    except: return None

# --- لوحة التحكم ---
def get_main_keyboard():
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton("📥 تحميل فيديو", callback_data="dl_video"),
        types.InlineKeyboardButton("🌐 أخبار وبث مباشر", callback_data="news_menu"),
        types.InlineKeyboardButton("🤖 Gemini AI", callback_data="gemini_mode"),
        types.InlineKeyboardButton("🎧 قسم الصوتيات", callback_data="voice_menu")
    )
    return markup

@bot.message_handler(commands=['start'])
def start(m):
    bot.send_message(m.chat.id, "👋 أهلاً بك، المطور سيف الدين يرحب بك!", reply_markup=get_main_keyboard())

# --- معالجة الأزرار ---
@bot.callback_query_handler(func=lambda c: True)
def query(c):
    cid = c.message.chat.id
    if c.data == "gemini_mode":
        user_states[cid] = "gemini"
        bot.edit_message_text("🤖 أنت الآن في وضع Gemini. أرسل سؤالك أو صورتك:", cid, c.message.message_id)
    elif c.data == "dl_video":
        user_states[cid] = "waiting_for_url"
        bot.edit_message_text("📥 أرسل رابط الفيديو:", cid, c.message.message_id)
    elif c.data == "main_menu":
        bot.edit_message_text("🤖 القائمة الرئيسية:", cid, c.message.message_id, reply_markup=get_main_keyboard())
    bot.answer_callback_query(c.id)

# --- معالجة الرسائل (النص + الصور + التحميل) ---
@bot.message_handler(content_types=['text', 'photo'])
def handle_msg(m):
    cid = m.chat.id
    # منطق Gemini
    if user_states.get(cid) == "gemini":
        bot.reply_to(m, "⏳ جاري التفكير...")
        try:
            if m.content_type == 'text':
                response = model.generate_content(m.text)
                bot.send_message(cid, response.text)
            elif m.content_type == 'photo':
                file_info = bot.get_file(m.photo[-1].file_id)
                downloaded_file = bot.download_file(file_info.file_path)
                image = PIL.Image.open(io.BytesIO(downloaded_file))
                response = model.generate_content(["اشرح هذه الصورة بالتفصيل", image])
                bot.send_message(cid, response.text)
        except Exception as e: bot.send_message(cid, f"❌ خطأ: {e}")
    
    # منطق التحميل
    elif user_states.get(cid) == "waiting_for_url":
        bot.reply_to(m, "⏳ جاري التحميل...")
        path = download_video_sync(m.text, cid)
        if path: bot.send_video(cid, open(path, 'rb')); os.remove(path)
        else: bot.reply_to(m, "❌ فشل التحميل")
        user_states[cid] = None

bot.polling(none_stop=True)
