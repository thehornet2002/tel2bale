"""
Administrative handlers for ticketing system, categories, and surveys.
"""
from pyrogram.types import Message, CallbackQuery
from db import model_async
from handlers.handler_helpers.callback_helpers.decorators import admin_required
from utils.keyboards import (
    build_admin_categories_manage_keyboard,
    build_admin_polls_manage_keyboard,
    build_admin_poll_detail_keyboard,
    build_admin_tickets_list_keyboard,
    build_admin_ticket_view_keyboard,
    build_back_keyboard,
    build_back_management_keyboard,
    build_cancel_reply_keyboard,
    build_captcha_settings_keyboard,
    build_category_anonymity_keyboard,
    build_category_delete_keyboard,
)


@admin_required
async def admin_manage_categories(message: Message, user_id: int) -> None:
    cats = await model_async.count_tickets_by_category()
    text = (
        "🗂 **مدیریت عناوین و موضوعات تیکتینگ:**\n\n"
        "برای حذف، تغییر وضعیت یا افزودن موضوع جدید، از دکمه‌های زیر استفاده کنید:"
    )
    kb = build_admin_categories_manage_keyboard(cats)
    if getattr(message, "outgoing", False) or getattr(getattr(message, "from_user", None), "is_self", False):
        try:
            await message.edit_text(text, reply_markup=kb)
            return
        except Exception:
            pass
    await message.reply_text(text, reply_markup=kb)


@admin_required
async def admin_start_add_category(message: Message, user_id: int) -> None:
    await model_async.set_state(user_id, "waiting_category_title")
    await message.reply_text(
        "➕ **افزودن موضوع تیکت جدید:**\n\n"
        "لطفاً عنوان مورد نظر را ارسال فرمایید:\n*(مثال: پشتیبانی مالی، گزارش باگ)*",
        reply_markup=build_cancel_reply_keyboard("🔙 انصراف و بازگشت به مدیریت")
    )


@admin_required
async def admin_category_detail_view(message: Message, user_id: int, cat_id: int) -> None:
    cat = await model_async.get_ticket_category(cat_id)
    if not cat:
        await message.reply_text("موضوع یافت نشد.", reply_markup=build_back_management_keyboard())
        return

    text = (
        f"📂 **مدیریت موضوع:** «{cat['title']}»\n"
        f"وضعیت: {'🟢 فعال' if cat['is_active'] else '🔴 آرشیو'}\n"
        f"حالت: {'🕶 ناشناس' if cat.get('is_anonymous') else '👤 عادی'}\n\n"
        "شیوه مدیریت یا حذف را انتخاب کنید:"
    )
    kb = build_category_delete_keyboard(cat_id)
    if getattr(message, "outgoing", False) or getattr(getattr(message, "from_user", None), "is_self", False):
        try:
            await message.edit_text(text, reply_markup=kb)
            return
        except Exception:
            pass
    await message.reply_text(text, reply_markup=kb)


@admin_required
async def admin_delete_category_action(message: Message, user_id: int, cat_id: int, hard: bool = False) -> None:
    _, del_cnt = await model_async.delete_ticket_category(cat_id, delete_tickets=hard)
    msg = f"⚠️ موضوع و تمامی {del_cnt} تیکت آن به طور کامل پاک شدند." if hard else "✅ موضوع غیرفعال و به آرشیو منتقل شد (تیکت‌ها باقی ماندند)."
    await message.reply_text(msg)
    await admin_manage_categories(message, user_id)


@admin_required
async def admin_polls_management(message: Message, user_id: int) -> None:
    polls = await model_async.get_all_polls_admin()
    text = (
        f"📊 **مدیریت نظرسنجی‌ها**\n\n"
        f"تعداد کل نظرسنجی‌ها: {len(polls)}\n"
        "جهت مشاهده وضعیت، بستن/بازکردن یا حذف، روی نظرسنجی مورد نظر بزنید:"
    )
    kb = build_admin_polls_manage_keyboard(polls)
    if getattr(message, "outgoing", False) or getattr(getattr(message, "from_user", None), "is_self", False):
        try:
            await message.edit_text(text, reply_markup=kb)
            return
        except Exception:
            pass
    await message.reply_text(text, reply_markup=kb)


@admin_required
async def admin_poll_detail_view(message: Message, user_id: int, poll_id: int) -> None:
    poll = await model_async.get_poll(poll_id)
    if not poll:
        await message.reply_text("نظرسنجی یافت نشد.", reply_markup=build_back_management_keyboard())
        return

    status_txt = "🟢 فعال" if poll.get("is_active") else "🔴 بسته"
    text = (
        f"📊 **جزئیات نظرسنجی #{poll['id']}**\n\n"
        f"❓ سوال: {poll['question']}\n"
        f"وضعیت: {status_txt}\n"
        f"تاریخ ایجاد: {poll.get('created_at')}\n"
    )
    kb = build_admin_poll_detail_keyboard(poll)
    if getattr(message, "outgoing", False) or getattr(getattr(message, "from_user", None), "is_self", False):
        try:
            await message.edit_text(text, reply_markup=kb)
            return
        except Exception:
            pass
    await message.reply_text(text, reply_markup=kb)


@admin_required
async def admin_toggle_poll(message: Message, user_id: int, poll_id: int) -> None:
    await model_async.toggle_poll_status(poll_id)
    await admin_poll_detail_view(message, user_id, poll_id)


@admin_required
async def admin_delete_poll(message: Message, user_id: int, poll_id: int) -> None:
    await model_async.delete_poll(poll_id)
    await admin_polls_management(message, user_id)


@admin_required
async def admin_tickets_menu(message: Message, user_id: int, status: str = "خوانده نشده", page: int = 1) -> None:
    tickets, total, total_pages = await model_async.get_tickets_paged(status=status, page=page, per_page=8)
    counts = await model_async.get_ticket_status_counts()
    text = (
        f"🎫 **سامانه مدیریت تیکت‌های پشتیبانی**\n\n"
        f"تعداد کل تیکت‌ها: {counts.get('همه', 0)} | در انتظار پاسخ: {counts.get('خوانده نشده', 0)}\n"
        f"صفحه {page} از {total_pages}\n"
        "جهت مشاهده جزئیات و پاسخ، روی هر تیکت کلیک کنید:"
    )
    kb = build_admin_tickets_list_keyboard(tickets, status, page, total_pages, counts)
    if getattr(message, "outgoing", False) or getattr(getattr(message, "from_user", None), "is_self", False):
        try:
            await message.edit_text(text, reply_markup=kb)
            return
        except Exception:
            pass
    await message.reply_text(text, reply_markup=kb)


@admin_required
async def admin_view_single_ticket(message: Message, user_id: int, ticket_id: int, status: str = "خوانده نشده", page: int = 1) -> None:
    ticket = await model_async.get_ticket(ticket_id)
    if not ticket:
        await message.reply_text("❌ تیکت یافت نشد.", reply_markup=build_back_management_keyboard())
        return

    status_icon = "🟢" if ticket["status"] == "پاسخ داده شده" else "🟡"
    sender_str = "🕶 کاربر ناشناس" if ticket.get("is_anonymous") else f"**{ticket.get('user_name') or 'کاربر'}** (`{ticket['telegram_id']}`)"
    text = (
        f"🎫 **جزئیات تیکت #{ticket['id']}**\n\n"
        f"📁 موضوع: **{ticket.get('category_title') or 'عمومی'}**\n"
        f"👤 فرستنده: {sender_str}\n"
        f"📅 تاریخ ایجاد: {ticket['created_at']}\n"
        f"📊 وضعیت: {status_icon} **{ticket['status']}**\n\n"
        f"💬 **متن تیکت:**\n{ticket['message']}\n\n"
    )
    if ticket.get("reply"):
        text += f"📨 **پاسخ قبلی ثبت‌شده:**\n{ticket['reply']}\n\n"

    kb = build_admin_ticket_view_keyboard(ticket_id, status, page)
    if getattr(message, "outgoing", False) or getattr(getattr(message, "from_user", None), "is_self", False):
        try:
            await message.edit_text(text, reply_markup=kb)
            return
        except Exception:
            pass
    await message.reply_text(text, reply_markup=kb)


@admin_required
async def admin_start_poll_creation(message: Message, user_id: int) -> None:
    await model_async.set_state(user_id, "enter_poll_data")
    prompt = (
        "📊 **ایجاد نظرسنجی جدید برای کاربران:**\n\n"
        "لطفاً صورت سوال و گزینه‌ها را در قالب زیر ارسال کنید (هر گزینه در یک خط جداگانه):\n\n"
        "صورت سوال نظرسنجی\n"
        "گزینه ۱\n"
        "گزینه ۲\n"
        "گزینه ۳\n"
    )
    await message.reply_text(prompt, reply_markup=build_cancel_reply_keyboard("🔙 انصراف و بازگشت به مدیریت"))


@admin_required
async def admin_captcha_settings_view(message: Message, user_id: int) -> None:
    ticket_on = model_async.is_captcha_ticket_enabled()
    poll_on = model_async.is_captcha_poll_enabled()
    file_on = model_async.is_captcha_file_enabled()

    text = (
        "🔐 **تنظیمات سیستم امنیتی کپچا (Captcha)**\n\n"
        "در این بخش می‌توانید وضعیت کپچا را برای بخش‌های مختلف به صورت جداگانه تعیین کنید:\n\n"
        f"• **کپچای تیکت**: {'🟢 فعال' if ticket_on else '🔴 غیرفعال'}\n"
        f"• **کپچای نظرسنجی**: {'🟢 فعال' if poll_on else '🔴 غیرفعال'}\n"
        f"• **کپچای ارسال فایل**: {'🟢 فعال' if file_on else '🔴 غیرفعال'}\n\n"
        "برای تغییر وضعیت روی دکمه مربوطه کلیک کنید:"
    )
    kb = build_captcha_settings_keyboard(ticket_on, poll_on, file_on)
    if getattr(message, "outgoing", False) or getattr(getattr(message, "from_user", None), "is_self", False):
        try:
            await message.edit_text(text, reply_markup=kb)
            return
        except Exception:
            pass
    await message.reply_text(text, reply_markup=kb)


@admin_required
async def admin_toggle_captcha_ticket(message: Message, user_id: int) -> None:
    current = model_async.is_captcha_ticket_enabled()
    await model_async.set_captcha_ticket_enabled(not current)
    await admin_captcha_settings_view(message, user_id)


@admin_required
async def admin_toggle_captcha_poll(message: Message, user_id: int) -> None:
    current = model_async.is_captcha_poll_enabled()
    await model_async.set_captcha_poll_enabled(not current)
    await admin_captcha_settings_view(message, user_id)


@admin_required
async def admin_toggle_captcha_file(message: Message, user_id: int) -> None:
    current = model_async.is_captcha_file_enabled()
    await model_async.set_captcha_file_enabled(not current)
    await admin_captcha_settings_view(message, user_id)
