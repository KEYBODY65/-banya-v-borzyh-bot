from aiogram.fsm.state import State, StatesGroup

class WaitingListStates(StatesGroup):
    choosing_dates = State()
    entering_specific_dates = State()
    choosing_people_count = State()
    entering_phone = State()
    confirming = State()

class BroadcastStates(StatesGroup):
    choosing_recipients = State()
    entering_message = State()
    confirming = State()

class AdminDeleteStates(StatesGroup):
    choosing_waiting_to_delete = State()
    confirming_deletion = State()

class UserDeleteStates(StatesGroup):
    confirming_deletion = State()
