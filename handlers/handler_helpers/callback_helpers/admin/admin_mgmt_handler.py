from pyrogram.types import Message

from config import ADMIN_IDS
from db.model_async import set_state
from handlers.handler_helpers.callback_helpers.decorators import admin_required
from utils.keyboards import build_back_management_keyboard


@admin_required
async def add_admin(message: Message, user_id: int) -> None:
    await set_state(user_id, "add_admin_send_id")
    await message.edit_text("ID عددی تلگرام ادمین جدید را وارد کنید:")


@admin_required
async def delete_admin(message: Message, user_id: int) -> None:
    await set_state(user_id, "delete_admin_send_id")

    lines = ["ID ادمینی که می‌خواهید حذف کنید:"]
    for index, admin_id in enumerate(ADMIN_IDS):
        lines.append(f"{index} - {admin_id}")

    await message.edit_text(
        "\n".join(lines),
        reply_markup=build_back_management_keyboard()
    )