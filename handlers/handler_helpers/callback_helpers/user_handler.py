from pyrogram.types import Message

from db.model_async import (
    get_access_key,
    get_bale_id,
    get_bale_token,
    get_s3_endpoint,
    get_secret_key,
    set_state,
)
from utils.keyboards import (
    build_back_keyboard,
    yes_or_no_bale_id,
    yes_or_no_set_bot_token,
    yes_or_no_set_s3,
)


async def set_bale_id(message: Message, user_id: int) -> None:
    try:
        bale_id = await get_bale_id(user_id)
        if bale_id is not None:
            message_txt = (
                'شما قبلا ID عددی بله خود را ذخیره کرده اید.\n'
                'آیا می خواهید دوباره آن را تنظیم کنید؟'
            )
            await message.reply_text(
                text=message_txt,
                reply_markup=yes_or_no_bale_id()
            )
        else:
            await set_state(user_id, 'enter_bale_id')
            await message.edit_text(
                text='لطفا ID عددی بله خود را وارد کنید:',
                reply_markup=build_back_keyboard()
            )
    except Exception as e:
        await message.reply_text(text='مشکل در ارسال:' + str(e))


async def reset_bale_id(message: Message, user_id: int) -> None:
    await set_state(user_id, 'enter_bale_id')
    await message.edit_text(
        text='لطفا ID عددی بله خود را وارد کنید:',
        reply_markup=build_back_keyboard()
    )


async def set_s3(message: Message, user_id: int) -> None:
    access_key = await get_access_key(user_id)
    secret_key = await get_secret_key(user_id)
    s3_endpoint = await get_s3_endpoint(user_id)

    if access_key is None or secret_key is None or s3_endpoint is None:
        await set_state(user_id, 'set_s3_access_key')
        await message.edit_text(
            text='لطفا Access Key موجود در Arvan Storage را وارد کنید.',
            reply_markup=build_back_keyboard()
        )
        return

    await message.edit_text(
        text='شما قبلا این مقدار تنظیم نموده اید آیا می خواهید آن را دوباره تنظیم کنید؟',
        reply_markup=yes_or_no_set_s3()
    )


async def reset_s3_access_key(message: Message, user_id: int) -> None:
    await set_state(user_id, 'set_s3_access_key')
    await message.edit_text(
        text='لطفا Access Key موجود در Arvan Storage را وارد کنید.',
        reply_markup=build_back_keyboard()
    )


async def set_bale_bot_token(message: Message, user_id: int) -> None:
    token_bot = await get_bale_token(user_id)

    if token_bot is None:
        await set_state(user_id, 'set_bale_token_bot')
        await message.edit_text(
            text='لطفا توکن ربات بله را وارد کنید.',
            reply_markup=build_back_keyboard()
        )
    else:
        await message.edit_text(
            text='شما قبلا توکن ربات را وارد کرده اید، آیا می خواهید آن را تغییر دهید؟',
            reply_markup=yes_or_no_set_bot_token()
        )


async def reset_bot_token(message: Message, user_id: int) -> None:
    await set_state(user_id, 'set_bale_token_bot')
    await message.edit_text(
        text='لطفا توکن ربات بله خود را وارد کنید.',
        reply_markup=build_back_keyboard()
    )


async def send_support_message(message: Message, user_id: int) -> None:
    await set_state(user_id, "send_support_message")
    await message.edit_text(
        "لطفاً پیام خود را وارد کنید:",
        reply_markup=build_back_keyboard()
    )