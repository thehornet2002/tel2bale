# docs /handlers/callback.py

این فایل نقطه ورود اصلی برای مدیریت callback queryهای دکمه‌های اینلاین است و بر اساس مقدار `callback.data`، درخواست را به هندلر مناسب هدایت می‌کند (یک router ساده مشابه `handlers/messages.py` اما برای callbackها).

## نقشه مسیرها

### `CALLBACK_ROUTES: dict`
دیکشنری‌ای که هر مقدار `callback_data` را به تابع هندلر مربوطه از `callback_helpers/*` نگاشت می‌کند؛ دسته‌بندی‌ها:

- **صفحه اصلی:** `"start"` → `start`
- **تنظیم:** `"set_bale_id"`, `"set_bale_bot_token"`, `"set_s3"`, `"reset_s3_access_key"`
- **بازنشانی:** `"reset_bale_id"`, `"reset_bot_token"`
- **متفرقه:** `"send_support_message"`, `"help"`, `"management"`
- **بازگشت:** `"back"`, `"back_to_management"`
- **مدیریت (ادمین):** `"get_db"`, `"ban_bale_id"`, `"unban_bale_id"`, `"ban_telegram_id"`, `"unban_telegram_id"`, `"show_10_high"`, `"set_join_ads"`, `"delete_join_ads"`, `"send_ads"`, `"send_message"`, `"add_admin"`, `"delete_admin"`, `"set_profile_photo"`, `"set_limit_all"`, `"set_limit"`, `"change_donation_link"`

## هندلر اصلی

### `callback_handler(client, callback)`
روی هر callback query که از فیلتر `join_filter_cb` عبور کند اجرا می‌شود.

**مراحل:**
1. اگر کاربر بن باشد: فقط `callback.answer()` خالی فراخوانی و خارج می‌شود (بدون پیام خطا).
2. اگر `callback.data` برابر `"start"` نباشد و کاربر در دیتابیس وجود نداشته باشد: با `callback.answer("کاربر یافت نشد", show_alert=True)` به کاربر اطلاع داده می‌شود.
3. هندلر مربوط به `callback.data` از `CALLBACK_ROUTES` گرفته می‌شود.
4. اگر هندلری پیدا نشود، فقط `callback.answer()` خالی اجرا و خارج می‌شود.
5. در غیر این صورت، هندلر با `(callback.message, user_id)` اجرا می‌شود و در پایان `callback.answer()` صدا زده می‌شود (برای برداشتن حالت لودینگ دکمه در کلاینت).
