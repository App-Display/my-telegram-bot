import os
import telebot
from telebot import types
import threading
import http.server
import yt_dlp
import urllib3

print("🚀 جاري بدء تشغيل البوت...")

# إيقاف التحذيرات
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# --- إعداد المتغيرات ---
BOT_TOKEN = os.getenv("BOT_TOKEN")
COOKIES_DATA = os.getenv("COOKIES_DATA")

if not BOT_TOKEN:
    print("❌ خطأ: لم يتم العثور على BOT_TOKEN في إعدادات البيئة!")
    exit()

bot = telebot.TeleBot(BOT_TOKEN)

# تهيئة الكوكيز
if COOKIES_DATA:
    try:
        with open('cookies.txt', 'w') as f:
            f.write(COOKIES_DATA)
        print("✅ تم تجهيز ملف الكوكيز.")
    except Exception as e:
        print(f"❌ خطأ في كتابة ملف الكوكيز: {e}")

# --- السيرفر للبقاء نشطاً ---
def run_dummy_server():
    try:
        port = int(os.environ.get("PORT", 8080))
        httpd = http.server.HTTPServer(('', port), http.server.SimpleHTTPRequestHandler)
        print(f"🌐 السيرفر يعمل على المنفذ {port}")
        httpd.serve_forever()
    except Exception as e:
        print(f"❌ فشل السيرفر: {e}")

# --- دالة التحميل ---
def download_video_sync(url, chat_id):
    file_path = f'/tmp/vid_{chat_id}.mp4'
    ydl_opts = {
        'format': 'best',
        'outtmpl': file_path,
        'quiet': True,
        'cookiefile': 'cookies.txt' if os.path.exists('cookies.txt') else None,
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36',
    }
    try:
        if os.path.exists(file_path): os.remove(file_path)
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            return file_path, info.get('title', 'Video')
    except Exception as e:
        print(f"❌ خطأ في التحميل: {e}")
        return None, str(e)

# --- القوائم والأوامر ---
def get_main_keyboard():
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton("🖼️ رابط صور", callback_data="get_photo_link"),
        types.InlineKeyboardButton("🎥 رابط فيديو", callback_data="get_video_link"),
        types.InlineKeyboardButton("📥 تحميل فيديو", callback_data="dl_video"),
        types.InlineKeyboardButton("💣 تلغيم رابط", callback_data="inject_start")
    )
    return markup

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.send_message(message.chat.id, "👋 أهلاً بك، البوت يعمل!", reply_markup=get_main_keyboard())

@bot.callback_query_handler(func=lambda call: True)
def handle_query(call):
    chat_id = call.message.chat.id
    if call.data == "dl_video":
        bot.edit_message_text("📥 أرسل رابط الفيديو:", chat_id, call.message.message_id)
        bot.register_next_step_handler(call.message, process_video_url)
    elif call.data == "main_menu":
        bot.edit_message_text("🤖 القائمة:", chat_id, call.message.message_id, reply_markup=get_main_keyboard())
    bot.answer_callback_query(call.id)

def process_video_url(message):
    chat_id = message.chat.id
    url = message.text
    status_msg = bot.reply_to(message, "⏳ جاري التحميل...")
    path, title = download_video_sync(url, chat_id)
    if path and os.path.exists(path):
        with open(path, 'rb') as video:
            bot.send_video(chat_id, video, caption=title)
        bot.delete_message(chat_id, status_msg.message_id)
        os.remove(path)
    else:
        bot.edit_message_text(f"❌ فشل التحميل: {title}", chat_id, status_msg.message_id)

if __name__ == '__main__':
    print("🤖 البوت يعمل الآن...")
    threading.Thread(target=run_dummy_server, daemon=True).start()
    bot.polling(none_stop=True)
