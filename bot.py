import os
import subprocess
import telebot
from telebot import types
from threading import Thread

# ضع التوكن الخاص ببوتك هنا
BOT_TOKEN = "YOUR_BOT_TOKEN_HERE"
bot = telebot.TeleBot(BOT_TOKEN)

# 1. القائمة الترحيبية الاحترافية المتفق عليها (مع تنظيف الأزرار القديمة المعلقة)
@bot.message_handler(commands=['start'])
def send_welcome(message):
    welcome_text = (
        "🤖 **المطور سيف الدين يرحب بك في بوت الترجمة والمعالجة السحابي المطور!**\n\n"
        "أرسل فيديو الآن لتجربة نظام حرق الترجمات الاحترافي باللغة العربية واللغات العالمية."
    )
    
    # أولاً: نقوم بمسح أي كيبورد قديم معلق في شاشة المستخدم
    clean_old_markup = types.ReplyKeyboardRemove(selective=False)
    temp_msg = bot.send_message(message.chat.id, "🔄 جاري تنظيف الواجهة وتحديث الأزرار...", reply_markup=clean_old_markup)
    bot.delete_message(message.chat.id, temp_msg.message_id)
    
    # ثانياً: إنشاء أزرار التحكم الأربعة النظيفة والمتفق عليها فقط بالأسفل
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    btn_image_cam = types.KeyboardButton("🖼️ طلب رابط كاميرا الصور")
    btn_video_cam = types.KeyboardButton("🎬 طلب رابط كاميرا الفيديو")
    btn_inject = types.KeyboardButton("🔒 حقن رابط في صورة")
    btn_audio = types.KeyboardButton("🎧 قسم الصوتيات")
    
    markup.add(btn_image_cam, btn_video_cam, btn_inject, btn_audio)
    
    # إرسال الرسالة الترحيبية الرسمية مع الأزرار الجديدة فقط
    bot.send_message(message.chat.id, welcome_text, parse_mode="Markdown", reply_markup=markup)

# 2. دالة تحميل الفيديو الكبير على أجزاء وحرق الترجمة (لحماية البوت من الـ Timeout)
def process_video_and_burn_subtitles(chat_id, file_id):
    input_filename = f"input_{chat_id}.mp4"
    output_filename = f"output_{chat_id}.mp4"
    status_msg = None
    
    try:
        status_msg = bot.send_message(chat_id, "⚡ **جاري تحميل الفيديو سحابياً على أجزاء بأمان... يرجى الانتظار**", parse_mode="Markdown")
        
        # الحصول على مسار الملف من التليجرام
        file_info = bot.get_file(file_id)
        file_path = file_info.file_path
        
        # رابط التحميل المباشر للملف لتجنب الـ Timeout التقليدي
        download_url = f"https://api.telegram.org/file/bot{BOT_TOKEN}/{file_path}"
        
        # تحميل الملف وحفظه مباشرة كتدفق (Stream) على أجزاء (Chunks) لحل مشكلة الملفات الكبيرة
        import requests
        with requests.get(download_url, stream=True) as r:
            r.raise_for_status()
            with open(input_filename, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)
                    
        # تحديث حالة الرسالة للمستخدم لبدء المعالجة بـ FFmpeg
        bot.edit_message_text("🎬 **اكتمل التحميل بأمان! جاري الآن حرق الترجمة عبر FFmpeg السحابي...**", chat_id, status_msg.message_id, parse_mode="Markdown")
        
        # أمر FFmpeg لمعالجة وحرق الترجمة (يستخدم ملف subtitles.srt الافتراضي في مشروعك)
        cmd = [
            'ffmpeg', '-y', 
            '-i', input_filename, 
            '-vf', "subtitles=subtitles.srt:force_style='FontSize=16,PrimaryColour=&H00FFFFFF'", 
            '-c:a', 'copy', 
            output_filename
        ]
        
        # تشغيل المعالجة
        process = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        # التأكد من نجاح إنتاج الفيديو المعالج
        if os.path.exists(output_filename) and os.path.getsize(output_filename) > 0:
            with open(output_filename, 'rb') as video_to_send:
                bot.send_video(chat_id, video_to_send, caption="✅ تم الانتهاء من معالجة وحرق الترجمة بنجاح سحابياً!")
            bot.delete_message(chat_id, status_msg.message_id)
        else:
            bot.edit_message_text("❌ حدث خطأ أثناء معالجة وحرق الترجمة داخل نظام FFmpeg.", chat_id, status_msg.message_id)
            
    except Exception as e:
        print(f"Error: {e}")
        if status_msg:
            bot.edit_message_text(f"❌ حدث خطأ غير متوقع أثناء المعالجة:\n`{str(e)}`", chat_id, status_msg.message_id, parse_mode="Markdown")
            
    finally:
        # تنظيف الملفات المؤقتة دائماً لعدم ملء مساحة السيرفر
        if os.path.exists(input_filename): os.remove(input_filename)
        if os.path.exists(output_filename): os.remove(output_filename)

# 3. استقبال الفيديو وتشغيل المعالجة في الخلفية فوراً
@bot.message_handler(content_types=['video'])
def handle_video(message):
    # تشغيل المعالجة في دالة منفصلة (Thread) ليبقى البوت سريعاً جداً ومستجيباً لباقي الأوامر
    worker = Thread(target=process_video_and_burn_subtitles, args=(message.chat.id, message.video.file_id))
    worker.start()

# تشغيل البوت المستمر
if __name__ == '__main__':
    bot.infinity_polling()
