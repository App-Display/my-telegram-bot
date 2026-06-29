import os
import telebot
import yt_dlp
import threading
import http.server
import time

# إعداد التوكن مع تنظيف أي مسافات زائدة
BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()

if not BOT_TOKEN:
    print("❌ خطأ: BOT_TOKEN فارغ في المتغيرات!")
    exit(1)

try:
    bot = telebot.TeleBot(BOT_TOKEN)
except Exception as e:
    print(f"❌ خطأ في تهيئة البوت: {e}")
    exit(1)

# سيرفر للحفاظ على البوت نشطاً
def run_dummy_server():
    port = int(os.environ.get("PORT", 8080))
    server = http.server.HTTPServer(('', port), http.server.SimpleHTTPRequestHandler)
    server.serve_forever()

threading.Thread(target=run_dummy_server, daemon=True).start()

# دالة التحميل
def download_video(url, chat_id):
    file_path = f'/tmp/vid_{chat_id}.mp4'
    ydl_opts = {
        'format': 'best',
        'outtmpl': file_path,
        'quiet': True,
        'no_warnings': True,
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36'
    }
    try:
        if os.path.exists(file_path): os.remove(file_path)
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            return file_path, info.get('title', 'Video')
    except Exception as e:
        return None, str(e)

@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message, "✅ البوت يعمل! أرسل رابط الفيديو.")

@bot.message_handler(func=lambda m: True)
def handle_msg(message):
    status_msg = bot.reply_to(message, "⏳ جاري التحميل...")
    path, title = download_video(message.text.strip(), message.chat.id)
    if path and os.path.exists(path):
        with open(path, 'rb') as v:
            bot.send_video(message.chat.id, v, caption=title)
        bot.delete_message(message.chat.id, status_msg.message_id)
        os.remove(path)
    else:
        bot.edit_message_text(f"❌ خطأ: {title}", message.chat.id, status_msg.message_id)

print("🤖 البوت يعمل الآن...")
bot.infinity_polling()
