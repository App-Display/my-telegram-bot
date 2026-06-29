import os
import telebot
import yt_dlp
import threading
import http.server

# جلب التوكن من المتغيرات
BOT_TOKEN = os.getenv("BOT_TOKEN")

if not BOT_TOKEN:
    print("❌ خطأ: لم يتم العثور على BOT_TOKEN في الإعدادات")
    exit(1)

bot = telebot.TeleBot(BOT_TOKEN)

# السيرفر الوهمي (لإبقاء الخدمة نشطة)
def run_dummy_server():
    port = int(os.environ.get("PORT", 8080))
    httpd = http.server.HTTPServer(('', port), http.server.SimpleHTTPRequestHandler)
    httpd.serve_forever()

threading.Thread(target=run_dummy_server, daemon=True).start()

# دالة التحميل
def download_video(url, chat_id):
    file_path = f'/tmp/vid_{chat_id}.mp4'
    ydl_opts = {
        'format': 'best',
        'outtmpl': file_path,
        'quiet': True,
        'no_warnings': True,
    }
    try:
        if os.path.exists(file_path): os.remove(file_path)
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            return file_path, info.get('title', 'Video')
    except Exception as e:
        return None, str(e)

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "✅ البوت يعمل وجاهز للتحميل!")

@bot.message_handler(func=lambda m: True)
def handle_msg(message):
    status_msg = bot.reply_to(message, "⏳ جاري المعالجة...")
    path, title = download_video(message.text.strip(), message.chat.id)
    
    if path and os.path.exists(path):
        with open(path, 'rb') as v:
            bot.send_video(message.chat.id, v, caption=title)
        bot.delete_message(message.chat.id, status_msg.message_id)
        os.remove(path)
    else:
        bot.edit_message_text(f"❌ خطأ: الرابط غير مدعوم أو خاص.\n{title}", message.chat.id, status_msg.message_id)

print("🤖 البوت يعمل الآن...")
bot.infinity_polling()
