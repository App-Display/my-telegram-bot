import os
import json
import urllib3
import telebot
from telebot import types
import threading
import http.server
import yt_dlp
import anthropic
import base64

# إيقاف التحذيرات
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

BOT_TOKEN = os.getenv("BOT_TOKEN", "8446745973:AAGRD2tFbSrzB2OFoByvYRHCY1Hp6nluHf0")
CLAUDE_API_KEY = os.getenv("CLAUDE_API_KEY", "ضع_مفتاح_Claude_هنا")
bot = telebot.TeleBot(BOT_TOKEN)
client = anthropic.Anthropic(api_key=CLAUDE_API_KEY)

DB_FILE = "/tmp/voice_db.json"
user_states = {}
user_histories = {}

def run_dummy_server():
    try: http.server.HTTPServer(('', int(os.environ.get("PORT", 8080))), http.server.SimpleHTTPRequestHandler).serve_forever()
    except: pass
threading.Thread(target=run_dummy_server, daemon=True).start()

# --- دالة Claude ---
def ask_claude(user_id, text):
    if user_id not in user_histories: user_histories[user_id] = []
    user_histories[user_id].append({"role": "user", "content": text})
    response = client.messages.create(model="claude-3-5-sonnet-20240620", max_tokens=1000, messages=user_histories[user_id])
    reply = response.content[0].text
    user_histories[user_id].append({"role": "assistant", "content": reply})
    return reply

# --- دالة التحميل ---
def download_video_sync(url, chat_id):
    try:
        path = f'/tmp/vid_{chat_id}.mp4'
        ydl_opts = {'format': 'best', 'outtmpl': path}
        with yt_dlp.YoutubeDL(ydl_opts) as ydl: ydl.download([url])
        return path
    except: return None

# --- الأزرار ---
def get_main_keyboard():
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton("📥 تحميل فيديو", callback_data="dl_video"),
        types.InlineKeyboardButton("🌐 أخبار وبث مباشر", callback_data="news_menu"),
        types.InlineKeyboardButton("🤖 Claude AI", callback_data="claude_mode"),
        types.InlineKeyboardButton("🎧 قسم الصوتيات", callback_data="voice_menu")
    )
    return markup

@bot.message_handler(commands=['start'])
def start(m):
    bot.send_message(m.chat.id, "👋 أهلاً بك، المطور سيف الدين يرحب بك!", reply_markup=get_main_keyboard())

@bot.callback_query_handler(func=lambda c: True)
def query(c):
    cid = c.message.chat.id
    if c.data == "claude_mode":
        user_states[cid] = "claude"
        bot.edit_message_text("🤖 أنت الآن في وضع Claude. أرسل سؤالك:", cid, c.message.message_id)
    elif c.data == "news_menu":
        markup = types.InlineKeyboardMarkup(row_width=1)
        markup.add(types.InlineKeyboardButton("🔴 الجزيرة مباشر", web_app=types.WebAppInfo(url="https://www.aljazeera.net/live")),
                   types.InlineKeyboardButton("🔙 عودة", callback_data="main_menu"))
        bot.edit_message_text("🌐 اختر القناة:", cid, c.message.message_id, reply_markup=markup)
    elif c.data == "main_menu":
        bot.edit_message_text("🤖 القائمة الرئيسية:", cid, c.message.message_id, reply_markup=get_main_keyboard())
    elif c.data == "dl_video":
        user_states[cid] = "waiting_for_url"
        bot.edit_message_text("📥 أرسل رابط الفيديو:", cid, c.message.message_id)
    bot.answer_callback_query(c.id)

@bot.message_handler(content_types=['text'])
def handle_text(m):
    cid = m.chat.id
    if user_states.get(cid) == "claude":
        bot.reply_to(m, "⏳ جاري التفكير...")
        reply = ask_claude(cid, m.text)
        bot.send_message(cid, reply)
    elif user_states.get(cid) == "waiting_for_url":
        path = download_video_sync(m.text, cid)
        if path: bot.send_video(cid, open(path, 'rb')); os.remove(path)
        else: bot.reply_to(m, "❌ خطأ في التحميل")
        user_states[cid] = None

bot.polling(none_stop=True)
