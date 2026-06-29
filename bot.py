import os
import telebot
import yt_dlp
import threading
import http.server
import time

# 1. إعداد التوكن والآيدي الخاص بك (ADMIN_ID)
BOT_TOKEN = os.getenv("BOT_TOKEN")
# استبدل هذا الرقم بالآيدي الخاص بك (يمكنك معرفته من بوت @userinfobot)
ADMIN_ID = "123456789" 

if not BOT_TOKEN:
    print("❌ خطأ: لم يتم العثور على BOT_TOKEN!")
    exit()

bot = telebot.TeleBot(BOT_TOKEN)

# --- دالة حفظ المستخدمين ---
def save_user(chat_id):
    try:
        with open("users.txt", "a") as f:
            f.write(f"{chat_id}\n")
    except:
        pass

def get_unique_users():
    if not os.path.exists("users.txt"): return []
    with open("users.txt", "r") as f:
        # قراءة الملف وإزالة التكرارات
        return list(set(f.read().splitlines()))

# 2. سيرفر للحفاظ على البوت نشطاً
def run_dummy_server():
    port = int(os.environ.get("PORT", 8080))
    httpd = http.server.HTTPServer(('', port), http.server.SimpleHTTPRequestHandler)
    print(f"🌐 السيرفر يعمل على المنفذ {port}")
    httpd.serve_forever()

# 3. دالة التحميل
def download_video(url, chat_id):
    file_path = f'/tmp/video_{chat_id}.mp4'
    ydl_opts = {
        'format': 'best',
        'outtmpl': file_path,
        'quiet': False,
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36'
    }
    try:
        if os.path.exists(file_path): os.remove(file_path)
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            return file_path, info.get('title', 'Video')
    except Exception as e:
        return None, str(e)

# 4. أوامر البوت
@bot.message_handler(commands=['start'])
def send_welcome(message):
    save_user(message.chat.id) # حفظ المستخدم عند البدء
    bot.reply_to(message, "🚀 البوت يعمل! أرسل رابط الفيديو للتحميل.")

# --- أمر الإعلان (Broadcast) ---
@bot.message_handler(commands=['announce'])
def broadcast(message):
    if str(message.chat.id) != ADMIN_ID:
        return # يتجاهل الأمر إذا لم تكن أنت المرسل

    users = get_unique_users()
    bot.reply_to(message, f"📢 جاري الإرسال لـ {len(users)} مستخدم...")
    
    for uid in users:
        try:
            bot.send_message(uid, "✅ تم إصلاح جميع المشاكل في البوت! الآن يعمل بسرعة وكفاءة. جرب التحميل الآن!")
            time.sleep(0.1) # تأخير بسيط لمنع حظر البوت من تيليجرام
        except:
            continue # تخطي المستخدمين الذين قاموا بحظر البوت
    
    bot.reply_to(message, "✅ تم الإرسال للجميع بنجاح.")

@bot.message_handler(func=lambda m: True)
def handle_msg(message):
    save_user(message.chat.id) # حفظ المستخدم عند إرسال أي رابط
    url = message.text.strip()
    if not url.startswith("http"):
        bot.reply_to(message, "يرجى إرسال رابط صحيح يبدأ بـ http")
        return

    status = bot.reply_to(message, "⏳ جاري التحميل، يرجى الانتظار...")
    
    file_path, title = download_video(url, message.chat.id)
    
    if file_path and os.path.exists(file_path):
        with open(file_path, 'rb') as v:
            bot.send_video(message.chat.id, v, caption=title)
        bot.delete_message(message.chat.id, status.message_id)
        os.remove(file_path)
    else:
        bot.edit_message_text(f"❌ فشل التحميل. الرابط قد لا يكون مدعوماً.\nالخطأ: {title}", message.chat.id, status.message_id)

# 5. تشغيل
if __name__ == '__main__':
    print("🤖 جاري بدء البوت...")
    threading.Thread(target=run_dummy_server, daemon=True).start()
    bot.infinity_polling()
