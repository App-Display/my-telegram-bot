import telebot

# 🔴 ضع توكن البوت الخاص بك هنا لتشغيله محلياً واستخراج الأيديات
BOT_TOKEN = "8128965245:AAHH3QO-vGGfWmFtCicmw7T9gmBcMWbUg6E"
bot = telebot.TeleBot(BOT_TOKEN)

print("⚡ البوت يعمل الآن... أرسل أي مقطع صوتي أو بصمة لاستخراج الـ ID الصحيح.")

# 1. معالج البصمات الصوتية (Voice Notes)
@bot.message_handler(content_types=['voice'])
def handle_voice_id(message):
    file_id = message.voice.file_id
    text_reply = (
        "✅ تم استلام (بصمة صوتية) بنجاح!\n"
        "🔗 الـ ID الصحيح الخاص بها هو:\n\n"
        f"`{file_id}`\n\n"
        "💡 اضغط على النص أعلاه لنسخه مباشرة وضعه في الكود."
    )
    bot.reply_to(message, text_reply, parse_mode="Markdown")

# 2. معالج الملفات الصوتية/الموسيقى (Audio Files)
@bot.message_handler(content_types=['audio'])
def handle_audio_id(message):
    file_id = message.audio.file_id
    text_reply = (
        "✅ تم استلام (ملف صوتي/موسيقى) بنجاح!\n"
        "🔗 الـ ID الصحيح الخاص به هو:\n\n"
        f"`{file_id}`\n\n"
        "💡 اضغط على النص أعلاه لنسخه مباشرة وضعه في الكود."
    )
    bot.reply_to(message, text_reply, parse_mode="Markdown")

if __name__ == '__main__':
    bot.infinity_polling()
