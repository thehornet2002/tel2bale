"""
هندلرهای مدیریتی ادمین: بن/آنبن کاربران، افزودن/حذف ادمین، تغییر لینک دونیت.
"""
import config
from pyrogram.types import Message
from db import model_async
from config import (
    add_admin,
    remove_admin,
    update_donation_link,
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
        if i == user_id:
            await model_async.set_state(user_id, 'management')
            await message.reply_text('شما نمی‌توانید خود را بن کنید.', reply_markup=build_back_management_keyboard())
            return
        if await model_async.check_admin(i) or i in config.ADMIN_IDS:
            await model_async.set_state(user_id, 'management')
            await message.reply_text('امکان بن کردن ادمین وجود ندارد.', reply_markup=build_back_management_keyboard())
            return

    for i in tg_ids:
        await model_async.ban_user(i)
    await model_async.set_state(user_id, 'management')
    await message.reply_text('کاربر با موفقیت مسدود شد.', reply_markup=build_back_management_keyboard())


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
    await message.reply_text('کاربر از بن خارج شد.', reply_markup=build_back_management_keyboard())


@admin_only
async def enter_telegram_ban(message: Message, user_id: int):
    tg_id = await get_valid_id(message)
    if not tg_id:
        return

    if tg_id == user_id:
        await model_async.set_state(user_id, 'management')
        await message.reply_text('شما نمی‌توانید خود را بن کنید.', reply_markup=build_back_management_keyboard())
        return

    if await model_async.check_admin(tg_id) or tg_id in config.ADMIN_IDS:
        await model_async.set_state(user_id, 'management')
        await message.reply_text('امکان بن کردن ادمین وجود ندارد.', reply_markup=build_back_management_keyboard())
        return

    if not await model_async.is_user_exist(tg_id):
        await model_async.set_state(user_id, 'management')
        await message.reply_text('کاربری با این ID عددی تلگرام در دیتابیس یافت نشد.', reply_markup=build_back_management_keyboard())
        return

    await model_async.ban_user(tg_id)
    await model_async.set_state(user_id, 'management')
    await message.reply_text('کاربر با موفقیت مسدود شد.', reply_markup=build_back_management_keyboard())


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
        await model_async.add_user(target_id, is_admin=True)

    if not await model_async.set_admin(target_id):
        await message.reply_text('مشکل در تغییر در دیتابیس', reply_markup=build_back_management_keyboard())
        await model_async.set_state(user_id, 'management')
        return

    if not await add_admin(target_id):
        await message.reply_text('مشکل در ذخیره ادمین (کاربر ممکن است از قبل در لیست باشد).', reply_markup=build_back_management_keyboard())
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

    if target_id not in config.ADMIN_IDS and 0 <= target_id < len(config.ADMIN_IDS):
        target_id = config.ADMIN_IDS[target_id]

    if target_id == user_id:
        await message.reply_text('شما نمی‌توانید خود را از لیست ادمین‌ها حذف کنید.', reply_markup=build_back_management_keyboard())
        await model_async.set_state(user_id, 'management')
        return

    if target_id not in config.ADMIN_IDS:
        await message.reply_text('کاربر مورد نظر در لیست ادمین‌ها یافت نشد.', reply_markup=build_back_management_keyboard())
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
async def add_whitelist_send_id(message: Message, user_id: int):
    target_id = await get_valid_id(message)
    if not target_id:
        return

    await model_async.add_to_whitelist(target_id)
    await model_async.set_state(user_id, 'management')
    await message.reply_text(
        f"✅ کاربر `{target_id}` با موفقیت به لیست سفید اضافه شد.",
        reply_markup=build_back_management_keyboard()
    )


@admin_only
async def remove_whitelist_send_id(message: Message, user_id: int):
    target_id = await get_valid_id(message)
    if not target_id:
        return

    if await model_async.check_admin(target_id) or target_id in config.ADMIN_IDS:
        await model_async.set_state(user_id, 'management')
        await message.reply_text('امکان حذف ادمین از لیست سفید در حالت فعال بودن آن وجود ندارد.', reply_markup=build_back_management_keyboard())
        return

    await model_async.remove_from_whitelist(target_id)
    await model_async.set_state(user_id, 'management')
    await message.reply_text(
        f"✅ کاربر `{target_id}` با موفقیت از لیست سفید حذف شد.",
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


@admin_only
async def enter_poll_data_handler(message: Message, user_id: int):
    raw_text = (message.text or "").strip()
    lines = [line.strip() for line in raw_text.splitlines() if line.strip()]
    if len(lines) < 3:
        await message.reply_text(
            "❌ فرمت نامعتبر است. حداقل یک صورت سوال و دو گزینه لازم است.\nهر مورد را در یک خط بنویسید.",
            reply_markup=build_back_management_keyboard()
        )
        return

    question = lines[0]
    options = lines[1:]

    await model_async.close_active_poll()
    poll_id = await model_async.create_poll(question, options)
    await model_async.set_state(user_id, 'management')
    await message.reply_text(
        f"✅ نظرسنجی با شناسه **#{poll_id}** با موفقیت ایجاد و فعال شد.\n\n"
        f"❓ سوال: {question}\n"
        f"🔢 تعداد گزینه‌ها: {len(options)}\n\n"
        "کاربران می‌توانند از دکمه «📊 نظرسنجی کاربران» در منوی اصلی ربات در آن شرکت کنند.",
        reply_markup=build_back_management_keyboard()
    )


@admin_only
async def enter_ticket_reply_handler(message: Message, user_id: int):
    state = await model_async.get_state(user_id)
    # state format: ticket_reply_TICKETID_STATUS_PAGE
    parts = state.split("_")
    try:
        ticket_id = int(parts[2])
    except (IndexError, ValueError):
        await model_async.set_state(user_id, 'management')
        await message.reply_text("❌ خطا در شناسایی تیکت.", reply_markup=build_back_management_keyboard())
        return

    ticket = await model_async.get_ticket(ticket_id)
    if not ticket:
        await model_async.set_state(user_id, 'management')
        await message.reply_text("❌ تیکت یافت نشد.", reply_markup=build_back_management_keyboard())
        return

    reply_content = message.text or message.caption or "پاسخ از سمت ادمین"
    user_sent = False
    try:
        header = f"💬 **پاسخ پشتیبانی به تیکت #{ticket['id']} ({ticket.get('category_title') or 'عمومی'}):**\n\n"
        await message._client.send_message(ticket["telegram_id"], header)
        await message.copy(ticket["telegram_id"])
        user_sent = True
    except Exception:
        user_sent = False

    await model_async.answer_ticket(ticket_id, reply_content)
    await model_async.reset_support_message_count(ticket["telegram_id"])
    await model_async.set_state(user_id, 'management')

    feedback = "و به کاربر تحویل داده شد." if user_sent else "اما پیام به کاربر ارسال نشد (شاید ربات را بلاک کرده باشد)."
    await message.reply_text(
        f"✅ پاسخ با موفقیت ثبت شد و وضعیت تیکت #{ticket_id} به «پاسخ داده شده» تغییر یافت {feedback}",
        reply_markup=build_back_management_keyboard()
    )


@admin_only
async def enter_category_title_handler(message: Message, user_id: int):
    title = (message.text or "").strip()
    if not title or len(title) > 60:
        await message.reply_text("❌ طول عنوان باید بین ۱ تا ۶۰ کاراکتر باشد.")
        return

    from db.redis_client import redis_set_state
    await model_async.set_state(user_id, f"choosing_category_anon_{title}")
    from utils.keyboards import build_category_anonymity_keyboard
    await message.reply_text(
        f"📌 **عنوان موضوع:** «{title}»\n\nلطفاً نوع ارسال تیکت برای این موضوع را تعیین فرمایید:",
        reply_markup=build_category_anonymity_keyboard()
    )
