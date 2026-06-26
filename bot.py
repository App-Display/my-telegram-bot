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

# إيقاف التحذيرات
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# الإعدادات
BOT_TOKEN = os.getenv("BOT_TOKEN", "8446745973:AAGRD2tFbSrzB2OFoByvYRHCY1Hp6nluHf0")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "") # ضع مفتاحك في Railway Variables
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-1.5-flash")

bot = telebot.TeleBot(BOT_TOKEN)
DB_FILE = "/tmp/voice_db.json"
user_states = {}

def run_dummy_server():
    try: http.server.HTTPServer(('', int(os.environ.get("PORT", 8080))), http.server.SimpleHTTPRequestHandler).serve_forever()
    except: pass
threading.Thread(target=run_dummy_server, daemon=True).start()

def load_db():
    if not os.path.exists(DB_FILE): return {"girl_1": {}, "girl_2": {}}
    with open(DB_FILE, 'r', encoding='utf-8') as f:
        try: return json.load(f)
        except: return {"girl_1": {}, "girl_2": {}}

# --- الميزات ---
def get_main_keyboard():
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton("🖼️ رابط صور", callback_data="get_photo_link"),
        types.InlineKeyboardButton("🎥 رابط فيديو", callback_data="get_video_link"),
        types.InlineKeyboardButton("✨ رابط تعديل", callback_data="get_image_edit_link"),
        types.InlineKeyboardButton("📥 تحميل فيديو", callback_data="dl_video"),
        types.InlineKeyboardButton("🌐 أخبار وبث مباشر", callback_data="news_menu"),
        types.InlineKeyboardButton("🤖 محادثة Gemini", callback_data="ai_mode"),
        types.InlineKeyboardButton("🔒 حقن رابط", callback_data="inject_start"),
        types.InlineKeyboardButton("🎧 قسم الصوتيات", callback_data="voice_menu")
    )
    return markup

@bot.message_handler(commands=['start'])
def send_welcome(m):
    bot.send_message(m.chat.id, "👋 أهلاً بك، المطور سيف الدين يرحب بك!", reply_markup=get_main_keyboard())

@bot.callback_query_handler(func=lambda c: True)
def handle_query(c):
    cid = c.message.chat.id
    if c.data == "dl_video":
        user_states[cid] = "waiting_for_url"
        bot.edit_message_text("📥 أرسل رابط الفيديو الآن:", cid, c.message.message_id)
    elif c.data == "ai_mode":
        user_states[cid] = "ai"
        bot.edit_message_text("🤖 أنت الآن في وضع Gemini. أرسل سؤالك أو صورتك:", cid, c.message.message_id)
    elif c.data == "voice_menu":
        bot.edit_message_text("🎧 قسم الصوتيات (مفعل)", cid, c.message.message_id, reply_markup=get_main_keyboard())
    elif c.data == "news_menu":
        bot.edit_message_text("🌐 قسم الأخبار والبث (مفعل)", cid, c.message.message_id, reply_markup=get_main_keyboard())
    elif c.data == "main_menu":
        bot.edit_message_text("🤖 القائمة الرئيسية:", cid, c.message.message_id, reply_markup=get_main_keyboard())
    bot.answer_callback_query(c.id)

@bot.message_handler(content_types=['text', 'photo'])
def handle_msg(m):
    cid = m.chat.id
    if user_states.get(cid) == "ai":
        try:
            if m.content_type == 'text':
                response = model.generate_content(m.text)
                bot.reply_to(m, response.text)
            elif m.content_type == 'photo':
                file_info = bot.get_file(m.photo[-1].file_id)
                img = PIL.Image.open(io.BytesIO(bot.download_file(file_info.file_path)))
                bot.reply_to(m, model.generate_content(["حلل هذه الصورة:", img]).text)
        except Exception as e: bot.reply_to(m, f"❌ خطأ في Gemini: {e}")
    elif user_states.get(cid) == "waiting_for_url":
        bot.reply_to(m, "⏳ جاري التحميل...")
        # (أضف دالة download_video_sync هنا)
        user_states[cid] = None

bot.polling(none_stop=True)
