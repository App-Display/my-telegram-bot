import os
import telebot
import yt_dlp
import threading
import http.server
import time

# --- الإعدادات ---
BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()
ADMIN_ID = "ضع_رقم_الآيدي_الخاص_بك_هنا" # <--- ضع رقمك هنا! (يمكنك معرفته من بوت @userinfobot)

# التحقق من التوكن
if not BOT_TOKEN:
    print("❌ خطأ: BOT_TOKEN غير موجود في إعدادات Variables!")
    exit(1)

try:
    bot = telebot.TeleBot(BOT_TOKEN)
except Exception as e:
    print(f"❌ خطأ في الاتصال: {e}")
    exit(1)

# --- حفظ المستخدمين ---
def save_user(chat_id):
    try:
        with open("users.txt", "a") as f:
            f.write(f"{chat_id}\n")
    except:
        pass

def get_users():
    if not os.path.exists("users.txt"): return []
    with open("users.txt", "r") as f:
        # قراءة الملف وحذف التكرار
        return list(set(f.read().splitlines()))

# --- سيرفر للبقاء نشطاً ---
def run_dummy_server():
    port = int(os.environ.get("PORT", 8080))
    server = http.server.HTTPServer(('', port), http.server.SimpleHTTPRequestHandler)
    print(f"🌐 السيرفر يعمل على المنفذ {port}")
    server.serve_forever()

threading.Thread(target=run_dummy_server, daemon=True).start()

# --- دالة التحميل ---
def download_video(url, chat_id):
    file_path = f'/tmp/vid_{chat_id}.mp4'
    ydl_opts = {
        'format': 'best',
        'outtmpl': file_path,
        'quiet': True,
        'no_warnings': True,
    }
    try:
        if os.path.exists(file_path): os.remove(file_path)
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            return file_path, info.get('title', 'Video')
    except Exception as e:
        return None, str(e)

# --- الأوامر ---
@bot.message_handler(commands=['start'])
def send_welcome(message):
    save_user(message.chat.id)
    bot.reply_to(message, "✅ أهلاً بك! البوت يعمل الآن. أرسل رابط الفيديو للتحميل.")

# أمر الإعلان (Broadcast)
@bot.message_handler(commands=['announce'])
def announce(message):
    if str(message.chat.id) != ADMIN_ID:
        return # يتجاهل أي شخص غيرك

    users = get_users()
    msg = "✅ تم إصلاح جميع المشاكل في البوت! الآن يعمل بسرعة وكفاءة. جرب التحميل الآن!"
    
    bot.reply_to(message, f"📢 جاري الإرسال لـ {len(users)} مستخدم...")
    
    for uid in users:
        try:
            bot.send_message(uid, msg)
            time.sleep(0.1) # لمنع حظر البوت من تيليجرام
        except:
            continue
    bot.reply_to(message, "✅ تم الإرسال للجميع!")

@bot.message_handler(func=lambda m: True)
def handle_msg(message):
    save_user(message.chat.id)
    status_msg = bot.reply_to(message, "⏳ جاري المعالجة...")
    path, title = download_video(message.text.strip(), message.chat.id)
    
    if path and os.path.exists(path):
        with open(path, 'rb') as v:
            bot.send_video(message.chat.id, v, caption=title)
        bot.delete_message(message.chat.id, status_msg.message_id)
        os.remove(path)
    else:
        bot.edit_message_text(f"❌ خطأ: الرابط غير مدعوم.\n{title}", message.chat.id, status_msg.message_id)

print("🤖 البوت يعمل الآن...")
bot.infinity_polling()
