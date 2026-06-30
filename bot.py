import os
import telebot
from telebot import types
import yt_dlp
import threading
import http.server

# 1. إعداد التوكن
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = "000000000" # ضع الآيدي الخاص بك هنا

if not BOT_TOKEN:
    print("❌ خطأ حرج: لم يتم العثور على BOT_TOKEN!")
    exit(1)

bot = telebot.TeleBot(BOT_TOKEN)

# 2. إنشاء الأزرار (Inline - المدمجة مع الرسالة)
# هذه الأزرار ستظهر فوق/تحت الرسالة ولن تأخذ مكان لوحة المفاتيح أبداً
def get_inline_menu():
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton('رابط فيديو 🎥', callback_data='btn_video'),
        types.InlineKeyboardButton('رابط تعديل ✨', callback_data='btn_edit'),
        types.InlineKeyboardButton('تحميل فيديو 📥', callback_data='btn_download'),
        types.InlineKeyboardButton('أخبار وبث مباشر 🌐', callback_data='btn_news'),
        types.InlineKeyboardButton('تلقيم رابط 💣', callback_data='btn_spam'),
        types.InlineKeyboardButton('رابط صور 🖼️', callback_data='btn_photo')
    )
    return markup

# 3. حفظ المستخدمين
def save_user(chat_id):
    try:
        with open("users.txt", "a") as f:
            f.write(f"{chat_id}\n")
    except: pass

def get_unique_users():
    if not os.path.exists("users.txt"): return []
    with open("users.txt", "r") as f:
        return list(set(f.read().splitlines()))

# 4. سيرفر الحفاظ على البوت نشطاً
def run_dummy_server():
    port = int(os.environ.get("PORT", 8080))
    httpd = http.server.HTTPServer(('', port), http.server.SimpleHTTPRequestHandler)
    httpd.serve_forever()

threading.Thread(target=run_dummy_server, daemon=True).start()

# 5. دالة التحميل
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

# 6. الأوامر
@bot.message_handler(commands=['start'])
def send_welcome(message):
    save_user(message.chat.id)
    # هنا تم استدعاء الأزرار المدمجة (Inline)
    bot.send_message(message.chat.id, "👋 أهلاً بك، المطور سيف الدين يرحب بك!", reply_markup=get_inline_menu())

@bot.message_handler(commands=['announce'])
def announce(message):
    if str(message.chat.id) != ADMIN_ID: return
    users = get_unique_users()
    for uid in users:
        try: bot.send_message(uid, "✅ تم تحديث البوت! جربه الآن.")
        except: continue

@bot.message_handler(func=lambda message: message.text.startswith("http"))
def handle_msg(message):
    save_user(message.chat.id)
    status = bot.reply_to(message, "⏳ جاري التحميل...")
    path, title = download_video(message.text.strip(), message.chat.id)
    if path and os.path.exists(path):
        with open(path, 'rb') as v: bot.send_video(message.chat.id, v, caption=title)
        bot.delete_message(message.chat.id, status.message_id)
        os.remove(path)
    else:
        bot.edit_message_text(f"❌ فشل التحميل: {title}", message.chat.id, status.message_id)

if __name__ == '__main__':
    bot.infinity_polling()
