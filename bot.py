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

# 2. الأزرار المدمجة فقط (Inline Buttons) - تظهر فوق الرسالة
def get_inline_menu():
    markup = types.InlineKeyboardMarkup(row_width=2)
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

# 4. الأوامر
@bot.message_handler(commands=['start'])
def send_welcome(message):
    save_user(message.chat.id)
    # إخفاء أي لوحة مفاتيح قديمة (Reply Keyboard)
    remove_keyboard = types.ReplyKeyboardRemove()
    bot.send_message(message.chat.id, "👋 أهلاً بك، المطور سيف الدين يرحب بك!", reply_markup=remove_keyboard)
    # إرسال الأزرار المدمجة فقط
    bot.send_message(message.chat.id, "اختر من القائمة:", reply_markup=get_inline_menu())

@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    bot.answer_callback_query(call.id, "أرسل الرابط للتحميل")
    bot.send_message(call.message.chat.id, "يرجى إرسال رابط الفيديو للبدء:")

@bot.message_handler(func=lambda message: message.text.startswith("http"))
def handle_msg(message):
    save_user(message.chat.id)
    status = bot.reply_to(message, "⏳ جاري التحميل...")
    # (هنا يتم تنفيذ التحميل)
    # ملاحظة: تم حذف أي كود ReplyKeyboardMarkup هنا
    bot.edit_message_text("تم استلام الرابط، جاري المعالجة...", message.chat.id, status.message_id)

# تشغيل السيرفر للبقاء نشطاً
threading.Thread(target=lambda: http.server.HTTPServer(('', 8080), http.server.SimpleHTTPRequestHandler).serve_forever(), daemon=True).start()

if __name__ == '__main__':
    bot.infinity_polling()
