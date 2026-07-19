# docs /handlers/handler_helpers/command_helper.py

این فایل منطق واقعی پشت دستورات `/start` و `/help` را پیاده‌سازی می‌کند و توسط `handlers/commands.py` فراخوانی می‌شود.

## توابع

### `async ensure_user(user_id: int) -> bool`
اطمینان می‌دهد کاربر در دیتابیس ثبت شده و وضعیت ادمین بودن او را برمی‌گرداند.

- با `is_user_exist` بررسی می‌کند کاربر وجود دارد یا نه.
- اگر وجود نداشت، با `add_user` ساخته می‌شود.
- در پایان `check_admin(user_id)` را برمی‌گرداند.

### `async start(message: Message, user_id: int) -> None`
پاسخ به دستور `/start`.

- با `ensure_user` وضعیت ادمین کاربر مشخص می‌شود.
- پیام `START_TXT` (از `config.py`) به همراه کیبورد ساخته‌شده توسط `build_start_keyboard(is_admin)` ارسال می‌شود.

### `async help(message: Message, user_id: int) -> None`
پاسخ به دستور `/help`.

- مشابه `start`، اما متن ارسالی `HELP_TXT` است.
