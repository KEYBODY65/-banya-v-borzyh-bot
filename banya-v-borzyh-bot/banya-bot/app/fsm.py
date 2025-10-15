from aiogram.fsm.state import State, StatesGroup

class BookingStates(StatesGroup):
    choosing_date = State()
    choosing_time = State()
    choosing_service = State()
    entering_phone = State()
    confirming = State()

