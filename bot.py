import os
import json
import urllib3
import telebot
from telebot import types
import threading
import http.server
import yt_dlp

# إيقاف التحذيرات
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

BOT_TOKEN = os.getenv("BOT_TOKEN", "8128965245:AAGolmLae3ALVga_kcloXCK2zsFRODK4BXc")
bot = telebot.TeleBot(BOT_TOKEN)

user_states = {}

# --- دالة تحميل قوية ---
def download_video_sync(url, chat_id):
    try:
        # إعدادات لضمان عدم فشل التحميل
        ydl_opts = {
            'format': 'best[ext=mp4]/best',
            'outtmpl': f'/tmp/vid_{chat_id}.mp4',
            'quiet': True,
            'no_warnings': True,
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
            return f'/tmp/vid_{chat_id}.mp4'
    except Exception as e:
        return None

# --- معالجة الرسائل النصية (التحميل) ---
@bot.message_handler(content_types=['text'])
def handle_text(message):
    chat_id = message.chat.id
    
    # التحقق مما إذا كان المستخدم في حالة انتظار رابط
    if user_states.get(chat_id) == "waiting_for_url":
        status_msg = bot.reply_to(message, "⏳ جاري التحميل، يرجى الانتظار...")
        
        file_path = download_video_sync(message.text, chat_id)
        
        if file_path and os.path.exists(file_path):
            try:
                with open(file_path, 'rb') as video:
                    bot.send_video(chat_id, video, caption="✅ تم التحميل بنجاح!")
                bot.delete_message(chat_id, status_msg.message_id)
                os.remove(file_path)
            except Exception as e:
                bot.edit_message_text(f"❌ خطأ أثناء الإرسال: {e}", chat_id, status_msg.message_id)
        else:
            bot.edit_message_text("❌ فشل التحميل، تأكد من الرابط وحاول مجدداً.", chat_id, status_msg.message_id)
        
        user_states[chat_id] = None # إعادة الحالة
    
    # إذا لم يكن في حالة انتظار، تجاهل النص أو أضف أوامر أخرى
    elif message.text == "/start":
        pass 

# --- معالجة الأزرار ---
@bot.callback_query_handler(func=lambda call: True)
def handle_query(call):
    chat_id = call.message.chat.id
    if call.data == "dl_video":
        user_states[chat_id] = "waiting_for_url"
        bot.edit_message_text("📥 أرسل رابط الفيديو الآن (يوتيوب/تيك توك/إنستغرام):", chat_id, call.message.message_id)
    # ... (باقي كود الأزرار) ...
    bot.answer_callback_query(call.id)

# ابدأ البوت
if __name__ == '__main__':
    bot.polling(none_stop=True)
