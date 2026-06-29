import os
import telebot
import yt_dlp
import threading
import http.server
import time
import logging

# تفعيل تسجيل الأخطاء
logging.basicConfig(level=logging.INFO)

BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    print("❌ خطأ: BOT_TOKEN غير موجود!")
    exit(1)

bot = telebot.TeleBot(BOT_TOKEN)

# 1. السيرفر الوهمي (لبقاء البوت نشطاً)
def run_dummy_server():
    port = int(os.environ.get("PORT", 8080))
    server = http.server.HTTPServer(('', port), http.server.SimpleHTTPRequestHandler)
    print(f"🌐 السيرفر الوهمي يعمل على المنفذ {port}")
    server.serve_forever()

threading.Thread(target=run_dummy_server, daemon=True).start()

# 2. دالة التحميل (مبسطة لتقليل استهلاك الذاكرة)
def download_video(url, chat_id):
    file_path = f'/tmp/vid_{chat_id}.mp4'
    ydl_opts = {
        'format': 'best[ext=mp4]/best',
        'outtmpl': file_path,
        'quiet': True,
        'no_warnings': True,
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36'
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            return file_path, info.get('title', 'Video')
    except Exception as e:
        return None, str(e)

# 3. الأوامر
@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message, "✅ البوت يعمل! أرسل رابط الفيديو للتحميل.")

@bot.message_handler(func=lambda m: True)
def handle_message(message):
    status_msg = bot.reply_to(message, "⏳ جاري التحميل...")
    path, title = download_video(message.text.strip(), message.chat.id)
    if path and os.path.exists(path):
        with open(path, 'rb') as v:
            bot.send_video(message.chat.id, v, caption=title)
        bot.delete_message(message.chat.id, status_msg.message_id)
        os.remove(path)
    else:
        bot.edit_message_text(f"❌ خطأ: {title}", message.chat.id, status_msg.message_id)

# 4. "حلقة الشفاء الذاتي" (هذا هو الجزء الأهم!)
print("🤖 البوت بدأ بالعمل...")
while True:
    try:
        bot.infinity_polling(none_stop=True)
    except Exception as e:
        print(f"⚠️ حدث خطأ، سيتم إعادة التشغيل في 5 ثوانٍ: {e}")
        time.sleep(5)
