import os
import telebot
import yt_dlp
import threading
import http.server
import time

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = "ضع_رقم_الـ_ID_الخاص_بك_هنا" # ضع هنا رقم الـ ID الخاص بك (تستطيع معرفته من بوتات كشف الآيدي)

bot = telebot.TeleBot(BOT_TOKEN)

# دالة لحفظ المستخدمين
def save_user(chat_id):
    if not os.path.exists("users.txt"):
        with open("users.txt", "w") as f: f.write("")
    
    with open("users.txt", "r+") as f:
        users = f.read().splitlines()
        if str(chat_id) not in users:
            f.write(f"{chat_id}\n")

# السيرفر الوهمي
def run_dummy_server():
    port = int(os.environ.get("PORT", 8080))
    server = http.server.HTTPServer(('', port), http.server.SimpleHTTPRequestHandler)
    server.serve_forever()

threading.Thread(target=run_dummy_server, daemon=True).start()

# --- الأوامر ---
@bot.message_handler(commands=['start'])
def send_welcome(message):
    save_user(message.chat.id) # حفظ المستخدم تلقائياً
    bot.reply_to(message, "✅ البوت يعمل وجاهز للتحميل!")

# هذا الأمر للإرسال للجميع (استخدمه مرة واحدة)
@bot.message_handler(commands=['announce'])
def broadcast_fix(message):
    if str(message.chat.id) != ADMIN_ID:
        return # لا يفعل شيئاً إذا لم تكن أنت المستخدم
    
    if os.path.exists("users.txt"):
        with open("users.txt", "r") as f:
            users = f.read().splitlines()
            
        bot.reply_to(message, f"📢 جاري الإرسال لـ {len(users)} مستخدم...")
        for user_id in users:
            try:
                bot.send_message(user_id, "✅ تم إصلاح جميع المشاكل في البوت! الآن يعمل بسرعة وكفاءة.")
            except:
                continue # لتخطي المستخدمين الذين قاموا بحظر البوت
        bot.reply_to(message, "✅ تم الإرسال للجميع بنجاح.")

@bot.message_handler(func=lambda m: True)
def handle_msg(message):
    save_user(message.chat.id) # حفظ المستخدمين الجدد أيضاً
    # (بقية الكود الخاص بالتحميل كما هو)
    status_msg = bot.reply_to(message, "⏳ جاري التحميل...")
    # ... ضع هنا منطق التحميل الخاص بك ...
    bot.edit_message_text("تم التحميل (مثال)", message.chat.id, status_msg.message_id)

bot.infinity_polling()
