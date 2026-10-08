from re import compile

from pyrogram import Client, filters
from pyrogram.types import Message, ReplyKeyboardRemove

from db.model_async import (
    check_admin,
    check_ban,
    get_state,
    is_user_exist,
    is_user_whitelisted,
    set_state,
)

from handlers.handler_helpers.callback_helpers.admin.admin_mgmt_handler import (
    add_admin,
    delete_admin,
)
from handlers.handler_helpers.callback_helpers.admin.ads_handler import (
    delete_join_ads,
    set_join_ads,
)
from handlers.handler_helpers.callback_helpers.admin.ban_handler import (
    ban_bale,
    ban_telegram,
    unban_bale,
    unban_telegram,
)
from handlers.handler_helpers.callback_helpers.admin.core_handler import (
    change_donation_link as change_donation_link_cb,
    get_db,
    management,
    set_max_active_users as set_max_active_users_cb,
    set_max_users as set_max_users_cb,
    show_10_high,
)
from handlers.handler_helpers.callback_helpers.admin.limit_handler import (
    set_limit,
    set_limit_all,
)
from handlers.handler_helpers.callback_helpers.admin.messaging_handler import (
    send_ads_message,
    send_message,
)
from handlers.handler_helpers.callback_helpers.admin.whitelist_handler import (
    add_whitelist,
    list_whitelist,
    manage_whitelist,
    remove_whitelist,
    toggle_whitelist,
)
from handlers.handler_helpers.message_helpers.admin_handler import (
    add_admin_send_id,
    add_whitelist_send_id,
    change_donation_link,
    delete_admin_send_id,
    enter_bale_ban,
    enter_bale_unban,
    enter_category_title_handler,
    enter_poll_data_handler,
    enter_telegram_ban,
    enter_telegram_unban,
    enter_ticket_reply_handler,
    remove_whitelist_send_id,
    set_max_active_users_send_value,
    set_max_users_send_value,
)
from handlers.handler_helpers.callback_helpers.admin.ticket_mgmt_handler import (
    admin_captcha_settings_view,
    admin_manage_categories,
    admin_polls_management,
    admin_start_add_category,
    admin_start_poll_creation,
    admin_tickets_menu,
)
from handlers.handler_helpers.message_helpers.ads_handler import (
    enter_delete_join_ads,
    enter_join_ads_channel,
)
from handlers.handler_helpers.message_helpers.forward_handler import forward
from handlers.handler_helpers.message_helpers.limit_handler import (
    set_limit_all_send_volume,
    set_limit_send_id,
    set_limit_set_limit,
)
from handlers.handler_helpers.message_helpers.messaging_handler import (
    enter_ads_message,
    send_message_chat_id,
    send_message_send_message,
)
from handlers.handler_helpers.message_helpers.s3_handler import (
    set_s3_access_key,
    set_s3_endpoint,
    set_s3_secret_key,
)
from handlers.handler_helpers.message_helpers.user_handler import (
    enter_bale_id,
    send_support_message,
    set_bale_token_bot,
)
from utils.filters import join_filter
from utils.keyboards import (
    build_admin_home_reply_keyboard,
    build_management_keyboard,
    build_start_keyboard,
)
import config

SEND_MESSAGE_RE = compile(r"^send_message_(\d{1,20})$")
SET_LIMIT_RE = compile(r"^set_limit_(\d{1,20})$")

STATE_HANDLERS = {
    "home": forward,
    "enter_bale_id": enter_bale_id,
    "send_support_message": send_support_message,
    "set_bale_token_bot": set_bale_token_bot,
    "enter_bale_ban": enter_bale_ban,
    "enter_bale_unban": enter_bale_unban,
    "enter_telegram_ban": enter_telegram_ban,
    "enter_telegram_unban": enter_telegram_unban,
    "enter_join_ads_channel": enter_join_ads_channel,
    "enter_delete_join_ads": enter_delete_join_ads,
    "enter_ads_message": enter_ads_message,
    "send_message_chat_id": send_message_chat_id,
    "add_admin_send_id": add_admin_send_id,
    "delete_admin_send_id": delete_admin_send_id,
    "set_limit_all_send_volume": set_limit_all_send_volume,
    "set_limit_send_id": set_limit_send_id,
    "change_donation_link": change_donation_link,
    "enter_poll_data": enter_poll_data_handler,
    "waiting_category_title": enter_category_title_handler,
    "set_max_users": set_max_users_send_value,
    "set_max_active_users": set_max_active_users_send_value,
    "add_whitelist_send_id": add_whitelist_send_id,
    "remove_whitelist_send_id": remove_whitelist_send_id,
    # s3
    "set_s3_access_key": set_s3_access_key,
    "set_s3_secret_key": set_s3_secret_key,
    "set_s3_endpoint": set_s3_endpoint,
}

CANCEL_WORDS = {
    "🔙 بازگشت",
    "بازگشت",
    "🔙 انصراف",
    "انصراف",
    "🔙 انصراف و بازگشت",
    "🔙 انصراف و بازگشت به مدیریت",
    "/cancel",
}


@Client.on_message(
    filters.private
    & ~filters.command("start")
    & ~filters.command("help")
    & ~filters.command("admin")
    & ~filters.command("panel")
    & join_filter
)
async def handle_input(client: Client, message: Message) -> None:
    user_id = message.from_user.id

    if not is_user_whitelisted(user_id):
        await message.reply_text("⛔ این ربات در حالت لیست سفید (Whitelist) قرار دارد و حساب شما مجاز نیست.")
        return

    if not await is_user_exist(user_id):
        return

    if await check_ban(user_id):
        return

    text = (message.text or "").strip()
    state = await get_state(user_id)

    # بررسی لغو عملیات / بازگشت
    if text in CANCEL_WORDS:
        is_admin = await check_admin(user_id)
        if is_admin:
            await set_state(user_id, "management")
            await message.reply_text(
                "عملیات لغو شد. به پنل مدیریت بازگشتید.",
                reply_markup=build_management_keyboard()
            )
            return

        await set_state(user_id, "home")
        await message.reply_text(
            "عملیات لغو شد.",
            reply_markup=ReplyKeyboardRemove()
        )
        return

    # پردازش دکمه‌های پنل مدیریت (ReplyKeyboardMarkup) منحصراً برای ادمین
    is_admin = await check_admin(user_id)
    if is_admin and text:
        admin_actions = {
            "⚙️ پنل مدیریت": management,
            "🔙 بازگشت به مدیریت": management,
            "💾 دریافت دیتابیس": get_db,
            "📊 ۱۰ کاربر پرمصرف": show_10_high,
            "🚫 بن تلگرام": ban_telegram,
            "✅ آنبن تلگرام": unban_telegram,
            "🚫 بن بله": ban_bale,
            "✅ آنبن بله": unban_bale,
            "➕ افزودن ادمین": add_admin,
            "➖ حذف ادمین": delete_admin,
            "🌐 سقف حجم همگانی": set_limit_all,
            "👤 سقف حجم کاربر": set_limit,
            "👥 سقف کل کاربران": set_max_users_cb,
            "🟢 سقف کاربران فعال": set_max_active_users_cb,
            "📢 ارسال تبلیغات": send_ads_message,
            "✉️ ارسال پیام به کاربر": send_message,
            "🔗 ایجاد Join اجباری": set_join_ads,
            "❌ حذف Join اجباری": delete_join_ads,
            "🎫 تیکت‌های پشتیبانی": admin_tickets_menu,
            "🗂 موضوعات تیکت": admin_manage_categories,
            "📊 مدیریت نظرسنجی‌ها": admin_polls_management,
            "➕ نظرسنجی جدید": admin_start_poll_creation,
            "🔐 تنظیمات کپچا": admin_captcha_settings_view,
            "☕ تغییر لینک دونیت": change_donation_link_cb,
            "⚙️ مدیریت لیست سفید": manage_whitelist,
            "➕ افزودن به لیست سفید": add_whitelist,
            "➖ حذف از لیست سفید": remove_whitelist,
            "📋 مشاهده اعضای لیست سفید": list_whitelist,
        }
        if text in admin_actions:
            await admin_actions[text](message, user_id)
            return

        if text in ("🟢 فعال‌سازی لیست سفید", "🔴 غیرفعال‌سازی لیست سفید", "🔄 تغییر وضعیت لیست سفید"):
            await toggle_whitelist(message, user_id)
            return

        if text in ("🔙 خروج از مدیریت", "📱 منوی کاربری"):
            await set_state(user_id, "home")
            await message.reply_text(
                config.START_TXT,
                reply_markup=build_start_keyboard()
            )
            await message.reply_text(
                "⚙️ برای دسترسی مجدد به پنل مدیریت از دکمه زیر استفاده کنید:",
                reply_markup=build_admin_home_reply_keyboard()
            )
            return

    handler = STATE_HANDLERS.get(state)
    if handler:
        await handler(message, user_id)
        return

    if state.startswith("captcha_verify_"):
        from handlers.handler_helpers.message_helpers.captcha_handler import (
            verify_captcha_answer,
            get_pending_file_message,
            clear_pending_file_message,
        )
        from utils.keyboards import build_back_keyboard
        passed = await verify_captcha_answer(message, user_id, message.text or "")
        if passed:
            tag = state.replace("captcha_verify_", "")
            if tag.startswith("ticket_"):
                cat_id = tag.replace("ticket_", "")
                await set_state(user_id, f"ticket_waiting_msg_{cat_id}")
                await message.reply_text(
                    "✅ هویت شما با موفقیت تایید شد.\n\n"
                    "✍️ اکنون لطفاً متن پیام یا فایل تیکت خود را ارسال نمایید:",
                    reply_markup=build_back_keyboard()
                )
            elif tag.startswith("poll_"):
                try:
                    _, poll_id_s, opt_idx_s = tag.split("_")
                    await model_async.record_poll_vote(int(poll_id_s), user_id, int(opt_idx_s))
                    await set_state(user_id, "home")
                    await message.reply_text("✅ کد امنیتی تایید شد و رأی شما با موفقیت ثبت گردید.")
                except Exception:
                    await set_state(user_id, "home")
            elif tag == "file_forward":
                pending_file = get_pending_file_message(user_id)
                clear_pending_file_message(user_id)
                await set_state(user_id, "home")
                if pending_file:
                    await message.reply_text("✅ کد امنیتی تایید شد. در حال ارسال فایل به بله...")
                    await forward(pending_file, user_id, bypass_captcha=True)
                else:
                    await message.reply_text("✅ کد امنیتی تایید شد. لطفاً فایل خود را ارسال کنید.")
            else:
                await set_state(user_id, f"ticket_waiting_msg_{tag}")
                await message.reply_text(
                    "✅ هویت شما با موفقیت تایید شد.\n\n"
                    "✍️ اکنون لطفاً متن پیام یا فایل تیکت خود را ارسال نمایید:",
                    reply_markup=build_back_keyboard()
                )
        return

    if state.startswith("ticket_waiting_msg_"):
        await send_support_message(message, user_id)
        return

    if state.startswith("ticket_reply_"):
        await enter_ticket_reply_handler(message, user_id)
        return

    if SEND_MESSAGE_RE.match(state):
        await send_message_send_message(message, user_id)
        return

    if SET_LIMIT_RE.match(state):
        await set_limit_set_limit(message, user_id)
        return
