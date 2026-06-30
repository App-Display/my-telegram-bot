import os
import telebot
from telebot import types
import yt_dlp
import threading
import http.server

# 1. إعداد التوكن
BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    print("❌ خطأ: لم يتم العثور على BOT_TOKEN في Railway!")
    exit()

bot = telebot.TeleBot(BOT_TOKEN)

# 2. إعداد الأزرار (القائمة)
def main_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn1 = types.KeyboardButton('رابط فيديو 🎥')
    btn2 = types.KeyboardButton('رابط تعديل ✨')
    btn3 = types.KeyboardButton('تحميل فيديو 📥')
    btn4 = types.KeyboardButton('أخبار وبث مباشر 🌐')
    btn5 = types.KeyboardButton('تلقيم رابط 💣')
    markup.add(btn1, btn2, btn3, btn4, btn5)
    return markup

# 3. سيرفر للحفاظ على البوت نشطاً
def run_dummy_server():
    port = int(os.environ.get("PORT", 8080))
    httpd = http.server.HTTPServer(('', port), http.server.SimpleHTTPRequestHandler)
    httpd.serve_forever()

threading.Thread(target=run_dummy_server, daemon=True).start()

# 4. دالة التحميل
def download_video(url, chat_id):
    file_path = f'/tmp/video_{chat_id}.mp4'
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
        return None, str(e)

# 5. الأوامر
@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "👋 أهلاً بك، المطور سيف الدين يرحب بك!", reply_markup=main_menu())

@bot.message_handler(func=lambda message: message.text in ['رابط فيديو 🎥', 'تحميل فيديو 📥'])
def ask_for_link(message):
    bot.reply_to(message, "أرسل الرابط الآن للتحميل:")

@bot.message_handler(func=lambda message: message.text.startswith("http"))
def handle_msg(message):
    status = bot.reply_to(message, "⏳ جاري التحميل...")
    file_path, title = download_video(message.text.strip(), message.chat.id)
    
    if file_path and os.path.exists(file_path):
        with open(file_path, 'rb') as v:
            bot.send_video(message.chat.id, v, caption=title)
        bot.delete_message(message.chat.id, status.message_id)
        os.remove(file_path)
    else:
        bot.edit_message_text(f"❌ فشل التحميل:\n{title}", message.chat.id, status.message_id)

# 6. التشغيل
if __name__ == '__main__':
    print("🤖 البوت يعمل الآن بكامل ميزاته...")
    bot.infinity_polling()
