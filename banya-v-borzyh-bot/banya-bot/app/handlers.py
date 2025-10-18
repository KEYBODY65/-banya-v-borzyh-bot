from aiogram import Router, F, types
from aiogram.fsm.context import FSMContext
from aiogram.filters import Command
from aiogram.types import callback_query
from app.fsm import WaitingListStates
from app.database import get_db_session, Client, WaitingList
from app.keyboards import start_kb, help_kb, back_to_help, get_dates_keyboard, get_people_count_keyboard, get_waiting_confirmation_keyboard, get_waiting_management_keyboard
from app.admin_keyboards import get_admin_panel_keyboard
from app.admin_filters import AdminFilter
from .data import get_data

router = Router()
data = []

@router.message(Command("start"), ~AdminFilter())
async def user_start(message: types.Message):
    await message.answer(
        "👋 Добро пожаловать в банный комплекс!\n"
        "Выберите действие:",
        reply_markup=start_kb
    )

@router.message(F.text == "❓ Помощь")
async def help_command(message: types.Message):
    global data
    data = await get_data()
    kb = await help_kb(data)
    await message.answer(
        "❓ Выберите интересующий вас вопрос:",
        reply_markup=kb
    )

@router.callback_query(F.data == 'back_to_faq')
async def back_to_faq(callback: types.CallbackQuery):
    global data
    kb = await help_kb(data)
    await callback.message.edit_text(text='Выберите интересующий вас вопрос', reply_markup=kb)

@router.callback_query(F.data.isdigit())
async def update_data_handler(callback: types.CallbackQuery):
    global data
    await callback.message.edit_text(text=data[int(callback.data)]['Answer'], reply_markup=back_to_help)

@router.message(F.text == "📝 Запись в лист ожидания")
async def start_waiting_list(message: types.Message, state: FSMContext):
    keyboard = get_dates_keyboard()
    await message.answer(
        "📝 Запись в лист ожидания\n"
        "📅 Выберите предпочтительные даты:",
        reply_markup=keyboard
    )
    await state.set_state(WaitingListStates.choosing_dates)

@router.callback_query(WaitingListStates.choosing_dates, F.data.startswith("date_"))
async def choose_dates(callback: types.CallbackQuery, state: FSMContext):
    date_choice = callback.data
    
    dates_map = {
        "date_any": "Неважно",
        "date_specific": "Конкретные даты"
    }
    
    selected_dates = dates_map.get(date_choice)
    
    if selected_dates:
        await state.update_data(dates=selected_dates)
        await callback.message.edit_text(f"✅ Выбраны даты: {selected_dates}")
        
        if date_choice == "date_specific":
            await callback.message.answer(
                "📅 Укажите конкретные даты (например: 'завтра', 'суббота', '15-17 января'):"
            )
            await state.set_state(WaitingListStates.entering_specific_dates)
        else:
            keyboard = get_people_count_keyboard()
            await callback.message.answer(
                "👥 Выберите количество человек:",
                reply_markup=keyboard
            )
            await state.set_state(WaitingListStates.choosing_people_count)
    else:
        await callback.answer("❌ Неизвестный выбор дат")
    
    await callback.answer()

@router.message(WaitingListStates.entering_specific_dates)
async def enter_specific_dates(message: types.Message, state: FSMContext):
    specific_dates = message.text
    await state.update_data(specific_dates=specific_dates)
    
    keyboard = get_people_count_keyboard()
    await message.answer(
        "👥 Выберите количество человек:",
        reply_markup=keyboard
    )
    await state.set_state(WaitingListStates.choosing_people_count)

@router.callback_query(WaitingListStates.choosing_people_count, F.data.startswith("people_"))
async def choose_people_count(callback: types.CallbackQuery, state: FSMContext):
    people_data = callback.data
    
    people_map = {
        "people_1": "1",
        "people_2": "2", 
        "people_3": "3",
        "people_4": "4",
        "people_5": "5",
        "people_6": "6+"
    }
    
    people_count = people_map.get(people_data)
    
    if people_count:
        await state.update_data(people_count=people_count)
        await callback.message.edit_text(f"✅ Выбрано количество человек: {people_count}")
        
        await callback.message.answer(
            "📞 Введите ваш номер телефона для связи:"
        )
        await state.set_state(WaitingListStates.entering_phone)
    else:
        await callback.answer("❌ Неизвестное количество")
    
    await callback.answer()

@router.message(WaitingListStates.entering_phone)
async def enter_phone(message: types.Message, state: FSMContext):
    phone = message.text
    await state.update_data(phone=phone)
    
    data = await state.get_data()
    
    dates_text = data['dates']
    if data.get('specific_dates'):
        dates_text = f"{dates_text} ({data['specific_dates']})"
    
    confirmation_text = (
        "📋 Подтвердите запись в лист ожидания:\n\n"
        f"📅 Предпочтительные даты: {dates_text}\n"
        f"👥 Количество человек: {data['people_count']}\n"
        f"📞 Телефон: {phone}\n"
        f"👤 Имя: {message.from_user.first_name}\n\n"
        "📝 Вы будете добавлены в лист ожидания. С вами свяжутся при освобождении места."
    )
    
    keyboard = get_waiting_confirmation_keyboard()
    
    await message.answer(confirmation_text, reply_markup=keyboard)
    await state.set_state(WaitingListStates.confirming)

@router.callback_query(WaitingListStates.confirming, F.data == "confirm_waiting")
async def confirm_waiting(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    session = get_db_session()
    
    try:
        client = Client(
            user_id=callback.from_user.id,
            username=callback.from_user.username,
            first_name=callback.from_user.first_name,
            phone=data['phone']
        )
        session.add(client)
        session.flush()
        
        dates_info = data['dates']
        if data.get('specific_dates'):
            dates_info = f"{dates_info} ({data['specific_dates']})"
        
        waiting_entry = WaitingList(
            client_id=client.id,
            preferred_dates=dates_info,
            people_count=data['people_count']
        )
        session.add(waiting_entry)
        session.commit()
        
        await callback.message.edit_text(
            "✅ Вы добавлены в лист ожидания!\n\n"
            f"📅 Предпочтительные даты: {dates_info}\n"
            f"👥 Количество человек: {data['people_count']}\n\n"
            "📞 Мы свяжемся с вами при освобождении места.\n"
            "Вы можете проверить статус в разделе '📋 Мой статус в очереди'"
        )

    except Exception as e:
        session.rollback()
        await callback.message.edit_text("❌ Произошла ошибка при добавлении в лист ожидания")
        print(f"Database error: {e}")

    finally:
        session.close()
        await state.clear()

@router.callback_query(WaitingListStates.confirming, F.data == "cancel_waiting")
async def cancel_waiting(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.edit_text("❌ Запись в лист ожидания отменена")
    await state.clear()

@router.message(F.text == "📋 Мой статус в очереди")
async def show_my_waiting_status(message: types.Message):
    session = get_db_session()
    try:
        client = session.query(Client).filter_by(user_id=message.from_user.id).first()
        
        if not client:
            await message.answer("❌ У вас нет активных записей в листе ожидания")
            return
        
        waiting_entry = session.query(WaitingList).filter_by(
            client_id=client.id, 
            is_active=True
        ).first()
        
        if not waiting_entry:
            await message.answer("❌ У вас нет активных записей в листе ожидания")
            return
        
        all_waiting = session.query(WaitingList).filter_by(is_active=True).order_by(WaitingList.created_at).all()
        position = all_waiting.index(waiting_entry) + 1
        
        status_text = (
            "📋 Ваш статус в листе ожидания:\n\n"
            f"📅 Предпочтительные даты: {waiting_entry.preferred_dates}\n"
            f"👥 Количество человек: {waiting_entry.people_count}\n"
            f"📅 Дата записи: {waiting_entry.created_at.strftime('%d.%m.%Y %H:%M')}\n"
            f"📊 Позиция в очереди: {position} из {len(all_waiting)}\n\n"
        )
        
        keyboard = get_waiting_management_keyboard()
        await message.answer(status_text, reply_markup=keyboard)
        
    except Exception as e:
        await message.answer("❌ Произошла ошибка при получении статуса")
        print(f"Database error: {e}")
        
    finally:
        session.close()

@router.callback_query(F.data == "cancel_my_waiting")
async def cancel_my_waiting(callback: types.CallbackQuery):
    session = get_db_session()
    try:
        client = session.query(Client).filter_by(user_id=callback.from_user.id).first()
        
        if not client:
            await callback.answer("❌ Запись не найдена")
            return
        
        waiting_entry = session.query(WaitingList).filter_by(
            client_id=client.id, 
            is_active=True
        ).first()
        
        if waiting_entry:
            waiting_entry.is_active = False
            session.commit()
            await callback.message.edit_text("✅ Ваша запись удалена из листа ожидания")
        else:
            await callback.answer("❌ Активная запись не найдена")
            
    except Exception as e:
        session.rollback()
        await callback.message.edit_text("❌ Произошла ошибка при отмене записи")
        print(f"Database error: {e}")
        
    finally:
        session.close()

@router.callback_query(F.data == "back_to_main")
async def back_to_main(callback: types.CallbackQuery):
    await callback.message.edit_text(
        "👋 Добро пожаловать в банный комплекс!\n"
        "Выберите действие:"
    )
    await callback.message.answer(
        "Выберите действие:",
        reply_markup=start_kb
    )