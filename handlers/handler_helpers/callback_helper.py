from functools import wraps
from pyrogram.types import Message

from config import (
    START_TXT,
    HELP_TXT,
    ADS_CHANNELS,
    ADMIN_IDS,
)

from db.db_sync import DB_NAME

from db.model_async import (
    add_user,
    check_admin,
    get_top_users,
    get_unread_support_message,
    is_user_exist,
    set_state,
    get_bale_id,
    get_access_key,
    get_secret_key,
    get_bale_token
)

from utils.keyboards import (
    build_back_keyboard,
    build_back_management_keyboard,
    build_management_keyboard,
    build_start_keyboard,
    support_keyboard,
    yes_or_no_bale_id,
    yes_or_no_set_arvan,
    yes_or_no_set_bot_token
)


# ==================================================
# Decorators
# ==================================================

def admin_required(func):
    @wraps(func)
    async def wrapper(message: Message, user_id: int, *args, **kwargs):
        if not await check_admin(user_id):
            return

        return await func(
            message,
            user_id,
            *args,
            **kwargs
        )

    return wrapper


# ==================================================
# Public
# ==================================================

async def start(
    message: Message,
    user_id: int
) -> None:

    if not await is_user_exist(user_id):
        await add_user(user_id)

    await message.edit_text(
        START_TXT,
        reply_markup=build_start_keyboard(
            await check_admin(user_id)
        )
    )


async def back(
    message: Message,
    user_id: int
) -> None:

    await set_state(user_id, "home")

    await message.edit_text(
        START_TXT,
        reply_markup=build_start_keyboard(
            await check_admin(user_id)
        )
    )


async def help(
    message: Message,
    user_id: int
) -> None:

    await set_state(user_id, "home")

    await message.edit_text(
        HELP_TXT,
        reply_markup=build_start_keyboard(
            await check_admin(user_id)
        )
    )


async def set_bale_id(
    message:Message,
    user_id:int
) -> None:
    try:
        bale_id = await get_bale_id(user_id)
        if bale_id != None:
            message_txt = 'شما قبلا ID عددی بله خود را ذخیره کرده اید.\n'+ 'آیا می خواهید دوباره آن را تنظیم کنید؟'
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
        await message.reply_text(
            text ='مشکل در ارسال:' + str(e)
        )


async def reset_bale_id(
        message:Message,
        user_id:int
) -> None:
    await set_state(user_id, 'enter_bale_id')
    await message.edit_text(
        text='لطفا ID عددی بله خود را وارد کنید:',
        reply_markup=build_back_keyboard()
    )


async def set_arvan(
        message:Message,
        user_id:int
):
    access_key = await get_access_key(user_id)
    secret_key = await get_secret_key(user_id)
    if secret_key == None or access_key == None:
        await set_state(user_id, 'set_access_key_arvan')
        await message.edit_text(
            text='لطفا Access Key موجود در Arvan Storage را وارد کنید.',
            reply_markup=build_back_keyboard()
        )
        return
    else:
        await message.edit_text(
            text='شما قبلا این مقدار تنظیم نموده اید آیا می خواهید آن را دوباره تنظیم کنید؟',
            reply_markup=yes_or_no_set_arvan()
        )


async def reset_access_key_arvan(
        message:Message,
        user_id:int
):
    await set_state(user_id, 'set_access_key_arvan')
    await message.edit_text(
        text='لطفا Access Key موجود در Arvan Storage را وارد کنید.',
        reply_markup=build_back_keyboard()
    )
    return
    

async def set_bale_bot_token(
        message:Message,
        user_id:int
):
    token_bot = await get_bale_token(user_id)
    if token_bot == None:
        await set_state(user_id,'set_bale_token_bot')
        await message.edit_text(
            text='لطفا توکن ربات بله را وارد کنید.',
            reply_markup=build_back_keyboard()
        )
    else:
        await message.edit_text(
            text='شما قبلا توکن ربات را وارد کرده اید، آیا می خواهید آن را تغییر دهید؟',
            reply_markup=yes_or_no_set_bot_token()
        )

async def reset_bot_token(
        message:Message,
        uesr_id:int
):
    await set_state(uesr_id, 'set_bale_token_bot')
    await message.edit_text(
        text='لطفا توکن ربات بله خود را وارد کنید.',
        reply_markup=build_back_keyboard()
    )

async def send_support_message(
    message: Message,
    user_id: int
) -> None:

    await set_state(
        user_id,
        "send_support_message"
    )

    await message.edit_text(
        "لطفاً پیام خود را وارد کنید:",
        reply_markup=build_back_keyboard()
    )


# ==================================================
# Admin Panel
# ==================================================

@admin_required
async def management(
    message: Message,
    user_id: int
) -> None:

    await set_state(user_id, "management")

    await message.edit_text(
        "ادمین عزیز به پنل مدیریت ربات خوش آمدید",
        reply_markup=build_management_keyboard()
    )


@admin_required
async def back_to_management(
    message: Message,
    user_id: int
) -> None:

    await set_state(user_id, "management")

    await message.edit_text(
        "ادمین عزیز به پنل مدیریت ربات خوش آمدید",
        reply_markup=build_management_keyboard()
    )


@admin_required
async def get_db(
    message: Message,
    user_id: int
) -> None:

    await message.reply_document(
        document=DB_NAME
    )

    await message.reply_text(
        "ادمین عزیز به پنل مدیریت ربات خوش آمدید",
        reply_markup=build_management_keyboard()
    )


@admin_required
async def ban_bale(
    message: Message,
    user_id: int
) -> None:

    await set_state(
        user_id,
        "enter_bale_ban"
    )

    await message.edit_text(
        "لطفا ID عددی بله فرد موردنظر را وارد کنید.",
        reply_markup=build_back_management_keyboard()
    )


@admin_required
async def unban_bale(
    message: Message,
    user_id: int
) -> None:

    await set_state(
        user_id,
        "enter_bale_unban"
    )

    await message.edit_text(
        "لطفا ID عددی بله فرد موردنظر را وارد کنید.",
        reply_markup=build_back_management_keyboard()
    )


@admin_required
async def ban_telegram(
    message: Message,
    user_id: int
) -> None:

    await set_state(
        user_id,
        "enter_telegram_ban"
    )

    await message.edit_text(
        "لطفا ID عددی تلگرام فرد موردنظر را وارد کنید.",
        reply_markup=build_back_management_keyboard()
    )


@admin_required
async def unban_telegram(
    message: Message,
    user_id: int
) -> None:

    await set_state(
        user_id,
        "enter_telegram_unban"
    )

    await message.edit_text(
        "لطفا ID عددی تلگرام فرد موردنظر را وارد کنید.",
        reply_markup=build_back_management_keyboard()
    )


@admin_required
async def show_10_high(
    message: Message,
    user_id: int
) -> None:

    users = await get_top_users()

    lines = [
        "Telegram ID | Bale ID | Downloaded Volume"
    ]

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
async def set_join_ads(
    message: Message,
    user_id: int
) -> None:

    await set_state(
        user_id,
        "enter_join_ads_channel"
    )

    await message.edit_text(
        "لطفا ID کانال را وارد کنید (مثال: tel2bale)",
        reply_markup=build_back_management_keyboard()
    )


@admin_required
async def delete_join_ads(
    message: Message,
    user_id: int
) -> None:

    await set_state(
        user_id,
        "enter_delete_join_ads"
    )

    channels = "\n".join(ADS_CHANNELS)

    await message.edit_text(
        f"کانال موردنظر را انتخاب کنید:\n\n{channels}",
        reply_markup=build_back_management_keyboard()
    )


@admin_required
async def send_ads_message(
    message: Message,
    user_id: int
) -> None:

    await set_state(
        user_id,
        "enter_ads_message"
    )

    await message.edit_text(
        "پیام همگانی را وارد کنید:",
        reply_markup=build_back_management_keyboard()
    )


@admin_required
async def send_message(
    message: Message,
    user_id: int
) -> None:

    await set_state(
        user_id,
        "send_message_chat_id"
    )

    await message.edit_text(
        "ID عددی تلگرام کاربر را وارد کنید:",
        reply_markup=build_back_management_keyboard()
    )


@admin_required
async def add_admin(
    message: Message,
    user_id: int
) -> None:

    await set_state(
        user_id,
        "add_admin_send_id"
    )

    await message.edit_text(
        "ID عددی تلگرام ادمین جدید را وارد کنید:"
    )


@admin_required
async def delete_admin(
    message: Message,
    user_id: int
) -> None:

    await set_state(
        user_id,
        "delete_admin_send_id"
    )

    lines = [
        "ID ادمینی که می‌خواهید حذف کنید:"
    ]

    for index, admin_id in enumerate(ADMIN_IDS):
        lines.append(
            f"{index} - {admin_id}"
        )

    await message.edit_text(
        "\n".join(lines),
        reply_markup=build_back_management_keyboard()
    )


@admin_required
async def set_profile_photo(
    message: Message,
    user_id: int
) -> None:

    await set_state(
        user_id,
        "set_profile_photo_send_photo"
    )

    await message.edit_text(
        "لطفا تصویر پروفایل را ارسال کنید.",
        reply_markup=build_back_management_keyboard()
    )


@admin_required
async def set_limit_all(
    message: Message,
    user_id: int
) -> None:

    await set_state(
        user_id,
        "set_limit_all_send_volume"
    )

    await message.edit_text(
        "محدودیت دانلود (GB) را وارد کنید:",
        reply_markup=build_back_management_keyboard()
    )


@admin_required
async def set_limit(
    message: Message,
    user_id: int
) -> None:

    await set_state(
        user_id,
        "set_limit_send_id"
    )

    await message.edit_text(
        "ID عددی کاربر را وارد کنید:",
        reply_markup=build_back_management_keyboard()
    )


@admin_required
async def show_support_messages(
    message: Message,
    user_id: int
) -> None:

    support_message = await get_unread_support_message()

    if support_message is None:
        await message.reply_text(
            "پیامی وجود ندارد.",
            reply_markup=build_back_management_keyboard()
        )
        return

    await message.reply_text(
        f"پیام ارسال شده از:\n"
        f"{support_message['tg_id']}\n\n"
        f"{support_message['message_text']}",
        reply_markup=support_keyboard()
    )