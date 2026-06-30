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

# 2. إنشاء الأزرار (Inline)
def get_inline_menu():
    markup = types.InlineKeyboardMarkup(row_width=2)
    btn1 = types.InlineKeyboardButton('رابط فيديو 🎥', callback_data='video_link')
    btn2 = types.InlineKeyboardButton('رابط تعديل ✨', callback_data='edit_link')
    btn3 = types.InlineKeyboardButton('تحميل فيديو 📥', callback_data='download')
    btn4 = types.InlineKeyboardButton('أخبار وبث مباشر 🌐', callback_data='news')
    btn5 = types.InlineKeyboardButton('تلقيم رابط 💣', callback_data='link_spam')
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
    ydl_opts = {'format': 'best', 'outtmpl': file_path, 'quiet': True}
    try:
        if os.path.exists(file_path): os.remove(file_path)
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            return file_path, info.get('title', 'Video')
    except Exception as e:
        return None, str(e)

# 5. الأوامر والمعالجات
@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.send_message(message.chat.id, "👋 أهلاً بك، المطور سيف الدين يرحب بك!", reply_markup=get_inline_menu())

@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    if call.data in ['video_link', 'download']:
        bot.answer_callback_query(call.id, "أرسل الرابط الآن")
        bot.send_message(call.message.chat.id, "أرسل رابط الفيديو للتحميل:")

@bot.message_handler(func=lambda message: message.text.startswith("http"))
def handle_msg(message):
    status = bot.reply_to(message, "⏳ جاري التحميل...")
    path, title = download_video(message.text.strip(), message.chat.id)
    if path and os.path.exists(path):
        with open(path, 'rb') as v:
            bot.send_video(message.chat.id, v, caption=title)
        bot.delete_message(message.chat.id, status.message_id)
        os.remove(path)
    else:
        bot.edit_message_text(f"❌ خطأ: {title}", message.chat.id, status.message_id)

if __name__ == '__main__':
    bot.infinity_polling()
