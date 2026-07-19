# docs /handlers/messages.py

این فایل نقطه ورود اصلی برای مدیریت پیام‌های عادی (غیر از `/start` و `/help`) است و بر اساس «وضعیت» (state) فعلی کاربر، پیام را به هندلر مناسب هدایت می‌کند. این الگو یک State Machine ساده برای مکالمه با کاربر پیاده‌سازی می‌کند.

## نقش کلی فایل

- تجمیع تمام هندلرهای پیام از زیرماژول‌های `message_helpers/*`
- نگاشت هر state ذخیره‌شده در دیتابیس به تابع هندلر مربوطه (`STATE_HANDLERS`)
- پشتیبانی از stateهای پویا (dynamic) با الگوی regex برای عملیات‌هایی مثل ارسال پیام به چند کاربر یا تنظیم محدودیت

## الگوهای Regex

### `SEND_MESSAGE_RE = r"^send_message_\d+$"`
تشخیص stateهایی مثل `send_message_123456` (شناسه چت هدف پیام ادمین).

### `SET_LIMIT_RE = r"^set_limit_\d+$"`
تشخیص stateهایی مثل `set_limit_123456` (شناسه کاربر برای تنظیم سهمیه دانلود).

## نگاشت وضعیت به هندلر

### `STATE_HANDLERS: dict`
دیکشنری‌ای که هر state ثابت را به تابع هندلر مربوطه از `message_helpers/*` نگاشت می‌کند؛ برای مثال:
- `"home"` → `forward` (حالت پیش‌فرض؛ فوروارد فایل به بله)
- `"enter_bale_id"` → دریافت شناسه بله کاربر
- `"send_support_message"` → ارسال پیام پشتیبانی
- `"set_bale_token_bot"` → ثبت توکن ربات بله
- `"enter_bale_ban"` / `"enter_bale_unban"` / `"enter_telegram_ban"` / `"enter_telegram_unban"` → عملیات بن/آنبن ادمین
- `"enter_join_ads_channel"` / `"enter_delete_join_ads"` → مدیریت کانال‌های تبلیغاتی
- `"enter_ads_message"` / `"send_message_chat_id"` → ارسال پیام همگانی/هدفمند
- `"add_admin_send_id"` / `"delete_admin_send_id"` → مدیریت ادمین‌ها
- `"set_profile_photo_send_photo"` → تنظیم عکس پروفایل ربات بله
- `"set_limit_all_send_volume"` / `"set_limit_send_id"` → تنظیم سقف دانلود
- `"change_donation_link"` → تغییر لینک حمایت مالی
- `"set_s3_access_key"` / `"set_s3_secret_key"` / `"set_s3_endpoint"` → تنظیمات S3

## هندلر اصلی

### `handle_input(client, message)`
روی هر پیام خصوصی به‌جز `/start` و `/help` (و پس از عبور از `join_filter`) اجرا می‌شود.

**مراحل:**
1. اگر کاربر در دیتابیس وجود نداشته باشد، پیام نادیده گرفته می‌شود (`return`).
2. اگر کاربر بن باشد (`check_ban`)، پیام نادیده گرفته می‌شود.
3. `state` فعلی کاربر با `get_state` خوانده می‌شود.
4. اگر state دقیقاً در `STATE_HANDLERS` باشد، هندلر مربوطه با `(message, user_id)` صدا زده می‌شود.
5. در غیر این صورت، اگر state با الگوی `SEND_MESSAGE_RE` مطابقت داشته باشد، `send_message_send_message` صدا زده می‌شود (متن پیامی که باید ارسال شود).
6. در غیر این صورت، اگر state با الگوی `SET_LIMIT_RE` مطابقت داشته باشد، `set_limit_set_limit` صدا زده می‌شود (مقدار عددی سقف دانلود).
