# docs /handlers/handler_helpers/callback_helpers/admin/ban_handler.py

این فایل هندلرهای callback مربوط به شروع فرآیند بن/آنبن کاربران (بر اساس شناسه بله یا تلگرام) را پیاده‌سازی می‌کند. تمام توابع با `admin_required` محافظت شده‌اند و صرفاً state کاربر را برای دریافت ID در پیام بعدی تنظیم می‌کنند؛ منطق واقعی بن/آنبن در `message_helpers/admin_handler.py` انجام می‌شود.

## توابع

### `async ban_bale(message, user_id) -> None`
state روی `"enter_bale_ban"` تنظیم می‌شود و از ادمین خواسته می‌شود ID عددی بله فرد موردنظر را وارد کند.

### `async unban_bale(message, user_id) -> None`
state روی `"enter_bale_unban"` تنظیم می‌شود و از ادمین خواسته می‌شود ID عددی بله فرد موردنظر را وارد کند.

### `async ban_telegram(message, user_id) -> None`
state روی `"enter_telegram_ban"` تنظیم می‌شود و از ادمین خواسته می‌شود ID عددی تلگرام فرد موردنظر را وارد کند.

### `async unban_telegram(message, user_id) -> None`
state روی `"enter_telegram_unban"` تنظیم می‌شود و از ادمین خواسته می‌شود ID عددی تلگرام فرد موردنظر را وارد کند.

> در همه توابع، کیبورد بازگشت به پنل مدیریت (`build_back_management_keyboard`) نمایش داده می‌شود.
