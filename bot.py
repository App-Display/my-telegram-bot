import os
import json
import telebot
from telebot import types
import threading
import http.server
import yt_dlp

# إعداد التوكن
BOT_TOKEN = os.getenv("BOT_TOKEN", "8128965245:AAGolmLae3ALVga_kcloXCK2zsFRODK4BXc")
bot = telebot.TeleBot(BOT_TOKEN)

# المسارات
DB_FILE = "/tmp/voice_db.json"

# --- السيرفر الوهمي ---
def run_dummy_server():
    port = int(os.environ.get("PORT", 8080))
    httpd = http.server.HTTPServer(('', port), http.server.SimpleHTTPRequestHandler)
    httpd.serve_forever()

# --- وظائف البيانات ---
def load_db():
    if not os.path.exists(DB_FILE): return {"girl_1": {}, "girl_2": {}}
    with open(DB_FILE, 'r', encoding='utf-8') as f:
        try: return json.load(f)
        except: return {"girl_1": {}, "girl_2": {}}

# --- القوائم الرئيسية ---
def get_main_keyboard():
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton("📥 تحميل فيديو", callback_data="dl_video"),
        types.InlineKeyboardButton("🎧 قسم الصوتيات", callback_data="voice_menu")
    )
    return markup

@bot.callback_query_handler(func=lambda call: True)
def handle_query(call):
    chat_id = call.message.chat.id
    db = load_db()

    if call.data == "voice_menu":
        markup = types.InlineKeyboardMarkup(row_width=1)
        markup.add(
            types.InlineKeyboardButton("👩 الفتاة 1 (10 مقاطع)", callback_data="girl_1_menu"),
            types.InlineKeyboardButton("👩 الفتاة 2 (13 مقطع)", callback_data="girl_2_menu"),
            types.InlineKeyboardButton("🔙 عودة", callback_data="main_menu")
        )
        bot.edit_message_text("📂 اختر المجلد:", chat_id, call.message.message_id, reply_markup=markup)

    # --- الفتاة 1 (10 مقاطع) ---
    elif call.data == "girl_1_menu":
        markup = types.InlineKeyboardMarkup(row_width=2)
        for i in range(1, 11): # من 1 إلى 10
            name = f"مقطع {i}"
            markup.add(types.InlineKeyboardButton(name, callback_data=f"play_g1:{name}"))
        markup.add(types.InlineKeyboardButton("🔙 عودة", callback_data="voice_menu"))
        bot.edit_message_text("👩 الفتاة 1 - المقاطع:", chat_id, call.message.message_id, reply_markup=markup)

    # --- الفتاة 2 (13 مقطع) ---
    elif call.data == "girl_2_menu":
        markup = types.InlineKeyboardMarkup(row_width=2)
        for i in range(1, 14): # من 1 إلى 13
            name = f"مقطع {i}"
            markup.add(types.InlineKeyboardButton(name, callback_data=f"play_g2:{name}"))
        markup.add(types.InlineKeyboardButton("🔙 عودة", callback_data="voice_menu"))
        bot.edit_message_text("👩 الفتاة 2 - المقاطع:", chat_id, call.message.message_id, reply_markup=markup)

    elif call.data == "main_menu":
        bot.edit_message_text("🤖 القائمة الرئيسية:", chat_id, call.message.message_id, reply_markup=get_main_keyboard())

    bot.answer_callback_query(call.id)

@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(message.chat.id, "أهلاً بك يا سيف:", reply_markup=get_main_keyboard())

if __name__ == '__main__':
    threading.Thread(target=run_dummy_server, daemon=True).start()
    bot.polling(none_stop=True)
