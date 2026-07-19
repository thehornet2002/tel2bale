from pyrogram.types import Message

from db import model_async


async def handle_support_reply(message: Message) -> None:
    """
    وقتی ادمین در گروه پشتیبانی روی پیام حاوی مشخصات کاربر ریپلای می‌زند،
    پاسخ او برای همان کاربر ارسال، پیام answered و محدودیت او ریست می‌شود.
    """
    if not message.from_user or not await model_async.check_admin(message.from_user.id):
        return

    replied_id = message.reply_to_message.id
    telegram_id = await model_async.get_telegram_id_by_group_message(replied_id)
    if telegram_id is None:
        return

    try:
        await message.copy(telegram_id)
    except Exception:
        await message.reply_text("❌ ارسال پاسخ به کاربر ناموفق بود (احتمالا کاربر ربات را بلاک کرده است).")
        return

    await model_async.mark_support_message_answered(replied_id)
    await model_async.reset_support_message_count(telegram_id)
    await message.reply_text("✅ پاسخ شما برای کاربر ارسال شد.")
