"""
هندلرهای مدیریتی ادمین: بن/آنبن کاربران، افزودن/حذف ادمین، تغییر لینک دونیت.
"""
from pyrogram.types import Message
from db import model_async
from config import (
    add_admin,
    remove_admin,
    update_donation_link,
    set_support_group,
    set_support_message_enabled,
    set_max_users,
    set_max_active_users,
)
from utils.keyboards import build_back_management_keyboard
from utils.parser import validate_link
from handlers.handler_helpers.message_helpers.common import admin_only, get_valid_id


@admin_only
async def enter_bale_ban(message: Message, user_id: int):
    bale_id = await get_valid_id(message)
    if not bale_id:
        return

    tg_ids = await model_async.get_telegram_ids_by_bale_id(bale_id=bale_id)
    if not tg_ids:
        await model_async.set_state(user_id, 'management')
        await message.reply_text('کاربری با این ID عددی بله در دیتابیس یافت نشد.', reply_markup=build_back_management_keyboard())
        return

    for i in tg_ids:
        await model_async.ban_user(i)
    await model_async.set_state(user_id, 'management')
    await message.reply_text('کاربر با خاک یکسان شد.', reply_markup=build_back_management_keyboard())


@admin_only
async def enter_bale_unban(message: Message, user_id: int):
    bale_id = await get_valid_id(message)
    if not bale_id:
        return

    tg_ids = await model_async.get_telegram_ids_by_bale_id(bale_id)
    if not tg_ids:
        await model_async.set_state(user_id, 'management')
        await message.reply_text('کاربری با این ID عددی بله در دیتابیس یافت نشد.', reply_markup=build_back_management_keyboard())
        return

    for i in tg_ids:
        await model_async.unban_user(i)
    await model_async.set_state(user_id, 'management')
    await message.reply_text('کاربر از بن خارج شد', reply_markup=build_back_management_keyboard())


@admin_only
async def enter_telegram_ban(message: Message, user_id: int):
    tg_id = await get_valid_id(message)
    if not tg_id:
        return

    if not await model_async.is_user_exist(tg_id):
        await model_async.set_state(user_id, 'management')
        await message.reply_text('کاربری با این ID عددی تلگرام در دیتابیس یافت نشد.', reply_markup=build_back_management_keyboard())
        return

    await model_async.ban_user(tg_id)
    await model_async.set_state(user_id, 'management')
    await message.reply_text('کاربر با خاک یکسان شد.', reply_markup=build_back_management_keyboard())


@admin_only
async def enter_telegram_unban(message: Message, user_id: int):
    tg_id = await get_valid_id(message)
    if not tg_id:
        return

    if not await model_async.is_user_exist(tg_id):
        await model_async.set_state(user_id, 'management')
        await message.reply_text('کاربری با این ID عددی تلگرام در دیتابیس یافت نشد.', reply_markup=build_back_management_keyboard())
        return

    await model_async.unban_user(tg_id)
    await model_async.set_state(user_id, 'management')
    await message.reply_text('کاربر از بن خارج شد.', reply_markup=build_back_management_keyboard())


@admin_only
async def add_admin_send_id(message: Message, user_id: int):
    target_id = await get_valid_id(message)
    if not target_id:
        await model_async.set_state(user_id, 'management')
        return

    if not await model_async.is_user_exist(target_id):
        await message.reply_text('کاربری با این ID عددی در دیتابیس یافت نشد.', reply_markup=build_back_management_keyboard())
        await model_async.set_state(user_id, 'management')
        return

    if not await model_async.set_admin(target_id):
        await message.reply_text('مشکل در تغییر در دیتابیس', reply_markup=build_back_management_keyboard())
        await model_async.set_state(user_id, 'management')
        return

    if not await add_admin(target_id):
        await message.reply_text('مشکل در فایل .env', reply_markup=build_back_management_keyboard())
        await model_async.set_state(user_id, 'management')
        return

    await message.reply_text('کاربر مورد نظر ادمین شد.', reply_markup=build_back_management_keyboard())
    await model_async.set_state(user_id, 'management')


@admin_only
async def delete_admin_send_id(message: Message, user_id: int):
    target_id = await get_valid_id(message)
    if not target_id:
        await model_async.set_state(user_id, 'management')
        return

    if not await remove_admin(target_id):
        await message.reply_text('مشکل در فایل .env', reply_markup=build_back_management_keyboard())
        await model_async.set_state(user_id, 'management')
        return

    if not await model_async.unset_admin(target_id):
        await message.reply_text('مشکل در تغییر در دیتابیس', reply_markup=build_back_management_keyboard())
        await model_async.set_state(user_id, 'management')
        return

    await message.reply_text('فرد مورد نظر از ادمینی خارج شد.', reply_markup=build_back_management_keyboard())
    await model_async.set_state(user_id, 'management')


@admin_only
async def change_donation_link(message: Message, user_id: int):
    try:
        new_link = await validate_link(message.text)
        if not new_link:
            await model_async.set_state(user_id, 'management')
            await message.reply_text(
                'لطفا لینک معتبر وارد کنید.',
                reply_markup=build_back_management_keyboard()
            )
            return
        result = await update_donation_link(new_link)
        if not result:
            await model_async.set_state(user_id, 'management')
            await message.reply_text(
                'لطفا لینک معتبر وارد کنید.',
                reply_markup=build_back_management_keyboard()
            )
            return
        await model_async.set_state(user_id, 'management')
        await message.reply_text(
            'لینک دونیت با موفقیت تغییر کرد.',
            reply_markup=build_back_management_keyboard()
        )
    except Exception:
        await model_async.set_state(user_id, 'management')
        await message.reply_text(
            'تغییر لینک دونیت با مشکل مواجه شد.',
            reply_markup=build_back_management_keyboard()
        )


@admin_only
async def set_support_group_send_id(message: Message, user_id: int):
    try:
        group_id = int((message.text or "").strip())
    except ValueError:
        await message.reply_text('لطفا فقط ID عددی گروه را ارسال کنید.')
        return

    await set_support_group(group_id)

    enabled = False
    try:
        me = await message._client.get_me()
        member = await message._client.get_chat_member(group_id, me.id)
        enabled = member.status.value in ("member", "administrator", "creator", "owner")
    except Exception:
        enabled = False

    await set_support_message_enabled(enabled)
    await model_async.set_state(user_id, 'management')

    if enabled:
        await message.reply_text(
            '✅ گروه پشتیبانی با موفقیت تنظیم شد و ربات عضو آن است. گزینه «پیام به پشتیبانی» برای کاربران فعال شد.',
            reply_markup=build_back_management_keyboard()
        )
    else:
        await message.reply_text(
            '⚠️ گروه پشتیبانی ذخیره شد اما ربات عضو آن گروه نیست. لطفا ابتدا ربات را به گروه اضافه کنید سپس دوباره تلاش کنید.',
            reply_markup=build_back_management_keyboard()
        )


@admin_only
async def set_max_users_send_value(message: Message, user_id: int):
    try:
        value = int((message.text or "").strip())
        if value < 0:
            raise ValueError
    except ValueError:
        await message.reply_text('لطفا فقط عدد صحیح و مثبت (یا صفر برای بدون محدودیت) ارسال کنید.')
        return

    current_count = await model_async.get_user_count()
    if value != 0 and value < current_count:
        await message.reply_text(
            f'در حال حاضر {current_count} کاربر در ربات ثبت‌نام کرده‌اند؛ سقف نمی‌تواند کمتر از این مقدار باشد.',
            reply_markup=build_back_management_keyboard()
        )
        return

    await set_max_users(value)
    await model_async.set_state(user_id, 'management')
    await message.reply_text('سقف کل کاربران با موفقیت تنظیم شد.', reply_markup=build_back_management_keyboard())


@admin_only
async def set_max_active_users_send_value(message: Message, user_id: int):
    try:
        value = int((message.text or "").strip())
        if value < 0:
            raise ValueError
    except ValueError:
        await message.reply_text('لطفا فقط عدد صحیح و مثبت (یا صفر برای بدون محدودیت) ارسال کنید.')
        return

    current_count = await model_async.get_active_user_count()
    if value != 0 and value < current_count:
        await message.reply_text(
            f'در حال حاضر {current_count} کاربر فعال وجود دارد؛ سقف نمی‌تواند کمتر از این مقدار باشد.',
            reply_markup=build_back_management_keyboard()
        )
        return

    await set_max_active_users(value)
    await model_async.set_state(user_id, 'management')
    await message.reply_text('سقف کاربران فعال با موفقیت تنظیم شد.', reply_markup=build_back_management_keyboard())
