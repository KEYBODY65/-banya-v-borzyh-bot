from aiogram import Router, F, types, Bot
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from aiogram.filters import Command
from app.database import get_db_session, Client, WaitingList
from app.fsm import BroadcastStates
from app.admin_keyboards import get_admin_panel_keyboard, get_broadcast_recipients_keyboard, get_back_to_admin_keyboard, get_broadcast_confirmation_keyboard
from app.waiting_list_keyboards import get_waiting_list_with_contacts_keyboard
from app.admin_filters import AdminFilter, CallbackAdminFilter
from dotenv import load_dotenv
import os


admin_router = Router()


@admin_router.message(Command("start"), AdminFilter())
async def admin_panel(message: types.Message):
    keyboard = get_admin_panel_keyboard()
    await message.answer(
        "👨‍💼 Админ-панель\n"
        "Выберите действие:",
        reply_markup=keyboard
    )

@admin_router.message(F.text == "📊 Посмотреть лист ожидания", AdminFilter())
async def view_waiting_list(message: types.Message):
    session = get_db_session()
    try:
        waiting_list = session.query(WaitingList, Client).join(
            Client, WaitingList.client_id == Client.id
        ).filter(WaitingList.is_active == True).order_by(WaitingList.created_at).all()
        
        if not waiting_list:
            await message.answer("📭 Лист ожидания пуст")
            return
        
        total_count = len(waiting_list)
        message_text = f"📋 Лист ожидания ({total_count} записей):\n\n"
        
        for i, (waiting, client) in enumerate(waiting_list, 1):
            message_text += (
                f"{i}. 👤 {client.first_name or 'Без имени'}\n"
                f"   📞 {client.phone or 'Не указано'}\n"
                f"   👥 {waiting.people_count} чел.\n"
                f"   📅 {waiting.preferred_dates}\n"
                f"   ⏰ {waiting.created_at.strftime('%d.%m.%Y %H:%M')}\n\n"
            )
        
        keyboard = get_waiting_list_with_contacts_keyboard(waiting_list)
        await message.answer(message_text, reply_markup=keyboard)
        
    except Exception as e:
        await message.answer("❌ Ошибка при получении листа ожидания")
        print(f"Database error: {e}")
    finally:
        session.close()

@admin_router.message(F.text == "📢 Сделать рассылку", AdminFilter())
async def start_broadcast(message: types.Message, state: FSMContext):
    session = get_db_session()
    try:
        dates = session.query(WaitingList.preferred_dates).filter(
            WaitingList.is_active == True,
            WaitingList.preferred_dates.isnot(None),
            WaitingList.preferred_dates != ""
        ).distinct().all()
        
        dates_list = [date[0] for date in dates if date[0] and date[0] != "cancel"]
        
        if not dates_list:
            await message.answer("❌ Нет доступных дат для рассылки")
            return
        
        keyboard = get_broadcast_recipients_keyboard(dates_list)
        await message.answer(
            "📢 Выберите получателей рассылки:",
            reply_markup=keyboard
        )
        await state.set_state(BroadcastStates.choosing_recipients)
        
    except Exception as e:
        await message.answer("❌ Ошибка при получении данных")
        print(f"Database error: {e}")
    finally:
        session.close()

@admin_router.message(BroadcastStates.entering_message, AdminFilter())
async def enter_broadcast_message(message: types.Message, state: FSMContext):
    broadcast_message = message.text
    await state.update_data(message=broadcast_message)
    
    data = await state.get_data()
    
    if data['recipients'] == "all":
        recipient_text = "👥 Всем клиентам из листа ожидания"
    else:
        recipient_text = f"📅 Клиентам с датой: {data['date_filter']}"
    
    confirmation_text = (
        "📋 Подтвердите рассылку:\n\n"
        f"{recipient_text}\n\n"
        f"📝 Сообщение:\n{broadcast_message}\n\n"
        "Отправить?"
    )
    
    keyboard = get_broadcast_confirmation_keyboard()
    await message.answer(confirmation_text, reply_markup=keyboard)
    await state.set_state(BroadcastStates.confirming)

@admin_router.message(F.text == "🔙 В главное меню", AdminFilter())
async def exit_to_main_menu(message: types.Message, state: FSMContext):
    await state.clear()
    keyboard = get_admin_panel_keyboard()
    await message.answer(
        "👨‍💼 Админ-панель\n"
        "Выберите действие:",
        reply_markup=keyboard
    )

@admin_router.callback_query(F.data == "refresh_waiting_list", CallbackAdminFilter())
async def refresh_waiting_list(callback: types.CallbackQuery, bot: Bot):
    await callback.answer("Обновляем список...")
    
    await callback.message.delete()
    
    session = get_db_session()
    try:
        waiting_list = session.query(WaitingList, Client).join(
            Client, WaitingList.client_id == Client.id
        ).filter(WaitingList.is_active == True).order_by(WaitingList.created_at).all()
        
        if not waiting_list:
            await callback.message.answer("📭 Лист ожидания пуст")
            return
        
        total_count = len(waiting_list)
        message_text = f"📋 Лист ожидания ({total_count} записей):\n\n"
        
        for i, (waiting, client) in enumerate(waiting_list, 1):
            message_text += (
                f"{i}. 👤 {client.first_name or 'Без имени'}\n"
                f"   📞 {client.phone or 'Не указано'}\n"
                f"   👥 {waiting.people_count} чел.\n"
                f"   📅 {waiting.preferred_dates}\n"
                f"   ⏰ {waiting.created_at.strftime('%d.%m.%Y %H:%M')}\n\n"
            )
        
        keyboard = get_waiting_list_with_contacts_keyboard(waiting_list)
        await callback.message.answer(message_text, reply_markup=keyboard)
        
    except Exception as e:
        await callback.message.answer("❌ Ошибка при получении листа ожидания")
        print(f"Database error: {e}")
    finally:
        session.close()

@admin_router.callback_query(BroadcastStates.choosing_recipients, F.data.startswith("broadcast_"), CallbackAdminFilter())
async def choose_broadcast_recipients(callback: types.CallbackQuery, state: FSMContext):
    recipient_type = callback.data.replace("broadcast_", "")
    
    if recipient_type == "all":
        await state.update_data(recipients="all", date_filter=None)
        recipient_text = "всем клиентам"
    else:
        await state.update_data(recipients="by_date", date_filter=recipient_type)
        recipient_text = f"клиентам с датой: {recipient_type}"
    
    await callback.message.edit_text(f"✅ Получатели: {recipient_text}")
    await callback.message.answer(
        "✍️ Введите сообщение для рассылки:"
    )
    await state.set_state(BroadcastStates.entering_message)
    await callback.answer()

@admin_router.callback_query(BroadcastStates.confirming, F.data == "confirm_broadcast", CallbackAdminFilter())
async def confirm_broadcast(callback: types.CallbackQuery, state: FSMContext, bot: Bot):
    data = await state.get_data()
    session = get_db_session()
    
    try:
        if data['recipients'] == "all":
            clients = session.query(Client).join(
                WaitingList, Client.id == WaitingList.client_id
            ).filter(WaitingList.is_active == True).all()
        else:
            clients = session.query(Client).join(
                WaitingList, Client.id == WaitingList.client_id
            ).filter(
                WaitingList.is_active == True,
                WaitingList.preferred_dates == data['date_filter']
            ).all()
        
        sent_count = 0
        failed_count = 0
        
        for client in clients:
            try:
                await bot.send_message(
                    chat_id=client.user_id,
                    text=data['message']
                )
                sent_count += 1
            except Exception:
                failed_count += 1
        
        await callback.message.edit_text(
            f"✅ Рассылка завершена!\n"
            f"📤 Отправлено: {sent_count}\n"
            f"❌ Не отправлено: {failed_count}"
        )
        
    except Exception as e:
        await callback.message.edit_text("❌ Ошибка при рассылке")
        print(f"Broadcast error: {e}")
    finally:
        session.close()
        await state.clear()

@admin_router.callback_query(BroadcastStates.confirming, F.data == "cancel_broadcast", CallbackAdminFilter())
async def cancel_broadcast_confirmation(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.edit_text("❌ Рассылка отменена")
    await state.clear()
    
    keyboard = get_admin_panel_keyboard()
    await callback.message.answer(
        "👨‍💼 Админ-панель\nВыберите действие:",
        reply_markup=keyboard
    )
    await callback.answer()


@admin_router.callback_query(BroadcastStates.choosing_recipients, F.data == "back_broadcast", CallbackAdminFilter())
async def back_broadcast_early(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.edit_text("↩️ Возвращаемся назад")
    await state.clear()
    
    keyboard = get_admin_panel_keyboard()
    await callback.message.answer(
        "👨‍💼 Админ-панель\nВыберите действие:",
        reply_markup=keyboard
    )
    await callback.answer()

@admin_router.callback_query(BroadcastStates.confirming, F.data == "back_broadcast", CallbackAdminFilter())
async def back_broadcast_from_confirm(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.edit_text("↩️ Возвращаемся к вводу сообщения")
    
    await callback.message.answer(
        "✍️ Введите сообщение для рассылки:"
    )
    await state.set_state(BroadcastStates.entering_message)
    await callback.answer()

@admin_router.callback_query(BroadcastStates.entering_message, F.data == "back_broadcast", CallbackAdminFilter())
async def back_from_message(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.edit_text("↩️ Возвращаемся к выбору получателей")
    
    session = get_db_session()
    try:
        dates = session.query(WaitingList.preferred_dates).filter(
            WaitingList.is_active == True,
            WaitingList.preferred_dates.isnot(None),
            WaitingList.preferred_dates != "",
            WaitingList.preferred_dates != "cancel"
        ).distinct().all()
        
        dates_list = [date[0] for date in dates if date[0]]
        
        keyboard = get_broadcast_recipients_keyboard(dates_list)
        await callback.message.answer(
            "📢 Выберите получателей рассылки:",
            reply_markup=keyboard
        )
        await state.set_state(BroadcastStates.choosing_recipients)
        
    except Exception as e:
        await callback.message.answer("❌ Ошибка при получении данных")
        print(f"Database error: {e}")
    finally:
        session.close()
    await callback.answer()

