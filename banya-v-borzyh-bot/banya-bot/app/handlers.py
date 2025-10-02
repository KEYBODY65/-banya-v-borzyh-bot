from aiogram import Router

from .keyboards import help_kb, back_to_help
from .data import get_data

router = Router()
data = []

@router.message()
async def faq_menu(message):
    global data 
    data = await get_data()
    kb = await help_kb(data)
    await message.answer(text='Выберите интересующий вас вопрос', reply_markup=kb)

@router.callback_query(lambda m: m.data == 'back_to_faq')
async def back_to_faq(callback):
    global data
    kb = await help_kb(data)
    await callback.message.edit_text(text='Выберите интересующий вас вопрос', reply_markup=kb)


@router.callback_query(lambda m: m.data.isdigit())
async def update_data_handler(callback):
    global data
    await callback.message.edit_text(text=data[int(callback.data)]['Answer'], reply_markup=back_to_help)


