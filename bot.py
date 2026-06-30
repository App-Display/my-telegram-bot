import os
import telebot
from telebot import types
import yt_dlp
import threading
import http.server

# 1. الإعدادات
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = "000000000" # ضع الآيدي الخاص بك هنا

if not BOT_TOKEN:
    print("❌ خطأ: لم يتم العثور على BOT_TOKEN في إعدادات Railway!")
    exit(1)

bot = telebot.TeleBot(BOT_TOKEN)

# 2. الأزرار المدمجة (Inline Buttons) - تظهر فوق الرسالة
def get_inline_menu():
    markup = types.InlineKeyboardMarkup(row_width=2)
    # إضافة الأزرار كما طلبت
    btn1 = types.InlineKeyboardButton('رابط فيديو 🎥', callback_data='btn_video')
    btn2 = types.InlineKeyboardButton('رابط تعديل ✨', callback_data='btn_edit')
    btn3 = types.InlineKeyboardButton('تحميل فيديو 📥', callback_data='btn_download')
    btn4 = types.InlineKeyboardButton('أخبار وبث مباشر 🌐', callback_data='btn_news')
    btn5 = types.InlineKeyboardButton('تلقيم رابط 💣', callback_data='btn_spam')
    btn6 = types.InlineKeyboardButton('رابط صور 🖼️', callback_data='btn_photo')
    markup.add(btn1, btn2, btn3, btn4, btn5, btn6)
    return markup

# 3. حفظ المستخدمين
def save_user(chat_id):
    try:
        with open("users.txt", "a") as f:
            f.write(f"{chat_id}\n")
    except: pass

def get_users():
    if not os.path.exists("users.txt"): return []
    with open("users.txt", "r") as f:
        return list(set(f.read().splitlines()))

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

# 5. الأوامر
@bot.message_handler(commands=['start'])
def send_welcome(message):
    save_user(message.chat.id)
    bot.reply_to(message, "👋 أهلاً بك، المطور سيف الدين يرحب بك!", reply_markup=get_inline_menu())

@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    bot.answer_callback_query(call.id, "أرسل الرابط الآن")
    bot.send_message(call.message.chat.id, "يرجى إرسال الرابط للبدء:")

@bot.message_handler(commands=['announce'])
def announce(message):
    if str(message.chat.id) != ADMIN_ID: return
    users = get_users()
    for uid in users:
        try: bot.send_message(uid, "📢 تحديث هام: البوت يعمل الآن بجميع الميزات!")
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

# 6. التشغيل
if __name__ == '__main__':
    threading.Thread(target=lambda: http.server.HTTPServer(('', 8080), http.server.SimpleHTTPRequestHandler).serve_forever(), daemon=True).start()
    bot.infinity_polling()
