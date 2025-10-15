from aiogram import Router, F, types
from app.fsm import BookingStates
from app.database import get_db_session, Client, Booking
from datetime import datetime, date, time
from aiogram.fsm.context import FSMContext
from aiogram.filters import Command
from .keyboards import help_kb, back_to_help, start_kb
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

@router.callback_query(lambda m: m.data == 'back_to_faq')
async def back_to_faq(callback):
    global data
    kb = await help_kb(data)
    await callback.message.edit_text(text='Выберите интересующий вас вопрос', reply_markup=kb)

@router.callback_query(lambda m: m.data.isdigit())
async def update_data_handler(callback):
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
        
        # Миша, тут нужно внести изменения, согласуй время!!!!
        await message.answer(
            "⏰ Выберите время (в формате ЧЧ:ММ):\n"
            "Доступное время: 10:00, 12:00, 14:00, 16:00, 18:00, 20:00"
        )
        await state.set_state(BookingStates.choosing_time)

    except ValueError:
        await message.answer("❌ Неверный формат даты. Используйте ДД.ММ.ГГГГ:")


@router.message(BookingStates.choosing_time)
async def choose_time(message: types.Message, state: FSMContext):
    try:
        booking_time = datetime.strptime(message.text, "%H:%M").time()
        
        # Соответсвенно, тут тоже измени
        available_times = [time(10,0), time(12,0), time(14,0), time(16,0), time(18,0), time(20,0)]
        if booking_time not in available_times:
            await message.answer("❌ Это время недоступно. Выберите из предложенных:")
            return
        
        data = await state.get_data()
        booking_datetime = datetime.combine(data['booking_date'], booking_time)
        
        await state.update_data(booking_datetime=booking_datetime)

        # Тут измени цены!!!!!
        await message.answer(
            "🛁 Выберите услугу:\n"
            "1. Сауна на 2 часа - 1500 руб\n"
            "2. Сауна на 3 часа - 2000 руб\n"
            "3. VIP сауна на 2 часа - 2500 руб"
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
    
    keyboard = types.InlineKeyboardMarkup(inline_keyboard=[
        [
            types.InlineKeyboardButton(text="✅ Подтвердить", callback_data="confirm_booking"),
            types.InlineKeyboardButton(text="❌ Отменить", callback_data="cancel_booking")
        ]
    ])
    
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
async def show_my_bookings(message: types.Message):
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
        
        past_bookings = session.query(Booking).filter(
            Booking.client_id == client.id,
            Booking.booking_date < datetime.now()
        ).order_by(Booking.booking_date.desc()).limit(5).all() # Получаем последние 5 записей
        
        if not future_bookings and not past_bookings:
            await message.answer("❌ У вас пока нет записей")
            return
        
        response_text = "📋 Ваши записи:\n\n"
        
        if future_bookings:
            response_text += "🔜 **Предстоящие записи:**\n"
            for i, booking in enumerate(future_bookings, 1):
                response_text += (
                    f"{i}. {booking.booking_date.strftime('%d.%m.%Y %H:%M')}\n"
                    f"   Услуга: {booking.service}\n\n"
                )
        
        if past_bookings:
            response_text += "📝 **История записей:**\n"
            for i, booking in enumerate(past_bookings, 1):
                response_text += (
                    f"{i}. {booking.booking_date.strftime('%d.%m.%Y %H:%M')}\n"
                    f"   Услуга: {booking.service}\n\n"
                )
        
        await message.answer(response_text)
        
    except Exception as e:
        await message.answer("❌ Произошла ошибка при получении записей")
        print(f"Database error: {e}")
        
    finally:
        session.close()








