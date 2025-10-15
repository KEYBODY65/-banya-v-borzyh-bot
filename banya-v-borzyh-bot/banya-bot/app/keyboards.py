from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from collections import defaultdict

from .data import get_data

start_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Помощь")],
        [KeyboardButton(text="📅 Забронировать")],
        [KeyboardButton(text="📋 Мои записи")]
    ],
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



