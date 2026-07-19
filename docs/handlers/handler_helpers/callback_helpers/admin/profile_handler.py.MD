# docs /handlers/handler_helpers/callback_helpers/admin/profile_handler.py

این فایل هندلر callback شروع فرآیند تغییر عکس پروفایل ربات بله را پیاده‌سازی می‌کند و با `admin_required` محافظت شده است.

## توابع

### `async set_profile_photo(message, user_id) -> None`
شروع فرآیند تنظیم عکس پروفایل ربات.

- state روی `"set_profile_photo_send_photo"` تنظیم می‌شود.
- از ادمین خواسته می‌شود تصویر پروفایل موردنظر را ارسال کند (دریافت واقعی تصویر در `message_helpers/profile_handler.py` انجام می‌شود).
