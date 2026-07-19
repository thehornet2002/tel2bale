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
    verify_state = await bale_bot.verify_token(message.text)
    if verify_state:
        await model_async.set_bale_token(user_id, message.text)
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

    limit = config.SUPPORT_MESSAGE_LIMIT
    count = await model_async.get_support_message_count(user_id)

    if limit and count >= limit:
        await model_async.set_state(user_id, 'home')
        await message.reply_text(
            'شما به سقف مجاز ارسال پیام به پشتیبانی رسیده اید. لطفا منتظر پاسخ ادمین بمانید.',
            reply_markup=build_back_keyboard()
        )
        return

    user = message.from_user
    username_line = f"یوزرنیم: @{user.username}" if user.username else "یوزرنیم: ندارد"
    full_name = f"{(user.first_name or '')} {(user.last_name or '')}".strip()
    info_text = (
        "\U0001F4E9 پیام جدید پشتیبانی\n"
        f"شناسه تلگرام: {user.id}\n"
        f"نام: {full_name}\n"
        f"{username_line}"
    )

    try:
        info_msg = await message._client.send_message(int(config.SUPPORT_GROUP), info_text)
        await message.copy(int(config.SUPPORT_GROUP), reply_to_message_id=info_msg.id)
    except Exception:
        await model_async.set_state(user_id, 'home')
        await message.reply_text(
            'ارسال پیام به پشتیبانی با خطا مواجه شد، لطفا بعدا تلاش کنید.',
            reply_markup=build_back_keyboard()
        )
        return

    await model_async.save_support_message(user_id, info_msg.id)
    await model_async.increment_support_message_count(user_id)
    await model_async.set_state(user_id, 'home')
    await message.reply_text('پیام شما با موفقیت برای پشتیبانی ارسال شد.', reply_markup=build_back_keyboard())
