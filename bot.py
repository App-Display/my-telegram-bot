import os
import json
import telebot
from telebot import types
import feedparser
import re
import threading
import http.server
import yt_dlp
from PIL import Image, PngImagePlugin

BOT_TOKEN = os.getenv("BOT_TOKEN", "8446745973:AAGRD2tFbSrzB2OFoByvYRHCY1Hp6nluHf0")
bot = telebot.TeleBot(BOT_TOKEN)
DB_FILE = "/tmp/voice_db.json"

NEWS_SOURCES = {
    "aljazeera": {"name": "🌍 الجزيرة", "url": "https://www.aljazeera.net/xmlfeeds/news.xml"},
    "bbc_arabic": {"name": "📺 BBC عربي", "url": "https://feeds.bbci.co.uk/arabic/rss.xml"}
}

# --- خدمات النظام ---
def run_dummy_server():
    try: http.server.HTTPServer(('', int(os.environ.get("PORT", 8080))), http.server.SimpleHTTPRequestHandler).serve_forever()
    except: pass
threading.Thread(target=run_dummy_server, daemon=True).start()

# --- وظائف البوت ---
def get_news(url):
    feed = feedparser.parse(url)
    return [{"title": e.get("title"), "link": e.get("link")} for e in feed.entries[:5]]

def save_voice(cid, target, fid):
    db = json.load(open(DB_FILE, 'r')) if os.path.exists(DB_FILE) else {"girl_1": {}, "girl_2": {}}
    idx = len(db[target]) + 1
    db[target][f"مقطع {idx}"] = fid
    json.dump(db, open(DB_FILE, 'w'), ensure_ascii=False)

# --- البداية ---
@bot.message_handler(commands=['start'])
def start(m):
    kb = types.InlineKeyboardMarkup(row_width=2)
    kb.add(
        types.InlineKeyboardButton("📥 تحميل", callback_data="dl_vid"),
        types.InlineKeyboardButton("🎧 صوتيات", callback_data="v_menu"),
        types.InlineKeyboardButton("🌍 أخبار", callback_data="news_menu"),
        types.InlineKeyboardButton("🔒 حقن رابط", callback_data="inject")
    )
    bot.send_message(m.chat.id, "👋 أهلاً بك، المطور سيف الدين يرحب بك!", reply_markup=kb)

# --- معالجة الأزرار ---
@bot.callback_query_handler(func=lambda c: True)
def query(c):
    cid = c.message.chat.id
    if c.data == "news_menu":
        m = types.InlineKeyboardMarkup()
        for k, v in NEWS_SOURCES.items(): m.add(types.InlineKeyboardButton(v['name'], callback_data=f"src:{k}"))
        bot.edit_message_text("اختر المصدر:", cid, c.message.message_id, reply_markup=m)
    elif c.data.startswith("src:"):
        news = get_news(NEWS_SOURCES[c.data.split(":")[1]]["url"])
        msg = "\n".join([f"• {n['title']}\n{n['link']}\n" for n in news])
        bot.send_message(cid, msg or "لا توجد أخبار حالياً")
    elif c.data == "dl_vid":
        bot.send_message(cid, "أرسل الرابط الآن:")
        bot.register_next_step_handler(c.message, dl_p)
    # (باقي الميزات كالسابق)
    bot.answer_callback_query(c.id)

def dl_p(m):
    try:
        s = bot.reply_to(m, "⏳ جار التحميل..."); ydl_opts = {'outtmpl': '/tmp/vid.mp4'}
        with yt_dlp.YoutubeDL(ydl_opts) as ydl: ydl.download([m.text])
        bot.send_video(m.chat.id, open('/tmp/vid.mp4', 'rb')); os.remove('/tmp/vid.mp4')
    except: bot.reply_to(m, "❌ خطأ")

@bot.message_handler(content_types=['voice'])
def handle_voice(m):
    # كود حفظ الفويس
    pass

bot.polling(none_stop=True)
