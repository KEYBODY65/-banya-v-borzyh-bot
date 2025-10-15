from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from .data import get_data

start_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="❓ Помощь")],
        [KeyboardButton(text="📝 Запись в лист ожидания")],
        [KeyboardButton(text="📋 Мой статус в очереди")]
    ],
    resize_keyboard=True
)

cancel_kb = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text="❌ Отмена")]],
    resize_keyboard=True
)

async def help_kb(data):
    keyboard = []
    for i, row in enumerate(data):
        if row['Answer'].startswith('http'):
            keyboard.append([InlineKeyboardButton(text=row['Question'], url=row['Answer'])])
        else:
            keyboard.append([InlineKeyboardButton(text=row['Question'], callback_data=str(i))])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

back_to_help = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='🔙 Назад к помощи', callback_data='back_to_faq')]
])

def get_dates_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🗓️ Неважно", callback_data="date_any")],
        [InlineKeyboardButton(text="🎉 Выходные", callback_data="date_weekend")],
        [InlineKeyboardButton(text="📅 Будни", callback_data="date_weekdays")],
        [InlineKeyboardButton(text="📌 Конкретные даты", callback_data="date_specific")]
    ])

def get_people_count_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="1 человек", callback_data="people_1")],
        [InlineKeyboardButton(text="2 человека", callback_data="people_2")],
        [InlineKeyboardButton(text="3 человека", callback_data="people_3")],
        [InlineKeyboardButton(text="4 человека", callback_data="people_4")],
        [InlineKeyboardButton(text="5 человек", callback_data="people_5")],
        [InlineKeyboardButton(text="6+ человек", callback_data="people_6")]
    ])

def get_waiting_confirmation_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Подтвердить", callback_data="confirm_waiting"),
            InlineKeyboardButton(text="❌ Отменить", callback_data="cancel_waiting")
        ]
    ])

def get_waiting_management_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="❌ Отменить запись", callback_data="cancel_my_waiting")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_main")]
    ])