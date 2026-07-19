from pyrogram.types import Message

from db.model_async import set_state
from handlers.handler_helpers.callback_helpers.decorators import admin_required
from utils.keyboards import build_back_management_keyboard


@admin_required
async def set_profile_photo(message: Message, user_id: int) -> None:
    await set_state(user_id, "set_profile_photo_send_photo")
    await message.edit_text(
        "لطفا تصویر پروفایل را ارسال کنید.",
        reply_markup=build_back_management_keyboard()
    )