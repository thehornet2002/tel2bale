from pyrogram.types import Message

from db.model_async import (
    get_access_key,
    get_bale_id,
    get_bale_token,
    get_s3_endpoint,
    get_secret_key,
    get_ticket,
    get_ticket_categories,
    get_user_tickets,
    set_state,
)
from utils.keyboards import (
    build_back_keyboard,
    build_ticket_categories_keyboard,
    build_ticket_detail_keyboard,
    build_user_tickets_keyboard,
    yes_or_no_bale_id,
    yes_or_no_set_bot_token,
    yes_or_no_set_s3,
)


async def _send_or_edit(message: Message, text: str, reply_markup=None):
    if getattr(message, "outgoing", False) or getattr(getattr(message, "from_user", None), "is_self", False):
        try:
            return await message.edit_text(text=text, reply_markup=reply_markup)
        except Exception:
            pass
    return await message.reply_text(text=text, reply_markup=reply_markup)


async def set_bale_id(message: Message, user_id: int) -> None:
    try:
        bale_id = await get_bale_id(user_id)
        if bale_id is not None:
            message_txt = (
                'شما قبلا ID عددی بله خود را ذخیره کرده اید.\n'
                'آیا می خواهید دوباره آن را تنظیم کنید؟'
            )
            await _send_or_edit(
                message=message,
                text=message_txt,
                reply_markup=yes_or_no_bale_id()
            )
        else:
            await set_state(user_id, 'enter_bale_id')
            await _send_or_edit(
                message=message,
                text='لطفا ID عددی بله خود را وارد کنید:',
                reply_markup=build_back_keyboard()
            )
    except Exception as e:
        await message.reply_text(text='مشکل در ارسال:' + str(e))


async def reset_bale_id(message: Message, user_id: int) -> None:
    await set_state(user_id, 'enter_bale_id')
    await _send_or_edit(
        message=message,
        text='لطفا ID عددی بله خود را وارد کنید:',
        reply_markup=build_back_keyboard()
    )


async def set_s3(message: Message, user_id: int) -> None:
    access_key = await get_access_key(user_id)
    secret_key = await get_secret_key(user_id)
    s3_endpoint = await get_s3_endpoint(user_id)

    if access_key is None or secret_key is None or s3_endpoint is None:
        await set_state(user_id, 'set_s3_access_key')
        await _send_or_edit(
            message=message,
            text='لطفا Access Key موجود در Arvan Storage را وارد کنید.',
            reply_markup=build_back_keyboard()
        )
        return

    await _send_or_edit(
        message=message,
        text='شما قبلا این مقدار تنظیم نموده اید آیا می خواهید آن را دوباره تنظیم کنید؟',
        reply_markup=yes_or_no_set_s3()
    )


async def reset_s3_access_key(message: Message, user_id: int) -> None:
    await set_state(user_id, 'set_s3_access_key')
    await _send_or_edit(
        message=message,
        text='لطفا Access Key موجود در Arvan Storage را وارد کنید.',
        reply_markup=build_back_keyboard()
    )


async def set_bale_bot_token(message: Message, user_id: int) -> None:
    token_bot = await get_bale_token(user_id)

    if not token_bot:
        await set_state(user_id, 'set_bale_token_bot')
        await _send_or_edit(
            message=message,
            text='لطفا توکن ربات بله را وارد کنید.',
            reply_markup=build_back_keyboard()
        )
    else:
        await _send_or_edit(
            message=message,
            text='شما قبلا توکن ربات را وارد کرده اید، آیا می خواهید آن را تغییر دهید؟',
            reply_markup=yes_or_no_set_bot_token()
        )


async def reset_bot_token(message: Message, user_id: int) -> None:
    await set_state(user_id, 'set_bale_token_bot')
    await _send_or_edit(
        message=message,
        text='لطفا توکن ربات بله خود را وارد کنید.',
        reply_markup=build_back_keyboard()
    )


async def send_support_message(message: Message, user_id: int) -> None:
    categories = await get_ticket_categories(active_only=True)
    if not categories:
        await set_state(user_id, "send_support_message")
        await _send_or_edit(
            message=message,
            text="لطفاً پیام یا مشکل خود را جهت ارسال به پشتیبانی تایپ کنید:",
            reply_markup=build_back_keyboard()
        )
        return

    await set_state(user_id, "home")
    await _send_or_edit(
        message=message,
        text="📂 لطفاً موضوع تیکت پشتیبانی خود را انتخاب کنید:",
        reply_markup=build_ticket_categories_keyboard(categories)
    )


async def user_my_tickets(message: Message, user_id: int) -> None:
    tickets = await get_user_tickets(user_id)
    if not tickets:
        await _send_or_edit(
            message=message,
            text="📋 شما تاکنون هیچ تیکتی ثبت نکرده‌اید.",
            reply_markup=build_back_keyboard()
        )
        return

    await _send_or_edit(
        message=message,
        text="📋 **لیست تیکت‌های پشتیبانی شما:**\nروی هر تیکت بزنید تا جزئیات و پاسخ آن را مشاهده کنید:",
        reply_markup=build_user_tickets_keyboard(tickets)
    )


async def view_user_ticket(message: Message, user_id: int, ticket_id: int) -> None:
    ticket = await get_ticket(ticket_id)
    if not ticket or ticket["telegram_id"] != user_id:
        await _send_or_edit(
            message=message,
            text="❌ تیکت یافت نشد یا شما اجازه مشاهده آن را ندارید.",
            reply_markup=build_back_keyboard()
        )
        return

    status_icon = "🟢" if ticket["status"] == "پاسخ داده شده" else "🟡"
    reply_text = ticket["reply"] if ticket.get("reply") else "هنوز پاسخی ثبت نشده است."
    text = (
        f"🎫 **تیکت #{ticket['id']}**\n\n"
        f"📁 موضوع: **{ticket.get('category_title') or 'پشتیبانی'}**\n"
        f"📅 تاریخ: {ticket['created_at']}\n"
        f"📊 وضعیت: {status_icon} **{ticket['status']}**\n\n"
        f"💬 **متن تیکت شما:**\n{ticket['message']}\n\n"
        f"📨 **پاسخ پشتیبانی:**\n{reply_text}"
    )
    await _send_or_edit(
        message=message,
        text=text,
        reply_markup=build_ticket_detail_keyboard(ticket_id)
    )


async def user_polls_list(message: Message, user_id: int) -> None:
    from db.model_async import get_all_active_polls
    from utils.keyboards import build_user_polls_list_keyboard

    polls = await get_all_active_polls()
    if not polls:
        await _send_or_edit(
            message=message,
            text="📊 در حال حاضر نظرسنجی فعالی وجود ندارد.",
            reply_markup=build_back_keyboard()
        )
        return

    await _send_or_edit(
        message=message,
        text="📊 **لیست نظرسنجی‌های فعال:**\nلطفاً نظرسنجی مورد نظر خود را انتخاب کنید:",
        reply_markup=build_user_polls_list_keyboard(polls)
    )


async def user_view_poll(message: Message, user_id: int, poll_id: int | None = None) -> None:
    from db.model_async import get_poll, get_active_poll, get_user_poll_vote
    from utils.keyboards import build_poll_voting_keyboard

    poll = await get_poll(poll_id) if poll_id else await get_active_poll()
    if not poll:
        await _send_or_edit(
            message=message,
            text="📊 نظرسنجی مورد نظر یافت نشد یا پایان یافته است.",
            reply_markup=build_back_keyboard()
        )
        return

    user_vote = await get_user_poll_vote(poll["id"], user_id)
    text = (
        f"📊 **نظرسنجی:** {poll.get('title') or ''}\n\n"
        f"❓ **{poll['question']}**\n\n"
        "لطفاً نظر خود را با کلیک روی گزینه‌های زیر ثبت کنید:"
    )
    if user_vote is not None:
        text += f"\n\n*(شما قبلاً به گزینه {user_vote + 1} رأی داده‌اید)*"

    kb = build_poll_voting_keyboard(poll["id"], poll["options"], user_vote)
    await _send_or_edit(message=message, text=text, reply_markup=kb)


async def user_vote_poll_action(message: Message, user_id: int, poll_id: int, option_idx: int) -> None:
    from db.model_async import record_poll_vote
    await record_poll_vote(poll_id, user_id, option_idx)
    await user_view_poll(message, user_id, poll_id=poll_id)


async def user_view_poll_results(message: Message, user_id: int, poll_id: int) -> None:
    from db.model_async import get_poll_results
    res = await get_poll_results(poll_id)
    if not res:
        await _send_or_edit(message=message, text="نظرسنجی یافت نشد.", reply_markup=build_back_keyboard())
        return

    lines = [f"📊 **نتایج نظرسنجی:**\n❓ **{res['question']}**", f"\n👥 کل آرا: **{res['total_votes']}**\n"]
    for r in res.get("results", []):
        bars = "🟩" * int(r["percentage"] // 10) or "▫️"
        lines.append(f"▫️ **{r['option']}**: {r['votes']} رأی ({r['percentage']}%)\n{bars}")

    from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    back_kb = InlineKeyboardMarkup([
        [InlineKeyboardButton(text="🔙 بازگشت به نظرسنجی", callback_data=f"user_select_poll_{poll_id}")],
        [InlineKeyboardButton(text="📊 لیست نظرسنجی‌ها", callback_data="user_polls_list")]
    ])
    await _send_or_edit(
        message=message,
        text="\n".join(lines),
        reply_markup=back_kb
    )