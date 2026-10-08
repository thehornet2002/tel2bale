import re
from pyrogram.types import Message
from db import model_async
from services.bale_service import bale_bot
from utils.keyboards import build_back_keyboard
from handlers.handler_helpers.message_helpers.common import get_valid_id


async def enter_bale_id(message: Message, user_id: int):
    id_num = await get_valid_id(message)
    if not id_num:
        return

    await model_async.set_bale_id(tg_id=user_id, bale_id=id_num)
    await model_async.set_state(user_id, 'home')
    await message.reply_text('ID عددی شما در بله با موفقیت ثبت شد.', reply_markup=build_back_keyboard())


async def set_bale_token_bot(message: Message, user_id: int):
    token = (message.text or "").strip()
    if not token or len(token) > 128 or not re.match(r"^\d+:[A-Za-z0-9_\-]+$", token):
        await model_async.set_state(user_id, 'home')
        await message.reply_text(
            'توکن بات بله معتبر نمی باشد لطفا دوباره تلاش کنید.',
            reply_markup=build_back_keyboard()
        )
        return

    verify_state = await bale_bot.verify_token(token)
    if verify_state:
        await model_async.set_bale_token(user_id, token)
        await model_async.set_state(user_id, 'home')
        await message.reply_text('توکن ربات بله با موفقیت ثبت شد.', reply_markup=build_back_keyboard())
    else:
        await model_async.set_state(user_id, 'home')
        await message.reply_text(
            'توکن بات بله معتبر نمی باشد لطفا دوباره تلاش کنید.',
            reply_markup=build_back_keyboard()
        )


async def send_support_message(message: Message, user_id: int):
    import config
    from db.redis_client import redis_get_state

    limit = config.SUPPORT_MESSAGE_LIMIT
    count = await model_async.get_support_message_count(user_id)

    if limit and count >= limit:
        await model_async.set_state(user_id, 'home')
        await message.reply_text(
            '⚠️ شما به سقف مجاز ارسال پیام/تیکت در انتظار پاسخ رسیده‌اید. لطفاً منتظر پاسخ ادمین بمانید.',
            reply_markup=build_back_keyboard()
        )
        return

    # Extract selected ticket category ID from state
    cat_id = 1
    state = await model_async.get_state(user_id)
    if state.startswith("ticket_waiting_msg_"):
        try:
            cat_id = int(state.split("_")[-1])
        except ValueError:
            cat_id = 1

    cat = await model_async.get_ticket_category(cat_id)
    cat_title = cat["title"] if cat else "پشتیبانی عمومی"
    is_anon = 1 if (cat and cat.get("is_anonymous")) else 0

    user = message.from_user
    username_line = f"@{user.username}" if user.username else "ندارد"
    full_name = f"{(user.first_name or '')} {(user.last_name or '')}".strip() or "کاربر"
    msg_content = message.text or message.caption or "(فایل/مدیا)"

    ticket_id = await model_async.create_user_ticket(
        telegram_id=user_id,
        user_name=full_name,
        category_id=cat_id,
        message=msg_content,
        subject=cat_title,
        is_anonymous=is_anon
    )

    await model_async.increment_support_message_count(user_id)
    await model_async.set_state(user_id, 'home')
    await message.reply_text(
        f"✅ تیکت شما با شناسه **#{ticket_id}** در بخش **{cat_title}** با موفقیت ثبت شد.\n"
        "به محض بررسی توسط تیم پشتیبانی، پاسخ برای شما ارسال خواهد شد.",
        reply_markup=build_back_keyboard()
    )
