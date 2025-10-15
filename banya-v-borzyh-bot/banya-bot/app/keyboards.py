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

def get_booking_confirmation_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Подтвердить", callback_data="confirm_booking"),
            InlineKeyboardButton(text="❌ Отменить", callback_data="cancel_booking")
        ]
    ])

def get_my_bookings_keyboard(future_bookings):
    keyboard = []
    
    for booking in future_bookings:
        keyboard.append([
            InlineKeyboardButton(
                text=f"❌ Отменить запись на {booking.booking_date.strftime('%d.%m.%Y %H:%M')}",
                callback_data=f"select_booking_{booking.id}"
            )
        ])
    
    keyboard.append([
        InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_main")
    ])
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_cancellation_confirmation_keyboard(booking_id):
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Да, отменить", callback_data=f"confirm_cancel_{booking_id}"),
            InlineKeyboardButton(text="❌ Нет, вернуться", callback_data="back_to_bookings_list")
        ]
    ])


def get_services_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🛁 Сауна на 2 часа - 1500 руб", callback_data="service_2h")],
        [InlineKeyboardButton(text="🛁 Сауна на 3 часа - 2000 руб", callback_data="service_3h")],
        [InlineKeyboardButton(text="⭐ VIP сауна на 2 часа - 2500 руб", callback_data="service_vip")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_time")]
    ])

def get_time_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="10:00", callback_data="time_10:00")],
        [InlineKeyboardButton(text="12:00", callback_data="time_12:00")],
        [InlineKeyboardButton(text="14:00", callback_data="time_14:00")],
        [InlineKeyboardButton(text="16:00", callback_data="time_16:00")],
        [InlineKeyboardButton(text="18:00", callback_data="time_18:00")],
        [InlineKeyboardButton(text="20:00", callback_data="time_20:00")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_date")]
    ])

main_menu_inline = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="📅 Забронировать", callback_data="book")],
    [InlineKeyboardButton(text="📋 Мои записи", callback_data="my_bookings")],
    [InlineKeyboardButton(text="❓ Помощь", callback_data="help")]
])
