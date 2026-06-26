import os
import telebot
import yt_dlp
import google.generativeai as genai
import PIL.Image
import io
import threading
import http.server

# 1. إعدادات البوت
BOT_TOKEN = os.getenv("BOT_TOKEN", "8446745973:AAGRD2tFbSrzB2OFoByvYRHCY1Hp6nluHf0")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
bot = telebot.TeleBot(BOT_TOKEN)

# 2. إعدادات Gemini
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-1.5-flash")

# 3. سيرفر للحفاظ على البوت نشطاً في Railway
def run_dummy_server():
    try: http.server.HTTPServer(('', int(os.environ.get("PORT", 8080))), http.server.SimpleHTTPRequestHandler).serve_forever()
    except: pass
threading.Thread(target=run_dummy_server, daemon=True).start()

# 4. دالة التحميل
def download_video(url, chat_id):
    try:
        path = f'/tmp/vid_{chat_id}.mp4'
        ydl_opts = {'format': 'best', 'outtmpl': path, 'quiet': True}
        with yt_dlp.YoutubeDL(ydl_opts) as ydl: ydl.download([url])
        return path
    except: return None

# 5. القائمة الرئيسية
def get_kb():
    kb = telebot.types.InlineKeyboardMarkup()
    kb.add(telebot.types.InlineKeyboardButton("📥 تحميل فيديو", callback_data="dl"))
    kb.add(telebot.types.InlineKeyboardButton("🤖 محادثة Gemini", callback_data="ai"))
    return kb

@bot.message_handler(commands=['start'])
def start(m):
    bot.send_message(m.chat.id, "👋 أهلاً بك يا سيف الدين، أنا جاهز للعمل!", reply_markup=get_kb())

@bot.callback_query_handler(func=lambda c: True)
def query(c):
    if c.data == "dl":
        bot.edit_message_text("أرسل رابط الفيديو للتحميل:", c.message.chat.id, c.message.message_id)
        bot.register_next_step_handler(c.message, process_dl)
    elif c.data == "ai":
        bot.edit_message_text("🤖 أنت الآن في وضع Gemini. أرسل سؤالك:", c.message.chat.id, c.message.message_id)
        bot.register_next_step_handler(c.message, process_ai)

def process_dl(m):
    msg = bot.reply_to(m, "⏳ جارٍ التحميل...")
    path = download_video(m.text, m.chat.id)
    if path:
        bot.send_video(m.chat.id, open(path, 'rb'))
        os.remove(path)
        bot.delete_message(m.chat.id, msg.message_id)
    else: bot.reply_to(m, "❌ فشل التحميل.")

def process_ai(m):
    try:
        bot.reply_to(m, "⏳ جاري التفكير...")
        response = model.generate_content(m.text)
        bot.send_message(m.chat.id, response.text)
    except Exception as e: bot.reply_to(m, f"❌ خطأ: {e}")

bot.polling(none_stop=True)
