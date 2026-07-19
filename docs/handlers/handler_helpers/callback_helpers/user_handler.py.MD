# docs /handlers/handler_helpers/callback_helpers/user_handler.py

این فایل هندلرهای callback مربوط به تنظیمات شخصی کاربر (شناسه بله، توکن ربات بله، اطلاعات S3، پیام پشتیبانی) را پیاده‌سازی می‌کند.

## توابع

### `async set_bale_id(message, user_id) -> None`
شروع فرآیند تنظیم شناسه عددی بله کاربر.

- اگر کاربر قبلاً `bale_id` تنظیم کرده باشد: پیام تأیید با دکمه‌های «بله/خیر» (`yes_or_no_bale_id`) نمایش داده می‌شود.
- اگر نداشته باشد: state روی `'enter_bale_id'` تنظیم و از کاربر خواسته می‌شود مقدار را وارد کند.
- در صورت بروز خطا، پیام خطا با متن استثنا به کاربر ارسال می‌شود.

### `async reset_bale_id(message, user_id) -> None`
بازنشانی مستقیم شناسه بله (بدون پرسیدن تأیید)؛ state روی `'enter_bale_id'` تنظیم می‌شود.

### `async set_s3(message, user_id) -> None`
شروع فرآیند تنظیم اطلاعات S3 (Arvan Storage).

- سه مقدار `access_key`, `secret_key`, `s3_endpoint` خوانده می‌شوند.
- اگر هرکدام مقدار نداشته باشد: state روی `'set_s3_access_key'` تنظیم و از کاربر خواسته می‌شود Access Key را وارد کند.
- اگر هر سه مقدار موجود باشد: پیام تأیید با دکمه‌های «بله/خیر» (`yes_or_no_set_s3`) نمایش داده می‌شود.

### `async reset_s3_access_key(message, user_id) -> None`
بازنشانی مستقیم اطلاعات S3؛ state روی `'set_s3_access_key'` تنظیم می‌شود.

### `async set_bale_bot_token(message, user_id) -> None`
شروع فرآیند تنظیم توکن ربات بله.

- اگر توکن قبلاً تنظیم نشده باشد: state روی `'set_bale_token_bot'` تنظیم و از کاربر خواسته می‌شود توکن را وارد کند.
- اگر توکن قبلاً وجود داشته باشد: پیام تأیید با دکمه‌های «بله/خیر» (`yes_or_no_set_bot_token`) نمایش داده می‌شود.

### `async reset_bot_token(message, user_id) -> None`
بازنشانی مستقیم توکن ربات بله؛ state روی `'set_bale_token_bot'` تنظیم می‌شود.

### `async send_support_message(message, user_id) -> None`
شروع فرآیند ارسال پیام پشتیبانی توسط کاربر.

- state روی `"send_support_message"` تنظیم می‌شود.
- از کاربر خواسته می‌شود متن پیام خود را وارد کند.

> در تمام توابع بالا، پیام قبلی با `message.edit_text` ویرایش می‌شود (به‌جز حالت خطا در `set_bale_id` که با `reply_text` پاسخ داده می‌شود) و اکثر توابع از `build_back_keyboard()` برای دکمه بازگشت استفاده می‌کنند.
