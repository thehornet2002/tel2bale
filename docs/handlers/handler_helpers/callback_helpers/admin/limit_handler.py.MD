# docs /handlers/handler_helpers/callback_helpers/admin/limit_handler.py

این فایل هندلرهای callback مربوط به شروع فرآیند تنظیم سقف دانلود (برای همه کاربران یا یک کاربر خاص) را پیاده‌سازی می‌کند. هر دو تابع با `admin_required` محافظت شده‌اند.

## توابع

### `async set_limit_all(message, user_id) -> None`
شروع فرآیند تنظیم سقف دانلود برای همه کاربران.

- state روی `"set_limit_all_send_volume"` تنظیم می‌شود.
- از ادمین خواسته می‌شود مقدار محدودیت دانلود (بر حسب GB) را وارد کند.

### `async set_limit(message, user_id) -> None`
شروع فرآیند تنظیم سقف دانلود برای یک کاربر خاص.

- state روی `"set_limit_send_id"` تنظیم می‌شود.
- از ادمین خواسته می‌شود ID عددی کاربر موردنظر را وارد کند (در گام بعد مقدار سقف پرسیده می‌شود).
