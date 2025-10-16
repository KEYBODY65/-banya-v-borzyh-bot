from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from .data import get_data


def get_admin_panel_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📊 Посмотреть лист ожидания")],
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
    
    keyboard.append([
        InlineKeyboardButton(text="🔙 Назад", callback_data="back_broadcast")
    ])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_back_to_admin_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 В админ-панель", callback_data="back_to_admin")]
    ])


def get_broadcast_confirmation_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Отправить", callback_data="confirm_broadcast"),
            InlineKeyboardButton(text="❌ Отменить", callback_data="cancel_broadcast")
        ]
    ])
