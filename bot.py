(client, callback_query: CallbackQuery):
    user_id = callback_query.from_user.id
    cursor.execute("SELECT reminders FROM users WHERE user_id = ?", (user_id,))
    user = cursor.fetchone()
    if not user: return await callback_query.answer("Iltimos, avval lokatsiya yuboring!", show_alert=True)
    new_status = 0 if user[0] == 1 else 1
    cursor.execute("UPDATE users SET reminders = ? WHERE user_id = ?", (new_status, user_id))
    conn.commit()
    rem_text = "🔕 Eslatmani o'chirish" if new_status == 1 else "🔔 Eslatmani yoqish"
    new_kb = InlineKeyboardMarkup([[InlineKeyboardButton(rem_text, callback_data="toggle_namoz_remind")], [InlineKeyboardButton(f"⏱ Ogohlantirish: {user[1] if len(user) > 1 and user[1] else 10} daqiqa oldin", callback_data="set_remind_offset")]])
    await callback_query.answer("✅ Eslatmalar yoqildi!" if new_status == 1 else "🔕 Eslatmalar o'chirildi.", show_alert=True)
    await callback_query.message.edit_reply_markup(reply_markup=new_kb)

@app.on_callback_query(filters.regex(r"^set_remind_offset$"))
async def set_remind_offset_menu(client, callback_query: CallbackQuery):
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("0 daqiqa", callback_data="apply_offset:0"), InlineKeyboardButton("5 daqiqa", callback_data="apply_offset:5")],
        [InlineKeyboardButton("10 daqiqa", callback_data="apply_offset:10"), InlineKeyboardButton("15 daqiqa", callback_data="apply_offset:15")],
        [InlineKeyboardButton("20 daqiqa", callback_data="apply_offset:20"), InlineKeyboardButton("30 daqiqa", callback_data="apply_offset:30")],
        [InlineKeyboardButton("⬅️ Orqaga", callback_data="close_offset_menu")]
    ])
    await callback_query.message.edit_text("⏱ <b>Ogohlantirish vaqtini tanlang:</b>\n\nNamoz vaqtidan qancha daqiqa oldin eslatma kelishini xohlaysiz?", reply_markup=kb, parse_mode=ParseMode.HTML)

@app.on_callback_query(filters.regex(r"^apply_offset:"))
async def apply_remind_offset(client, callback_query: CallbackQuery):
    offset = int(callback_query.data.split(":")[1])
    user_id = callback_query.from_user.id
    cursor.execute("UPDATE users SET reminder_offset = ? WHERE user_id = ?", (offset, user_id))
    conn.commit()
    await callback_query.answer(f"✅ Ogohlantirish {offset} daqiqa oldin qilib belgilandi!", show_alert=True)
    cursor.execute("SELECT reminders FROM users WHERE user_id = ?", (user_id,))
    user_data = cursor.fetchone()
    rem_status = user_data[0] if user_data else 0
    rem_text = "🔕 Eslatmani o'chirish" if rem_status == 1 else "🔔 Eslatmani yoqish"
    new_kb = InlineKeyboardMarkup([[InlineKeyboardButton(rem_text, callback_data="toggle_namoz_remind")], [InlineKeyboardButton(f"⏱ Ogohlantirish: {offset} daqiqa oldin", callback_data="set_remind_offset")]])
    await callback_query.message.edit_reply_markup(reply_markup=new_kb)

@app.on_callback_query(filters.regex(r"^close_offset_menu$"))
async def close_offset_menu(client, callback_query: CallbackQuery):
    user_id = callback_query.from_user.id
    cursor.execute("SELECT reminders, reminder_offset FROM users WHERE user_id = ?", (user_id,))
    user_data = cursor.fetchone()
    rem_status = user_data[0] if user_data else 0
    offset = user_data[1] if user_data and user_data[1] else 10
    rem_text = "🔕 Eslatmani o'chirish" if rem_status == 1 else "🔔 Eslatmani yoqish"
    new_kb = InlineKeyboardMarkup([[InlineKeyboardButton(rem_text, callback_data="toggle_namoz_remind")], [InlineKeyboardButton(f"⏱ Ogohlantirish: {offset} daqiqa oldin", callback_data="set_remind_offset")]])
    await callback_query.message.edit_reply_markup(reply_markup=new_kb)

# --- ASOSIY LOOP ---
async def main():
    print("Bot ishga tushmoqda...")
    await load_data_from_github() 
    await app.start()
    asyncio.create_task(namoz_eslatma_loop(app))
    asyncio.create_task(weekly_winners_notifier(app))
    await app.set_bot_commands([
        BotCommand("start", "Botni ishga tushirish"),
        BotCommand("quiz", "Viktorinani boshlash"),
        BotCommand("top", "Haftalik reytingni ko'rish"),
        BotCommand("namoz", "Namoz vaqtlarini bilish"),
        BotCommand("qibla", "Qibla yo'nalishini aniqlash"),
        BotCommand("ramazon", "Ramazonga qolgan kunlar")
    ], scope=BotCommandScopeAllPrivateChats())
    await app.set_bot_commands([
        BotCommand("start", "Botni ishga tushirish"),
        BotCommand("quiz", "Viktorinani boshlash"),
        BotCommand("top", "Guruh reytingini ko'rish"),
        BotCommand("ramazon", "Ramazonga qolgan kunlar")
    ], scope=BotCommandScopeAllGroupChats())
    print("Bot muvaffaqiyatli ishga tushdi...")
    await idle()
    await app.stop()

if __name__ == "__main__":
    app.run(main())
