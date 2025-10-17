from aiogram.filters import Filter
from aiogram import types
from dotenv import load_dotenv
import os

load_dotenv()

def is_admin(user_id: int) -> bool:
    admin_ids = []
    
    try:
        admin_id = os.getenv("ADMIN_ID_MAIN")
        if admin_id and admin_id.strip().isdigit():
            admin_ids.append(int(admin_id.strip()))
    except:
        pass
    
    try:
        admin_id_additional = os.getenv("ADMIN_ID_ADDITIONAL")
        if admin_id_additional and admin_id_additional.strip().isdigit():
            admin_ids.append(int(admin_id_additional.strip()))
    except:
        pass
        
    try:
        admin_id_additional_2 = os.getenv("ADMIN_ID_ADDITIONAL_2")
        if admin_id_additional_2 and admin_id_additional_2.strip().isdigit():
            admin_ids.append(int(admin_id_additional_2.strip()))
    except:
        pass
    
    return user_id in admin_ids

class AdminFilter(Filter):
    async def __call__(self, message: types.Message) -> bool:
        return is_admin(message.from_user.id)

class CallbackAdminFilter(Filter):
    async def __call__(self, callback: types.CallbackQuery) -> bool:
        return is_admin(callback.from_user.id)