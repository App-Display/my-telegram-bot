import os
import telebot
import yt_dlp
import threading
import http.server

# 1. إعداد التوكن
BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    print("❌ خطأ: لم يتم العثور على BOT_TOKEN في إعدادات المتغيرات (Variables) في Railway!")
    exit()

bot = telebot.TeleBot(BOT_TOKEN)

# 2. سيرفر للحفاظ على البوت نشطاً
def run_dummy_server():
    port = int(os.environ.get("PORT", 8080))
    httpd = http.server.HTTPServer(('', port), http.server.SimpleHTTPRequestHandler)
    print(f"🌐 السيرفر يعمل على المنفذ {port}")
    httpd.serve_forever()

# 3. دالة التحميل (بدون كوكيز لضمان العمل)
def download_video(url, chat_id):
    file_path = f'/tmp/video_{chat_id}.mp4'
    # خيارات تحميل قوية تحاكي المتصفح دون الحاجة لملفات كوكيز
    ydl_opts = {
        'format': 'best',
        'outtmpl': file_path,
        'quiet': False,
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36'
    }
    try:
        if os.path.exists(file_path): os.remove(file_path)
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            return file_path, info.get('title', 'Video')
    except Exception as e:
        print(f"❌ خطأ في التحميل: {e}")
        return None, str(e)

# 4. أوامر البوت
@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "🚀 البوت يعمل! أرسل رابط الفيديو للتحميل.")

@bot.message_handler(func=lambda m: True)
def handle_msg(message):
    url = message.text.strip()
    if not url.startswith("http"):
        bot.reply_to(message, "يرجى إرسال رابط صحيح يبدأ بـ http")
        return

    status = bot.reply_to(message, "⏳ جاري التحميل، يرجى الانتظار...")
    
    file_path, title = download_video(url, message.chat.id)
    
    if file_path and os.path.exists(file_path):
        with open(file_path, 'rb') as v:
            bot.send_video(message.chat.id, v, caption=title)
        bot.delete_message(message.chat.id, status.message_id)
        os.remove(file_path)
    else:
        bot.edit_message_text(f"❌ فشل التحميل. الرابط قد لا يكون مدعوماً أو خاصاً.\nالخطأ: {title}", message.chat.id, status.message_id)

# 5. تشغيل
if __name__ == '__main__':
    print("🤖 جاري بدء البوت...")
    threading.Thread(target=run_dummy_server, daemon=True).start()
    bot.infinity_polling()
