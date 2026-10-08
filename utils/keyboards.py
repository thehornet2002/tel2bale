import config
from pyrogram.enums import ButtonStyle
from pyrogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    KeyboardButtonRequestChat,
    KeyboardButtonRequestUsers,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
)


def build_start_keyboard(is_admin: bool = False):
    rows = [
        [InlineKeyboardButton(text="تنظیم ID عددی بله", callback_data='set_bale_id', style=ButtonStyle('primary'))],
        [InlineKeyboardButton(text='تنظیم Bot Token بله', callback_data='set_bale_bot_token', style=ButtonStyle('primary'))],
        [InlineKeyboardButton(text='تنظیم Access Key و Secret Key برای  S3', callback_data="set_s3", style=ButtonStyle('primary'))]
    ]
    # لینک دونیت همیشه در صفحه اصلی نمایش داده می‌شود
    donate_url = config.DONATION_LINK or "https://daramet.com/Hornet2002"
    rows.append([InlineKeyboardButton(text='☕ حمایت مالی (دونیت)', url=donate_url, style=ButtonStyle('success'))])
    rows.append([InlineKeyboardButton(text='راهنمای استفاده از ربات', callback_data='help', style=ButtonStyle('success'))])
    rows.append([
        InlineKeyboardButton(text="📩 ارسال تیکت پشتیبانی", callback_data='user_new_ticket', style=ButtonStyle('primary')),
        InlineKeyboardButton(text="📋 تیکت‌های من", callback_data='user_my_tickets', style=ButtonStyle('success'))
    ])
    rows.append([
        InlineKeyboardButton(text="📊 نظرسنجی‌ها", callback_data='user_polls_list', style=ButtonStyle('primary')),
    ])
    rows.append([InlineKeyboardButton(text="GitHub", url='https://github.com/thehornet2002/tel2bale', style=ButtonStyle('success'))])
    return InlineKeyboardMarkup(rows)


def build_back_keyboard():
    rows = [
        [InlineKeyboardButton(text='بازگشت', callback_data='back', style=ButtonStyle('success'))]
    ]
    return InlineKeyboardMarkup(rows)
def build_ads_channels(channels: list) -> InlineKeyboardMarkup:
    """ساخت کیبورد شیشه‌ای برای کانال‌های عضویت اجباری"""
    rows = []
    for i, ch in enumerate(channels, 1):
        ch_str = str(ch).strip()
        if ch_str.startswith("http://") or ch_str.startswith("https://"):
            url = ch_str
            rows.append([InlineKeyboardButton(text=f"📢 عضویت در کانال {i}", url=url)])
        elif ch_str.startswith("@"):
            url = f"https://t.me/{ch_str.lstrip('@')}"
            rows.append([InlineKeyboardButton(text=f"📢 عضویت در کانال {i}", url=url)])
        elif not ch_str.startswith("-") and not ch_str.isdigit():
            url = f"https://t.me/{ch_str}"
            rows.append([InlineKeyboardButton(text=f"📢 عضویت در کانال {i}", url=url)])
        else:
            rows.append([InlineKeyboardButton(text=f"📢 کانال {i}: {ch_str}", callback_data=f"ads_{i}")])

    rows.append([InlineKeyboardButton(text="✅ عضو شدم", callback_data="start")])
    return InlineKeyboardMarkup(rows)





def build_management_keyboard() -> ReplyKeyboardMarkup:
    """پنل مدیریت به صورت کامل در کیبورد پایین صفحه (ReplyKeyboardMarkup)"""
    rows = [
        [KeyboardButton("💾 دریافت دیتابیس"), KeyboardButton("📊 ۱۰ کاربر پرمصرف")],
        [KeyboardButton("🎫 تیکت‌های پشتیبانی"), KeyboardButton("🗂 موضوعات تیکت")],
        [KeyboardButton("📊 مدیریت نظرسنجی‌ها"), KeyboardButton("➕ نظرسنجی جدید")],
        [KeyboardButton("🔐 تنظیمات کپچا"), KeyboardButton("⚙️ مدیریت لیست سفید")],
        [KeyboardButton("🚫 بن تلگرام"), KeyboardButton("✅ آنبن تلگرام")],
        [KeyboardButton("🚫 بن بله"), KeyboardButton("✅ آنبن بله")],
        [KeyboardButton("➕ افزودن ادمین"), KeyboardButton("➖ حذف ادمین")],
        [KeyboardButton("🌐 سقف حجم همگانی"), KeyboardButton("👤 سقف حجم کاربر")],
        [KeyboardButton("👥 سقف کل کاربران"), KeyboardButton("🟢 سقف کاربران فعال")],
        [KeyboardButton("📢 ارسال تبلیغات"), KeyboardButton("✉️ ارسال پیام به کاربر")],
        [KeyboardButton("🔗 ایجاد Join اجباری"), KeyboardButton("❌ حذف Join اجباری")],
        [KeyboardButton("☕ تغییر لینک دونیت"), KeyboardButton("⚙️ مدیریت لیست سفید")],
        [KeyboardButton("📱 منوی کاربری"), KeyboardButton("🔙 خروج از مدیریت")],
    ]
    return ReplyKeyboardMarkup(rows, resize_keyboard=True)


def build_back_management_keyboard() -> ReplyKeyboardMarkup:
    return build_management_keyboard()

def build_admin_home_reply_keyboard() -> ReplyKeyboardMarkup:
    """منوی کوچک ادمین در حالت عادی جهت دسترسی سریع به پنل مدیریت"""
    return ReplyKeyboardMarkup(
        [[KeyboardButton("⚙️ پنل مدیریت")]],
        resize_keyboard=True
    )


def build_whitelist_reply_keyboard(is_enabled: bool) -> ReplyKeyboardMarkup:
    """کیبورد پایین صفحه مدیریت لیست سفید"""
    status_str = "🔴 غیرفعال‌سازی لیست سفید" if is_enabled else "🟢 فعال‌سازی لیست سفید"
    return ReplyKeyboardMarkup(
        [
            [KeyboardButton(status_str)],
            [KeyboardButton("➕ افزودن به لیست سفید"), KeyboardButton("➖ حذف از لیست سفید")],
            [KeyboardButton("📋 مشاهده اعضای لیست سفید")],
            [KeyboardButton("🔙 بازگشت به مدیریت")],
        ],
        resize_keyboard=True
    )


def build_main_reply_keyboard(is_admin: bool = False):
    """کیبورد Reply فقط برای ادمین در دسترس است و هیچ گزینه‌ای برای bale_id یا bot_token ندارد."""
    if is_admin:
        return build_management_keyboard()
    return ReplyKeyboardRemove()


def build_request_user_keyboard(button_text: str = "👤 انتخاب کاربر (Choose a user)") -> ReplyKeyboardMarkup:
    """کیبورد پایین صفحه با دکمه native تلگرام برای انتخاب مستقیم کاربر"""
    return ReplyKeyboardMarkup(
        [
            [KeyboardButton(button_text, request_users=KeyboardButtonRequestUsers(button_id=1, max_quantity=1))],
            [KeyboardButton("🔙 انصراف و بازگشت به مدیریت")]
        ],
        resize_keyboard=True,
        one_time_keyboard=True
    )


def build_request_group_keyboard(button_text: str = "👥 انتخاب گروه (Choose a group)") -> ReplyKeyboardMarkup:
    """کیبورد پایین صفحه با دکمه native تلگرام برای انتخاب مستقیم گروه"""
    return ReplyKeyboardMarkup(
        [
            [KeyboardButton(button_text, request_chat=KeyboardButtonRequestChat(button_id=2, chat_is_channel=False))],
            [KeyboardButton("🔙 انصراف و بازگشت به مدیریت")]
        ],
        resize_keyboard=True,
        one_time_keyboard=True
    )


def build_cancel_reply_keyboard(button_text: str = "🔙 انصراف و بازگشت به مدیریت") -> ReplyKeyboardMarkup:
    """کیبورد انصراف برای مراحل دریافت ورودی متنی ادمین"""
    return ReplyKeyboardMarkup(
        [[KeyboardButton(button_text)]],
        resize_keyboard=True,
        one_time_keyboard=True
    )


def yes_or_no_set_id():
    rows = [
        [InlineKeyboardButton(text='بله',callback_data='reset_bale_id', style=ButtonStyle('danger'))],
        [InlineKeyboardButton(text='خیر',callback_data='back', style=ButtonStyle('success'))]
    ]
    return InlineKeyboardMarkup(rows)


yes_or_no_bale_id = yes_or_no_set_id


def yes_or_no_set_s3():
    rows = [
        [InlineKeyboardButton(text='بله',callback_data='reset_s3_access_key', style=ButtonStyle('danger'))],
        [InlineKeyboardButton(text='خیر', callback_data='back', style=ButtonStyle('success'))]
    ]
    return InlineKeyboardMarkup(rows)


def yes_or_no_set_bot_token():
    rows = [
        [InlineKeyboardButton(text='بله',callback_data='reset_bot_token', style=ButtonStyle('danger'))],
        [InlineKeyboardButton(text='خیر', callback_data='back', style=ButtonStyle('success'))]
    ]
    return InlineKeyboardMarkup(rows)


def build_ticket_categories_keyboard(categories: list[dict]) -> InlineKeyboardMarkup:
    """ساخت کیبورد انتخاب موضوع تیکت (مشابه Senfi_bot با نمایش حالت ناشناس/عادی)"""
    rows = []
    for cat in categories:
        badge = " (🕶 ناشناس)" if cat.get("is_anonymous") else " (👤 عادی)"
        rows.append([InlineKeyboardButton(text=f"📁 {cat['title']}{badge}", callback_data=f"ticket_cat_{cat['id']}")])
    rows.append([InlineKeyboardButton(text="🔙 بازگشت", callback_data="back")])
    return InlineKeyboardMarkup(rows)


def build_admin_categories_manage_keyboard(categories: list[dict]) -> InlineKeyboardMarkup:
    """کیبورد مدیریت موضوعات تیکت برای ادمین (افزودن و حذف عناوین)"""
    rows = []
    for c in categories:
        status_txt = "فعال" if c.get("is_active") else "آرشیو"
        anon_txt = "🕶 ناشناس" if c.get("is_anonymous") else "👤 عادی"
        rows.append([InlineKeyboardButton(
            text=f"📂 {c['title']} [{anon_txt} | {status_txt}]",
            callback_data=f"adm_manage_cat_{c['id']}"
        )])
    rows.append([InlineKeyboardButton(text="➕ افزودن عنوان جدید تیکت", callback_data="adm_add_cat_btn")])
    rows.append([InlineKeyboardButton(text="🔙 بستن", callback_data="back")])
    return InlineKeyboardMarkup(rows)


def build_category_anonymity_keyboard() -> InlineKeyboardMarkup:
    """انتخاب حالت عادی یا ناشناس برای عنوان جدید"""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(text="👤 عادی (مشخصات کاربر نمایش داده شود)", callback_data="adm_cat_anon_0")],
        [InlineKeyboardButton(text="🕶 ناشناس (مشخصات کاربر مخفی بماند)", callback_data="adm_cat_anon_1")],
        [InlineKeyboardButton(text="🔙 انصراف", callback_data="adm_manage_cats")],
    ])


def build_category_delete_keyboard(cat_id: int) -> InlineKeyboardMarkup:
    """گزینه‌های حذف موضوع تیکت"""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(text="🗑 حذف موضوع (تیکت‌ها باقی بمانند)", callback_data=f"adm_del_cat_soft_{cat_id}")],
        [InlineKeyboardButton(text="⚠️ حذف موضوع همراه با تمام تیکت‌های آن", callback_data=f"adm_del_cat_hard_{cat_id}")],
        [InlineKeyboardButton(text="🔙 انصراف و بازگشت", callback_data="adm_manage_cats")],
    ])


def build_user_tickets_keyboard(tickets: list[dict]) -> InlineKeyboardMarkup:
    """لیست تیکت‌های کاربر"""
    rows = []
    for t in tickets:
        status_icon = "🟢" if t.get("status") == "پاسخ داده شده" else "🟡"
        category = t.get("category_title") or "پشتیبانی"
        btn_text = f"{status_icon} تیکت #{t['id']} ({category})"
        rows.append([InlineKeyboardButton(text=btn_text, callback_data=f"view_ticket_{t['id']}")])
    rows.append([InlineKeyboardButton(text="➕ تیکت جدید", callback_data="user_new_ticket")])
    rows.append([InlineKeyboardButton(text="🔙 بازگشت به منوی اصلی", callback_data="back")])
    return InlineKeyboardMarkup(rows)


def build_ticket_detail_keyboard(ticket_id: int) -> InlineKeyboardMarkup:
    """دکمه‌های جزئیات تیکت"""
    rows = [
        [InlineKeyboardButton(text="📋 بازگشت به لیست تیکت‌ها", callback_data="user_my_tickets")],
        [InlineKeyboardButton(text="🔙 منوی اصلی", callback_data="back")]
    ]
    return InlineKeyboardMarkup(rows)


def build_admin_tickets_list_keyboard(
    tickets: list[dict],
    status: str,
    page: int,
    total_pages: int,
    status_counts: dict[str, int]
) -> InlineKeyboardMarkup:
    """لیست تیکت‌ها در پنل ادمین مشابه Senfi_bot با تب‌های وضعیت و صفحه‌بندی"""
    rows = []
    # تب‌های فیلتر وضعیت
    unread_cnt = status_counts.get("خوانده نشده", 0)
    ans_cnt = status_counts.get("پاسخ داده شده", 0)
    all_cnt = status_counts.get("همه", 0)

    rows.append([
        InlineKeyboardButton(text=f"{'🔘 ' if status == 'خوانده نشده' else ''}⏳ منتظر پاسخ ({unread_cnt})", callback_data="adm_tickets:unread:1"),
        InlineKeyboardButton(text=f"{'🔘 ' if status == 'پاسخ داده شده' else ''}✅ پاسخ داده ({ans_cnt})", callback_data="adm_tickets:answered:1"),
    ])
    rows.append([
        InlineKeyboardButton(text=f"{'🔘 ' if status == 'همه' else ''}📋 همه تیکت‌ها ({all_cnt})", callback_data="adm_tickets:all:1"),
    ])

    # لیست تیکت‌ها
    for t in tickets:
        status_ico = "🟢" if t.get("status") == "پاسخ داده شده" else "🟡"
        uname = (t.get("user_name") or "کاربر")[:10]
        rows.append([
            InlineKeyboardButton(
                text=f"#{t['id']} {status_ico} {uname}: {(t.get('message') or '')[:18]}...",
                callback_data=f"adm_ticket_view:{t['id']}:{status}:{page}"
            )
        ])

    # نوار صفحه‌بندی
    nav_row = []
    if page > 1:
        status_param = "unread" if status == "خوانده نشده" else ("answered" if status == "پاسخ داده شده" else "all")
        nav_row.append(InlineKeyboardButton(text="◀️ قبلی", callback_data=f"adm_tickets:{status_param}:{page - 1}"))
    nav_row.append(InlineKeyboardButton(text=f"📄 {page}/{total_pages}", callback_data="noop"))
    if page < total_pages:
        status_param = "unread" if status == "خوانده نشده" else ("answered" if status == "پاسخ داده شده" else "all")
        nav_row.append(InlineKeyboardButton(text="بعدی ▶️", callback_data=f"adm_tickets:{status_param}:{page + 1}"))
    if nav_row:
        rows.append(nav_row)

    rows.append([InlineKeyboardButton(text="🔙 بستن", callback_data="back")])
    return InlineKeyboardMarkup(rows)


def build_admin_ticket_view_keyboard(ticket_id: int, status: str, page: int) -> InlineKeyboardMarkup:
    """دکمه‌های اقدام روی یک تیکت در پنل ادمین"""
    status_param = "unread" if status == "خوانده نشده" else ("answered" if status == "پاسخ داده شده" else "all")
    rows = [
        [InlineKeyboardButton(text="💬 ارسال پاسخ به کاربر", callback_data=f"adm_reply_ticket:{ticket_id}:{status_param}:{page}")],
        [InlineKeyboardButton(text="🔙 بازگشت به لیست تیکت‌ها", callback_data=f"adm_tickets:{status_param}:{page}")]
    ]
    return InlineKeyboardMarkup(rows)


def build_poll_voting_keyboard(poll_id: int, options: list[str], user_vote: int | None = None) -> InlineKeyboardMarkup:
    """کیبورد شرکت در نظرسنجی برای کاربران"""
    rows = []
    for idx, opt in enumerate(options):
        prefix = "✅ " if user_vote == idx else "▫️ "
        rows.append([InlineKeyboardButton(text=f"{prefix}{opt}", callback_data=f"poll_vote:{poll_id}:{idx}")])
    rows.append([InlineKeyboardButton(text="📊 مشاهده نتایج", callback_data=f"poll_results:{poll_id}")])
    rows.append([InlineKeyboardButton(text="🔙 لیست نظرسنجی‌ها", callback_data="user_polls_list")])
    return InlineKeyboardMarkup(rows)


def build_user_polls_list_keyboard(polls: list[dict]) -> InlineKeyboardMarkup:
    """لیست چندگانه نظرسنجی‌ها برای کاربران (مشابه Senfi_bot)"""
    rows = []
    for p in polls:
        title = p.get("title") or p.get("question") or f"نظرسنجی #{p['id']}"
        rows.append([InlineKeyboardButton(text=f"📊 {title[:35]}", callback_data=f"user_select_poll_{p['id']}")])
    rows.append([InlineKeyboardButton(text="🔙 بازگشت به منوی اصلی", callback_data="back")])
    return InlineKeyboardMarkup(rows)


def build_captcha_keyboard(refreshes_left: int = 3) -> InlineKeyboardMarkup:
    """کیبورد تصویر کپچا (الگوبرداری از Senfi)"""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(text=f"🔄 تصویر جدید (فرصت: {refreshes_left})", callback_data="refresh_captcha")],
        [InlineKeyboardButton(text="🔙 انصراف و بازگشت", callback_data="back")],
    ])


def build_admin_polls_manage_keyboard(polls: list[dict]) -> InlineKeyboardMarkup:
    """کیبورد مدیریت نظرسنجی‌ها برای ادمین"""
    rows = []
    for p in polls:
        status_txt = "🟢 فعال" if p.get("is_active") else "🔴 بسته"
        label = p.get("title") or p.get("question") or f"نظرسنجی #{p['id']}"
        rows.append([InlineKeyboardButton(
            text=f"{label[:24]} [{status_txt}]",
            callback_data=f"adm_poll_detail_{p['id']}"
        )])
    rows.append([InlineKeyboardButton(text="➕ ایجاد نظرسنجی جدید", callback_data="admin_create_poll_btn")])
    rows.append([InlineKeyboardButton(text="🔙 بستن", callback_data="back")])
    return InlineKeyboardMarkup(rows)


def build_admin_poll_detail_keyboard(poll: dict) -> InlineKeyboardMarkup:
    """عملیات ادمین روی نظرسنجی مشخص"""
    toggle_txt = "🔒 بستن نظرسنجی" if poll.get("is_active") else "🔓 فعال‌سازی مجدد"
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(text="📊 مشاهده نتایج آرا", callback_data=f"poll_results:{poll['id']}")],
        [InlineKeyboardButton(text=toggle_txt, callback_data=f"adm_poll_toggle_{poll['id']}")],
        [InlineKeyboardButton(text="🗑 حذف نظرسنجی", callback_data=f"adm_poll_delete_{poll['id']}")],
        [InlineKeyboardButton(text="🔙 بازگشت به لیست نظرسنجی‌ها", callback_data="adm_manage_polls")],
    ])


def build_captcha_settings_keyboard(ticket_on: bool, poll_on: bool, file_on: bool) -> InlineKeyboardMarkup:
    """کیبورد تنظیمات فعال/غیرفعال‌سازی کپچا برای بخش‌های مختلف"""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(
            text=f"🎫 کپچای تیکت: {'🟢 فعال' if ticket_on else '🔴 غیرفعال'}",
            callback_data="adm_toggle_captcha_ticket"
        )],
        [InlineKeyboardButton(
            text=f"📊 کپچای نظرسنجی: {'🟢 فعال' if poll_on else '🔴 غیرفعال'}",
            callback_data="adm_toggle_captcha_poll"
        )],
        [InlineKeyboardButton(
            text=f"📁 کپچای ارسال فایل: {'🟢 فعال' if file_on else '🔴 غیرفعال'}",
            callback_data="adm_toggle_captcha_file"
        )],
        [InlineKeyboardButton(text="🔙 بازگشت به مدیریت", callback_data="back_to_management")]
    ])
