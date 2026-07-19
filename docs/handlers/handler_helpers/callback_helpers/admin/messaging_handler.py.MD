# docs /handlers/handler_helpers/callback_helpers/admin/messaging_handler.py

این فایل هندلرهای callback مربوط به شروع فرآیند ارسال پیام همگانی و پیام هدفمند به یک کاربر خاص را پیاده‌سازی می‌کند. هر دو تابع با `admin_required` محافظت شده‌اند.

## توابع

### `async send_ads_message(message, user_id) -> None`
شروع فرآیند ارسال پیام همگانی (broadcast) به همه کاربران.

- state روی `"enter_ads_message"` تنظیم می‌شود.
- از ادمین خواسته می‌شود متن پیام همگانی را وارد کند.

### `async send_message(message, user_id) -> None`
شروع فرآیند ارسال پیام به یک کاربر خاص.

- state روی `"send_message_chat_id"` تنظیم می‌شود.
- از ادمین خواسته می‌شود ID عددی تلگرام کاربر مقصد را وارد کند (در گام بعد متن پیام پرسیده می‌شود).
