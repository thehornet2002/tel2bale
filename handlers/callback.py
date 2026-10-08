from pyrogram import Client
from pyrogram.types import CallbackQuery

from db.model_async import check_ban, is_user_exist

from handlers.handler_helpers.callback_helpers.navigation_handler import (
    back,
    help,
    start,
)
from handlers.handler_helpers.callback_helpers.user_handler import (
    reset_bale_id,
    reset_bot_token,
    reset_s3_access_key,
    send_support_message,
    set_bale_id,
    set_bale_bot_token,
    set_s3,
    user_my_tickets,
    user_polls_list,
    user_view_poll,
    user_view_poll_results,
    user_vote_poll_action,
    view_user_ticket,
)
from handlers.handler_helpers.callback_helpers.admin.ticket_mgmt_handler import (
    admin_captcha_settings_view,
    admin_category_detail_view,
    admin_delete_category_action,
    admin_delete_poll,
    admin_manage_categories,
    admin_poll_detail_view,
    admin_polls_management,
    admin_start_add_category,
    admin_start_poll_creation,
    admin_tickets_menu,
    admin_toggle_captcha_file,
    admin_toggle_captcha_poll,
    admin_toggle_captcha_ticket,
    admin_toggle_poll,
    admin_view_single_ticket,
)
from handlers.handler_helpers.message_helpers.captcha_handler import (
    issue_captcha,
    refresh_captcha_handler,
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
    back_to_management,
    change_donation_link,
    get_db,
    management,
    set_max_active_users,
    set_max_users,
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

from utils.filters import join_filter_cb


CALLBACK_ROUTES = {
    # main page
    "start": start,
    # set
    "set_bale_id": set_bale_id,
    "set_bale_bot_token": set_bale_bot_token,
    "set_s3": set_s3,
    "reset_s3_access_key": reset_s3_access_key,
    # resets
    "reset_bale_id": reset_bale_id,
    "reset_bot_token": reset_bot_token,
    # other
    "send_support_message": send_support_message,
    "user_new_ticket": send_support_message,
    "user_my_tickets": user_my_tickets,
    "user_polls_list": user_polls_list,
    "refresh_captcha": refresh_captcha_handler,
    "adm_manage_polls": admin_polls_management,
    "admin_create_poll_btn": admin_start_poll_creation,
    "adm_manage_cats": admin_manage_categories,
    "adm_add_cat_btn": admin_start_add_category,
    "help": help,
    "management": management,

    # backs
    "back": back,
    "back_to_management": back_to_management,

    # management
    "get_db": get_db,
    "ban_bale_id": ban_bale,
    "unban_bale_id": unban_bale,
    "ban_telegram_id": ban_telegram,
    "unban_telegram_id": unban_telegram,
    "show_10_high": show_10_high,
    "set_join_ads": set_join_ads,
    "delete_join_ads": delete_join_ads,
    "send_ads": send_ads_message,
    "send_message": send_message,
    "add_admin": add_admin,
    "delete_admin": delete_admin,
    "set_limit_all": set_limit_all,
    "set_limit": set_limit,
    "change_donation_link": change_donation_link,
    "set_max_users": set_max_users,
    "set_max_active_users": set_max_active_users,
    # whitelist
    "manage_whitelist": manage_whitelist,
    "toggle_whitelist": toggle_whitelist,
    "add_whitelist": add_whitelist,
    "remove_whitelist": remove_whitelist,
    "list_whitelist": list_whitelist,
    # captcha settings
    "adm_captcha_settings": admin_captcha_settings_view,
    "adm_toggle_captcha_ticket": admin_toggle_captcha_ticket,
    "adm_toggle_captcha_poll": admin_toggle_captcha_poll,
    "adm_toggle_captcha_file": admin_toggle_captcha_file,
}


ADMIN_CALLBACK_NAMES = {
    "management",
    "back_to_management",
    "get_db",
    "ban_bale_id",
    "unban_bale_id",
    "ban_telegram_id",
    "unban_telegram_id",
    "show_10_high",
    "set_join_ads",
    "delete_join_ads",
    "send_ads",
    "send_message",
    "add_admin",
    "delete_admin",
    "set_limit_all",
    "set_limit",
    "change_donation_link",
    "set_max_users",
    "set_max_active_users",
    "manage_whitelist",
    "toggle_whitelist",
    "add_whitelist",
    "remove_whitelist",
    "list_whitelist",
    "adm_manage_polls",
    "admin_create_poll_btn",
    "adm_manage_cats",
    "adm_add_cat_btn",
    "adm_captcha_settings",
    "adm_toggle_captcha_ticket",
    "adm_toggle_captcha_poll",
    "adm_toggle_captcha_file",
}


@Client.on_callback_query(join_filter_cb)
async def callback_handler(client: Client, callback: CallbackQuery) -> None:
    user_id = callback.from_user.id

    from db.model_async import is_user_whitelisted, check_admin
    if not is_user_whitelisted(user_id):
        await callback.answer("⛔ دسترسی شما مجاز نیست (لیست سفید فعال است).", show_alert=True)
        return

    if await check_ban(user_id):
        await callback.answer()
        return

    # Strict access control: block non-admin execution of management callbacks
    if callback.data in ADMIN_CALLBACK_NAMES or callback.data.startswith(("adm_", "admin_")):
        if not await check_admin(user_id):
            await callback.answer("⛔ دسترسی غیرمجاز.", show_alert=True)
            return

    if callback.data != "start":
        if not await is_user_exist(user_id):
            await callback.answer("کاربر یافت نشد", show_alert=True)
            return

    if callback.data.startswith("ticket_cat_"):
        try:
            cat_id = int(callback.data.split("_")[-1])
            from db import model_async
            if model_async.is_captcha_ticket_enabled():
                await callback.message.delete()
                await issue_captcha(callback.message, user_id, f"ticket_{cat_id}")
            else:
                await model_async.set_state(user_id, f"ticket_waiting_msg_{cat_id}")
                from utils.keyboards import build_back_keyboard
                await callback.message.edit_text(
                    "✍️ لطفاً متن پیام یا تیکت خود را ارسال کنید:\n"
                    "(می‌توانید متن، عکس، فایل یا ویدیو ارسال کنید)",
                    reply_markup=build_back_keyboard()
                )
            await callback.answer()
            return
        except Exception:
            pass

    if callback.data.startswith("user_select_poll_"):
        try:
            poll_id = int(callback.data.split("_")[-1])
            await user_view_poll(callback.message, user_id, poll_id=poll_id)
            await callback.answer()
            return
        except Exception:
            pass

    if callback.data.startswith("view_ticket_"):
        try:
            ticket_id = int(callback.data.split("_")[-1])
            await view_user_ticket(callback.message, user_id, ticket_id)
            await callback.answer()
            return
        except Exception:
            pass

    if callback.data.startswith("poll_vote:"):
        try:
            _, poll_id_s, opt_idx_s = callback.data.split(":")
            from db import model_async
            if model_async.is_captcha_poll_enabled():
                await callback.message.delete()
                await issue_captcha(callback.message, user_id, f"poll_{poll_id_s}_{opt_idx_s}")
            else:
                await user_vote_poll_action(callback.message, user_id, int(poll_id_s), int(opt_idx_s))
                await callback.answer("رأی شما با موفقیت ثبت شد.")
            return
        except Exception:
            pass

    if callback.data.startswith("poll_results:"):
        try:
            _, poll_id_s = callback.data.split(":")
            await user_view_poll_results(callback.message, user_id, int(poll_id_s))
            await callback.answer()
            return
        except Exception:
            pass

    # Admin Ticket Callbacks (الگوبرداری از Senfi_bot)
    if callback.data.startswith("adm_tickets:"):
        try:
            _, status_code, page_s = callback.data.split(":")
            status_map = {"unread": "خوانده نشده", "answered": "پاسخ داده شده", "all": "همه"}
            status_str = status_map.get(status_code, "خوانده نشده")
            await admin_tickets_menu(callback.message, user_id, status=status_str, page=int(page_s))
            await callback.answer()
            return
        except Exception:
            pass

    if callback.data.startswith("adm_ticket_view:"):
        try:
            _, ticket_id_s, status_code, page_s = callback.data.split(":")
            await admin_view_single_ticket(callback.message, user_id, int(ticket_id_s), status=status_code, page=int(page_s))
            await callback.answer()
            return
        except Exception:
            pass

    if callback.data.startswith("adm_reply_ticket:"):
        try:
            _, ticket_id_s, status_code, page_s = callback.data.split(":")
            from db.model_async import set_state
            from utils.keyboards import build_cancel_reply_keyboard
            await set_state(user_id, f"ticket_reply_{ticket_id_s}_{status_code}_{page_s}")
            await callback.message.reply_text(
                f"✍️ لطفاً متن پاسخ خود برای تیکت #{ticket_id_s} را ارسال کنید:",
                reply_markup=build_cancel_reply_keyboard("🔙 انصراف و بازگشت به مدیریت")
            )
            await callback.answer()
            return
        except Exception:
            pass

    if callback.data.startswith("adm_manage_cat_"):
        try:
            cat_id = int(callback.data.split("_")[-1])
            await admin_category_detail_view(callback.message, user_id, cat_id)
            await callback.answer()
            return
        except Exception:
            pass

    if callback.data.startswith("adm_del_cat_soft_"):
        try:
            cat_id = int(callback.data.split("_")[-1])
            await admin_delete_category_action(callback.message, user_id, cat_id, hard=False)
            await callback.answer()
            return
        except Exception:
            pass

    if callback.data.startswith("adm_del_cat_hard_"):
        try:
            cat_id = int(callback.data.split("_")[-1])
            await admin_delete_category_action(callback.message, user_id, cat_id, hard=True)
            await callback.answer()
            return
        except Exception:
            pass

    if callback.data.startswith("adm_cat_anon_"):
        try:
            anon_val = int(callback.data.split("_")[-1])
            state = await model_async.get_state(user_id)
            if state.startswith("choosing_category_anon_"):
                title = state.replace("choosing_category_anon_", "")
                await model_async.add_ticket_category(title, is_anonymous=anon_val)
                await model_async.set_state(user_id, "management")
                anon_desc = "🕶 ناشناس" if anon_val else "👤 عادی"
                await callback.message.edit_text(f"✅ موضوع «{title}» با حالت {anon_desc} با موفقیت افزوده شد.")
                await admin_manage_categories(callback.message, user_id)
            await callback.answer()
            return
        except Exception:
            pass

    if callback.data.startswith("adm_poll_detail_"):
        try:
            poll_id = int(callback.data.split("_")[-1])
            await admin_poll_detail_view(callback.message, user_id, poll_id)
            await callback.answer()
            return
        except Exception:
            pass

    if callback.data.startswith("adm_poll_toggle_"):
        try:
            poll_id = int(callback.data.split("_")[-1])
            await admin_toggle_poll(callback.message, user_id, poll_id)
            await callback.answer("وضعیت تغییر یافت.")
            return
        except Exception:
            pass

    if callback.data.startswith("adm_poll_delete_"):
        try:
            poll_id = int(callback.data.split("_")[-1])
            await admin_delete_poll(callback.message, user_id, poll_id)
            await callback.answer("نظرسنجی حذف شد.")
            return
        except Exception:
            pass

    handler = CALLBACK_ROUTES.get(callback.data)

    if handler is None:
        await callback.answer()
        return

    await handler(callback.message, user_id)
    await callback.answer()