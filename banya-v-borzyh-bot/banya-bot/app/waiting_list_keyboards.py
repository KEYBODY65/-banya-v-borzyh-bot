from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

def get_waiting_list_with_contacts_keyboard(waiting_list):
    keyboard = []
    
    for i, (waiting, client) in enumerate(waiting_list, 1):
        keyboard.append([
            InlineKeyboardButton(
                text=f"📞 Связаться с {client.first_name or 'клиентом'}",
                url=f"tg://user?id={client.user_id}"
            )
        ])
    
    # Кнопка обновления списка
    keyboard.append([
        InlineKeyboardButton(text="🔄 Обновить", callback_data="refresh_waiting_list")
    ])
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)