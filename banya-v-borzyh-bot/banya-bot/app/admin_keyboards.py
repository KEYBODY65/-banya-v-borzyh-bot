from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

def get_admin_panel_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📊 Посмотреть лист ожидания")],
            [KeyboardButton(text="🗑️ Удалить из листа ожидания")],
            [KeyboardButton(text="📢 Сделать рассылку")],
            [KeyboardButton(text="🔙 В главное меню")]
        ],
        resize_keyboard=True
    )

def get_broadcast_recipients_keyboard(dates_list):
    keyboard = []
    keyboard.append([InlineKeyboardButton(text="👥 Всем клиентам", callback_data="broadcast_all")])
    
    for date in dates_list:
        if date and date != "Неважно":
            keyboard.append([InlineKeyboardButton(text=f"📅 {date}", callback_data=f"broadcast_{date}")])
    
    keyboard.append([InlineKeyboardButton(text="❌ Отмена", callback_data="broadcast_cancel")])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_delete_waiting_keyboard(waiting_list):
    keyboard = []
    
    for waiting, client in waiting_list:
        username = f"@{client.username}" if client.username else client.first_name
        button_text = f"{username} - {waiting.people_count} чел. - {waiting.preferred_dates}"
        callback_data = f"delete_waiting_{waiting.id}"
        
        keyboard.append([
            InlineKeyboardButton(text=button_text, callback_data=callback_data)
        ])
    
    keyboard.append([
        InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_delete")
    ])
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_delete_confirmation_keyboard(waiting_id):
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Удалить", callback_data=f"confirm_delete_{waiting_id}"),
            InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_delete")
        ]
    ])

def get_broadcast_confirmation_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Отправить", callback_data="confirm_broadcast"),
            InlineKeyboardButton(text="❌ Отменить", callback_data="cancel_broadcast")
        ]
    ])
    