# docs /handlers/handler_helpers/message_helpers/user_handler.py

این فایل هندلرهای پیام مربوط به دریافت مقدار واقعی شناسه بله، توکن ربات بله و پیام پشتیبانی از کاربر را پیاده‌سازی می‌کند (ادامه فرآیندهایی که در `callback_helpers/user_handler.py` شروع شده‌اند).

## توابع

### `async enter_bale_id(message, user_id)`
دریافت و ذخیره شناسه عددی بله کاربر.

- با `get_valid_id` مقدار عددی از پیام استخراج می‌شود؛ اگر نامعتبر باشد، تابع بدون ادامه خارج می‌شود (پیام خطا قبلاً توسط `get_valid_id` ارسال شده).
- شناسه با `model_async.set_bale_id` ذخیره می‌شود.
- state کاربر روی `'home'` بازنشانی می‌شود.
- پیام موفقیت با کیبورد بازگشت ارسال می‌شود.

### `async set_bale_token_bot(message, user_id)`
دریافت، اعتبارسنجی و ذخیره توکن ربات بله کاربر.

- توکن با `bale_bot.verify_token(message.text)` (فراخوانی `getMe` روی API بله) اعتبارسنجی می‌شود.
- اگر معتبر باشد: توکن با `model_async.set_bale_token` ذخیره می‌شود، state روی `'home'` تنظیم و پیام موفقیت ارسال می‌شود.
- اگر نامعتبر باشد: state همچنان روی `'home'` تنظیم می‌شود و پیام خطای «توکن معتبر نمی‌باشد» ارسال می‌شود.

### `async send_support_message(message, user_id)`
دریافت و ذخیره پیام پشتیبانی کاربر.

- متن پیام با `model_async.save_support_message(user_id, message_text=...)` ذخیره می‌شود.
- state روی `'home'` بازنشانی می‌شود.
- پیام تأیید ارسال به کاربر نمایش داده می‌شود.
