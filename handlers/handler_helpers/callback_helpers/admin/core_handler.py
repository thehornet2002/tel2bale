import os

from pyrogram.types import Message

from db.backup import create_database_backup_async
from db.model_async import get_top_users, set_state
from handlers.handler_helpers.callback_helpers.decorators import admin_required
from utils.keyboards import (
    build_back_keyboard,
    build_back_management_keyboard,
    build_management_keyboard,
)


@admin_required
async def management(message: Message, user_id: int) -> None:
    await set_state(user_id, "management")
    await message.edit_text(
        "ادمین عزیز به پنل مدیریت ربات خوش آمدید",
        reply_markup=build_management_keyboard()
    )


# صفحه‌ی "management" و "back_to_management" دقیقا یک محتوا و رفتار دارن،
# پس به جای تکرار کد فقط یک نام مستعار (alias) براش تعریف شده.
back_to_management = management


@admin_required
async def get_db(message: Message, user_id: int) -> None:
    backup_path = None

    try:
        backup_path = await create_database_backup_async()
        await message.reply_document(
            document=backup_path,
            caption="✅ نسخه پشتیبان دیتابیس"
        )
    except Exception as e:
        await message.reply_text(
            f"❌ خطا در گرفتن backup دیتابیس:\n{e}",
            reply_markup=build_back_management_keyboard()
        )
    finally:
        if backup_path and os.path.exists(backup_path):
            try:
                os.remove(backup_path)
            except Exception:
                pass


@admin_required
async def show_10_high(message: Message, user_id: int) -> None:
    users = await get_top_users()

    lines = ["Telegram ID | Bale ID | Downloaded Volume"]
    for user in users:
        lines.append(
            f"{user['tg_id']} | "
            f"{user['bale_id'] or '-'} | "
            f"{user['downloaded_volume']}"
        )

    await message.edit_text(
        "\n".join(lines),
        reply_markup=build_back_management_keyboard()
    )


@admin_required
async def change_donation_link(message: Message, user_id: int) -> None:
    await set_state(user_id, 'change_donation_link')
    await message.edit_text(
        'لطفا لینک دونیت خود را وارد کنید.',
        reply_markup=build_back_keyboard()
    )


@admin_required
async def set_support_group(message: Message, user_id: int) -> None:
    await set_state(user_id, 'set_support_group')
    await message.edit_text(
        'لطفا ID عددی گروه پشتیبانی را ارسال کنید (ربات باید عضو آن گروه باشد).',
        reply_markup=build_back_keyboard()
    )


@admin_required
async def set_max_users(message: Message, user_id: int) -> None:
    await set_state(user_id, 'set_max_users')
    await message.edit_text(
        'لطفا سقف کل کاربرانی که می‌توانند ربات را start کنند را وارد کنید (0 برای بدون محدودیت).',
        reply_markup=build_back_keyboard()
    )


@admin_required
async def set_max_active_users(message: Message, user_id: int) -> None:
    await set_state(user_id, 'set_max_active_users')
    await message.edit_text(
        'لطفا سقف کاربران فعال (کسانی که bale_id یا bale_token دارند) را وارد کنید (0 برای بدون محدودیت).',
        reply_markup=build_back_keyboard()
    )