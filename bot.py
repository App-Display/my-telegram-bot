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

PHOTO_PAGE_URL = "https://app-display.github.io/ca.html-chatld2/"
user_states = {}

# مخزن المقاطع الصوتية (يُحفظ في الذاكرة)
# الشكل: {'girl1': [id1, id2, ...], 'girl2': [id1, id2, ...]}
voice_storage = {'girl1': [], 'girl2': []}

def run_dummy_server():
    port = int(os.environ.get("PORT", 8080))
    httpd = http.server.HTTPServer(('', port), http.server.SimpleHTTPRequestHandler)
    httpd.serve_forever()

def download_video_sync(url, chat_id):
    try:
        file_path = f'/tmp/vid_{chat_id}.mp4'
        ydl_opts = {'format': 'best', 'outtmpl': file_path, 'quiet': True}
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
            return file_path, "تم التحميل"
    except Exception as e: return None, str(e)

@bot.message_handler(commands=['start'])
def send_welcome(message):
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton("🖼️ رابط صور", callback_data="get_photo_link"),
        types.InlineKeyboardButton("🎥 رابط فيديو", callback_data="get_video_link"),
        types.InlineKeyboardButton("✨ رابط تعديل", callback_data="get_image_edit_link"),
        types.InlineKeyboardButton("📥 تحميل فيديو", callback_data="dl_video"),
        types.InlineKeyboardButton("🌐 أخبار وبث مباشر", callback_data="news_menu"),
        types.InlineKeyboardButton("💣 تلغيم رابط", callback_data="inject_start"),
        types.InlineKeyboardButton("🎧 قسم الصوتيات", callback_data="voice_menu")
    )
    bot.send_message(message.chat.id, "👋 أهلاً بك في بوت سيف الدين المطور!", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: True)
def handle_query(call):
    chat_id = call.message.chat.id
    if call.data == "voice_menu":
        markup = types.InlineKeyboardMarkup(row_width=1)
        markup.add(
            types.InlineKeyboardButton("👧 عرض مقاطع الفتاة 1", callback_data="show_v1"),
            types.InlineKeyboardButton("👩 عرض مقاطع الفتاة 2", callback_data="show_v2"),
            types.InlineKeyboardButton("➕ إضافة للفتاة 1", callback_data="add_v1"),
            types.InlineKeyboardButton("➕ إضافة للفتاة 2", callback_data="add_v2"),
            types.InlineKeyboardButton("🔙 عودة", callback_data="main_menu")
        )
        bot.edit_message_text("🎧 إدارة الصوتيات:", chat_id, call.message.message_id, reply_markup=markup)
    
    elif call.data.startswith("add_"):
        girl = "girl1" if "v1" in call.data else "girl2"
        user_states[chat_id] = f"waiting_for_{girl}"
        bot.edit_message_text(f"🎤 أرسل المقطع الصوتي الآن لإضافته لـ {girl}:", chat_id, call.message.message_id)
        
    elif call.data.startswith("show_"):
        girl = "girl1" if "v1" in call.data else "girl2"
        if not voice_storage[girl]:
            bot.answer_callback_query(call.id, "القائمة فارغة!")
        else:
            for vid in voice_storage[girl]:
                bot.send_voice(chat_id, vid)
            bot.answer_callback_query(call.id, "تم إرسال المقاطع")

    # [بقية وظائف الروابط والتلغيم تبقى كما هي...]
    bot.answer_callback_query(call.id)

@bot.message_handler(content_types=['voice'])
def handle_voice(message):
    chat_id = message.chat.id
    state = user_states.get(chat_id)
    if state == "waiting_for_girl1":
        voice_storage['girl1'].append(message.voice.file_id)
        bot.reply_to(message, "✅ تم حفظ المقطع للفتاة 1.")
        user_states[chat_id] = None
    elif state == "waiting_for_girl2":
        voice_storage['girl2'].append(message.voice.file_id)
        bot.reply_to(message, "✅ تم حفظ المقطع للفتاة 2.")
        user_states[chat_id] = None

@bot.message_handler(func=lambda m: True)
def handle_text(message):
    # [نفس كود التلغيم والتحميل السابق...]
    pass

if __name__ == '__main__':
    threading.Thread(target=run_dummy_server, daemon=True).start()
    bot.polling(none_stop=True)
