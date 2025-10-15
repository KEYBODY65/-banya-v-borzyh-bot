from aiogram import Router, F, types
from app.fsm import BookingStates, CancelBookingStates
from app.database import get_db_session, Client, Booking
from datetime import datetime, date, time
from aiogram.fsm.context import FSMContext
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from .keyboards import start_kb, help_kb, back_to_help, get_booking_confirmation_keyboard, get_my_bookings_keyboard, get_cancellation_confirmation_keyboard, get_services_keyboard, get_time_keyboard
from .data import get_data


router = Router()
data = []

@router.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer(
        "👋 Добро пожаловать в банный комплекс!\n"
        "Выберите действие:",
        reply_markup=start_kb
    )

@router.message(F.text == "Помощь")
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

@router.message(F.text == "📅 Забронировать")
async def start_booking(message: types.Message, state: FSMContext):
    await message.answer(
        "🎯 Давайте запишем вас в сауну!\n"
        "Выберите дату (в формате ДД.ММ.ГГГГ):"
    )
    await state.set_state(BookingStates.choosing_date)
    

@router.message(BookingStates.choosing_date)
async def choose_date(message: types.Message, state: FSMContext):
    try:
        booking_date = datetime.strptime(message.text, "%d.%m.%Y").date()
        today = date.today()
        
        if booking_date < today:
            await message.answer("❌ Нельзя выбрать прошедшую дату. Введите корректную дату:")
            return
        
        await state.update_data(booking_date=booking_date)
        
        keyboard = get_time_keyboard()
        
        await message.answer(
            "⏰ Выберите время:",
            reply_markup=keyboard
        )
        await state.set_state(BookingStates.choosing_time)

    except ValueError:
        await message.answer("❌ Неверный формат даты. Используйте ДД.ММ.ГГГГ:")


@router.message(BookingStates.choosing_time)
async def choose_time(message: types.Message, state: FSMContext):
    try:
        booking_time = datetime.strptime(message.text, "%H:%M").time()
        
        available_times = [time(10,0), time(12,0), time(14,0), time(16,0), time(18,0), time(20,0)]
        if booking_time not in available_times:
            await message.answer("❌ Это время недоступно. Выберите из предложенных:")
            return
        
        state_data = await state.get_data()
        booking_datetime = datetime.combine(state_data['booking_date'], booking_time)
        
        await state.update_data(booking_datetime=booking_datetime)

        keyboard = get_services_keyboard()
        
        await message.answer(
            "🛁 Выберите услугу:",
            reply_markup=keyboard
        )
        await state.set_state(BookingStates.choosing_service)
        
    except ValueError:
        await message.answer("❌ Неверный формат времени. Используйте ЧЧ:ММ:")

@router.message(BookingStates.choosing_service)
async def choose_service(message: types.Message, state: FSMContext):
    service = message.text
    await state.update_data(service=service)
    
    await message.answer(
        "📞 Введите ваш номер телефона для связи:"
    )
    await state.set_state(BookingStates.entering_phone)


@router.message(BookingStates.entering_phone)
async def enter_phone(message: types.Message, state: FSMContext):
    phone = message.text
    await state.update_data(phone=phone)
    
    data = await state.get_data()
    
    confirmation_text = (
        "📋 Подтвердите запись:\n"
        f"📅 Дата: {data['booking_datetime'].strftime('%d.%m.%Y %H:%M')}\n"
        f"🛁 Услуга: {data['service']}\n"
        f"📞 Телефон: {phone}\n"
        f"👤 Имя: {message.from_user.first_name}"
    )
    
    keyboard = get_booking_confirmation_keyboard()
    
    await message.answer(confirmation_text, reply_markup=keyboard)
    await state.set_state(BookingStates.confirming)

@router.callback_query(BookingStates.confirming, F.data == "confirm_booking")
async def confirm_booking(callback: types.CallbackQuery, state: FSMContext):
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
        
        booking = Booking(
            client_id=client.id,
            booking_date=data['booking_datetime'],
            service=data['service']
        )
        session.add(booking)
        session.commit()
        
        await callback.message.edit_text(
            "✅ Запись успешно создана!\n"
            f"📅 Ваше время: {data['booking_datetime'].strftime('%d.%m.%Y %H:%M')}\n"
            f"🛁 Услуга: {data['service']}\n\n"
            "Ждем вас! 🏊‍♂️"
        )

    except Exception as e:
        session.rollback()
        await callback.message.edit_text("❌ Произошла ошибка при создании записи")
        print(f"Database error: {e}")

    finally:
        session.close()
        await state.clear()

@router.callback_query(BookingStates.confirming, F.data == "cancel_booking")
async def cancel_booking(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.edit_text("❌ Запись отменена")
    await state.clear()

@router.message(F.text == "📋 Мои записи")
async def show_my_bookings(message: types.Message, state: FSMContext):
    session = get_db_session()
    try:
        client = session.query(Client).filter_by(user_id=message.from_user.id).first()
        
        if not client:
            await message.answer("❌ У вас пока нет записей")
            return
        
        future_bookings = session.query(Booking).filter(
            Booking.client_id == client.id,
            Booking.booking_date >= datetime.now()
        ).order_by(Booking.booking_date).all()
        
        if not future_bookings:
            await message.answer("❌ У вас нет активных записей для отмены")
            return
        
        bookings_text = "📋 Ваши активные записи:\n\n"
        
        for i, booking in enumerate(future_bookings, 1):
            bookings_text += (
                f"{i}. {booking.booking_date.strftime('%d.%m.%Y %H:%M')}\n"
                f"   Услуга: {booking.service}\n\n"
            )
        
        reply_markup = get_my_bookings_keyboard(future_bookings)
        
        await state.update_data(bookings={booking.id: booking for booking in future_bookings})
        
        await message.answer(bookings_text, reply_markup=reply_markup)
        await state.set_state(CancelBookingStates.choosing_booking_to_cancel)
        
    except Exception as e:
        await message.answer("❌ Произошла ошибка при получении записей")
        print(f"Database error: {e}")
        
    finally:
        session.close()


@router.callback_query(CancelBookingStates.choosing_booking_to_cancel, F.data.startswith("select_booking_"))
async def select_booking_for_cancellation(callback: types.CallbackQuery, state: FSMContext):
    booking_id = int(callback.data.split("_")[2])
    
    data = await state.get_data()
    bookings = data.get('bookings', {})
    booking = bookings.get(booking_id)
    
    if not booking:
        await callback.answer("❌ Запись не найдена")
        return
    
    confirmation_text = (
        "❓ Вы уверены, что хотите отменить запись?\n\n"
        f"📅 Дата: {booking.booking_date.strftime('%d.%m.%Y %H:%M')}\n"
        f"🛁 Услуга: {booking.service}"
    )
    
    keyboard = get_cancellation_confirmation_keyboard(booking_id)
    
    await callback.message.edit_text(confirmation_text, reply_markup=keyboard)
    await state.set_state(CancelBookingStates.confirming_cancellation)
    await state.update_data(selected_booking_id=booking_id)
    await callback.answer()

@router.callback_query(CancelBookingStates.confirming_cancellation, F.data.startswith("confirm_cancel_"))
async def confirm_booking_cancellation(callback: types.CallbackQuery, state: FSMContext):
    session = get_db_session()
    try:
        booking_id = int(callback.data.split("_")[2])
        
        state_data = await state.get_data()
        if state_data.get('selected_booking_id') != booking_id:
            await callback.answer("❌ Несоответствие данных")
            return
        
        booking = session.query(Booking).filter_by(id=booking_id).first()
        
        if not booking:
            await callback.message.edit_text("❌ Запись не найдена")
            return
        
        client = session.query(Client).filter_by(
            user_id=callback.from_user.id,
            id=booking.client_id
        ).first()
        
        if not client:
            await callback.message.edit_text("❌ Это не ваша запись")
            return
        
        booking_info = f"{booking.booking_date.strftime('%d.%m.%Y %H:%M')} - {booking.service}"
        
        session.delete(booking)
        session.commit()
        
        await callback.message.edit_text(
            f"✅ Запись успешно отменена:\n"
            f"📅 {booking_info}"
        )
        
    except Exception as e:
        session.rollback()
        await callback.message.edit_text("❌ Произошла ошибка при отмене записи")
        print(f"Database error: {e}")
        
    finally:
        session.close()
        await state.clear()

@router.callback_query(CancelBookingStates.choosing_booking_to_cancel, F.data == "back_to_main")
async def back_to_main_from_bookings(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.edit_text(
        "👋 Добро пожаловать в банный комплекс!\n"
        "Выберите действие:"
    )
    await callback.message.answer("Выберите действие:", reply_markup=start_kb)
    await state.clear()

@router.callback_query(CancelBookingStates.confirming_cancellation, F.data == "back_to_bookings_list")
async def back_to_bookings_list(callback: types.CallbackQuery, state: FSMContext):
    session = get_db_session()
    try:
        client = session.query(Client).filter_by(user_id=callback.from_user.id).first()
        
        if not client:
            await callback.message.edit_text("❌ У вас пока нет записей")
            return
        
        future_bookings = session.query(Booking).filter(
            Booking.client_id == client.id,
            Booking.booking_date >= datetime.now()
        ).order_by(Booking.booking_date).all()
        
        if not future_bookings:
            await callback.message.edit_text("❌ У вас нет активных записей для отмены")
            return
        
        bookings_text = "📋 Ваши активные записи:\n\n"
        
        for i, booking in enumerate(future_bookings, 1):
            bookings_text += (
                f"{i}. {booking.booking_date.strftime('%d.%m.%Y %H:%M')}\n"
                f"   Услуга: {booking.service}\n\n"
            )
        
        reply_markup = get_my_bookings_keyboard(future_bookings)
        
        await state.update_data(bookings={booking.id: booking for booking in future_bookings})
        
        await callback.message.edit_text(bookings_text, reply_markup=reply_markup)
        await state.set_state(CancelBookingStates.choosing_booking_to_cancel)
        
    except Exception as e:
        await callback.message.edit_text("❌ Произошла ошибка при получении записей")
        print(f"Database error: {e}")
        
    finally:
        session.close()



@router.callback_query(BookingStates.choosing_time, F.data.startswith("time_"))
async def choose_time_callback(callback: types.CallbackQuery, state: FSMContext):
    time_data = callback.data.replace("time_", "")
    
    try:
        booking_time = datetime.strptime(time_data, "%H:%M").time()
        
        available_times = [time(10,0), time(12,0), time(14,0), time(16,0), time(18,0), time(20,0)]
        if booking_time not in available_times:
            await callback.answer("❌ Это время недоступно")
            return
        
        state_data = await state.get_data()
        booking_datetime = datetime.combine(state_data['booking_date'], booking_time)
        
        await state.update_data(booking_datetime=booking_datetime)

        keyboard = get_services_keyboard()
        
        await callback.message.edit_text(f"✅ Выбрано время: {time_data}")
        await callback.message.answer(
            "🛁 Выберите услугу:",
            reply_markup=keyboard
        )
        await state.set_state(BookingStates.choosing_service)
        
    except ValueError:
        await callback.answer("❌ Ошибка формата времени")
    
    await callback.answer()

@router.callback_query(BookingStates.choosing_time, F.data == "back_to_date")
async def back_to_date_from_time(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.edit_text(
        "🎯 Выберите дату (в формате ДД.ММ.ГГГГ):"
    )
    await state.set_state(BookingStates.choosing_date)
    await callback.answer()

@router.callback_query(BookingStates.choosing_service, F.data.startswith("service_"))
async def choose_service_callback(callback: types.CallbackQuery, state: FSMContext):
    service_data = callback.data
    
    services_map = {
        "service_2h": "Сауна на 2 часа - 1500 руб",
        "service_3h": "Сауна на 3 часа - 2000 руб", 
        "service_vip": "VIP сауна на 2 часа - 2500 руб"
    }
    
    service = services_map.get(service_data)
    
    if service:
        await state.update_data(service=service)
        await callback.message.edit_text(f"✅ Выбрана услуга: {service}")
        
        await callback.message.answer(
            "📞 Введите ваш номер телефона для связи:"
        )
        await state.set_state(BookingStates.entering_phone)
    else:
        await callback.answer("❌ Неизвестная услуга")
    
    await callback.answer()

@router.callback_query(BookingStates.choosing_service, F.data == "back_to_time")
async def back_to_time_from_services(callback: types.CallbackQuery, state: FSMContext):
    keyboard = get_time_keyboard()
    
    await callback.message.edit_text(
        "⏰ Выберите время:",
        reply_markup=keyboard
    )
    await state.set_state(BookingStates.choosing_time)
    await callback.answer()
