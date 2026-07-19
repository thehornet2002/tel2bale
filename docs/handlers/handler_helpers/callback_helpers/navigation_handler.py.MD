# docs /handlers/handler_helpers/callback_helpers/navigation_handler.py

این فایل هندلرهای پایه‌ای برای پیمایش بین صفحات اصلی ربات (صفحه شروع، راهنما، بازگشت) را پیاده‌سازی می‌کند و توسط `handlers/callback.py` استفاده می‌شود.

## توابع

### `async start(message: Message, user_id: int) -> None`
نمایش صفحه شروع (هنگام کلیک روی دکمه «شروع»/«بازگشت به خانه»).

- اگر کاربر در دیتابیس نباشد، با `add_user` ساخته می‌شود.
- پیام موجود با `message.edit_text` به `START_TXT` همراه با کیبورد `build_start_keyboard(is_admin)` تغییر می‌کند.

### `async back(message: Message, user_id: int) -> None`
بازگشت به صفحه اصلی از هر جای دیگر ربات.

- وضعیت کاربر با `set_state(user_id, "home")` بازنشانی می‌شود.
- پیام با `START_TXT` و کیبورد مناسب ویرایش می‌شود.

### `async help(message: Message, user_id: int) -> None`
نمایش صفحه راهنما از طریق دکمه.

- وضعیت کاربر روی `"home"` تنظیم می‌شود.
- پیام با `HELP_TXT` و کیبورد مناسب ویرایش می‌شود.
