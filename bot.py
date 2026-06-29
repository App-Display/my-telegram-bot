import os
import telebot
import yt_dlp
import threading
import http.server
import time

# 1. إعداد البوت
BOT_TOKEN = os.getenv("BOT_TOKEN")

if not BOT_TOKEN:
    print("❌ خطأ: BOT_TOKEN غير موجود في متغيرات البيئة!")
    exit(1)

bot = telebot.TeleBot(BOT_TOKEN)

# 2. السيرفر الوهمي (ضروري جداً لبقاء البوت نشطاً في Railway)
def run_dummy_server():
    port = int(os.environ.get("PORT", 8080))
    server = http.server.HTTPServer(('', port), http.server.SimpleHTTPRequestHandler)
    print(f"🌐 السيرفر الوهمي يعمل على البورت {port}")
    server.serve_forever()

# تشغيل السيرفر في الخلفية
threading.Thread(target=run_dummy_server, daemon=True).start()

# 3. دالة التحميل المحدثة
def download_video(url, chat_id):
    file_path = f'/tmp/video_{chat_id}.mp4'
    ydl_opts = {
        'format': 'best',
        'outtmpl': file_path,
        'quiet': False, # غيرنا لـ False لنرى الأخطاء في السجلات
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36'
    }
    try:
        if os.path.exists(file_path): os.remove(file_path)
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            return file_path, info.get('title', 'Video')
    except Exception as e:
        return None, str(e)

# 4. الأوامر
@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message, "✅ البوت يعمل! أرسل رابط الفيديو للتحميل.")

@bot.message_handler(func=lambda m: True)
def handle_message(message):
    url = message.text.strip()
    status_msg = bot.reply_to(message, "⏳ جاري المعالجة...")
    
    path, title = download_video(url, message.chat.id)
    
    if path and os.path.exists(path):
        with open(path, 'rb') as v:
            bot.send_video(message.chat.id, v, caption=title)
        bot.delete_message(message.chat.id, status_msg.message_id)
        os.remove(path)
    else:
        bot.edit_message_text(f"❌ خطأ في التحميل:\n{title}", message.chat.id, status_msg.message_id)

# 5. التشغيل الدائم
print("🤖 البوت يعمل الآن وبانتظار الأوامر...")
bot.infinity_polling(none_stop=True)
