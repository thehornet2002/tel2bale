# docs /handlers/commands.py

این فایل هندلرهای دستورات اصلی تلگرام (`/start` و `/help`) را ثبت می‌کند.

## هندلرها

### `start_handle(client, message)`
با دستور `/start` در چت خصوصی فعال می‌شود.

- شرط فعال‌سازی: `filters.command('start') & filters.private & join_filter`
- `join_filter` تضمین می‌کند کاربر ابتدا در کانال‌های تبلیغاتی عضو شده باشد (`utils/filters.py`).
- `user_id` از `message.from_user.id` گرفته می‌شود.
- تابع `start` از `command_helper.py` فراخوانی می‌شود.

### `help_handle(client, message)`
با دستور `/help` در چت خصوصی فعال می‌شود.

- همان شرط‌های `start_handle` را دارد.
- تابع `help` از `command_helper.py` فراخوانی می‌شود.
