from aiogram.filters import Filter
from aiogram import types
from dotenv import load_dotenv
import os

load_dotenv()

admin_id = os.getenv("ADMIN_ID")

def is_admin(user_id: int) -> bool:
    try:
        admin_id_value = int(admin_id)
        return user_id == admin_id_value
    except (ValueError, TypeError) as e:
        print(f"Error in is_admin: {e}, admin_id: {admin_id}")
        return False

class AdminFilter(Filter):
    async def __call__(self, message: types.Message) -> bool:
        return is_admin(message.from_user.id)

class CallbackAdminFilter(Filter):
    async def __call__(self, callback: types.CallbackQuery) -> bool:
        return is_admin(callback.from_user.id)