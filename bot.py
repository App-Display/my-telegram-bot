import os
import telebot
from telebot import types
import yt_dlp
import threading
import http.server

# 1. الإعدادات
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = "8169635171" # تم تحديث الآيدي الخاص بك هنا

bot = telebot.TeleBot(BOT_TOKEN)

# 2. الأزرار المدمجة (Inline Buttons) فقط
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

# 3. الأوامر
@bot.message_handler(commands=['start'])
def send_welcome(message):
    # إزالة أي لوحة مفاتيح سابقة نهائياً
    remove_kb = types.ReplyKeyboardRemove()
    bot.send_message(message.chat.id, "👋 أهلاً بك، تم تحديث البوت.", reply_markup=remove_kb)
    # إرسال الأزرار المدمجة
    bot.send_message(message.chat.id, "اختر من القائمة:", reply_markup=get_inline_menu())

@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    bot.answer_callback_query(call.id, "أرسل الرابط للتحميل")
    bot.send_message(call.message.chat.id, "أرسل رابط الفيديو الآن:")

@bot.message_handler(func=lambda message: True)
def handle_msg(message):
    # إذا كان رابطاً
    if message.text.startswith("http"):
        bot.reply_to(message, "⏳ جاري المعالجة...")
    # إذا كان أمراً إدارياً (الإعلان)
    elif message.text == "/announce" and str(message.chat.id) == ADMIN_ID:
        bot.reply_to(message, "📢 تم تفعيل ميزة الإعلان.")
    else:
        bot.reply_to(message, "الرجاء إرسال رابط فيديو صحيح.")

# تشغيل السيرفر
if __name__ == '__main__':
    threading.Thread(target=lambda: http.server.HTTPServer(('', 8080), http.server.SimpleHTTPRequestHandler).serve_forever(), daemon=True).start()
    bot.infinity_polling()
