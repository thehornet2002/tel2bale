# docs /db/model_async.py

این فایل لایه اصلی دسترسی async به داده‌های کاربران است و روی جدول `users` کار می‌کند.
تمام handlerها و سرویس‌های پروژه برای خواندن/نوشتن اطلاعات کاربر (وضعیت، سهمیه دانلود، توکن بله، کلیدهای S3 و ...) از این فایل استفاده می‌کنند.

## نقش کلی فایل

- فراهم کردن توابع ایمن برای خواندن/نوشتن فیلدهای جدول `users` (با allowlist در برابر SQL injection)
- مدیریت سهمیه دانلود به‌صورت atomic (بدون race condition) با استفاده از `get_async_db_immediate`
- عملیات مربوط به وضعیت (state)، مسدودسازی (ban)، ادمین‌سازی و آمار کاربران

## Allowlist فیلدها

### `_USER_READABLE_FIELDS`
مجموعه فیلدهایی که اجازه دارند در عبارت `SELECT` به‌صورت پویا استفاده شوند (شامل `telegram_id`, `bale_id`, `is_banned`, `is_admin`, `state`, `bale_token`, `access_key`, `secret_key`, `downloaded_volume`, `limit_download`, `created_at`, `updated_at`, `s3_endpoint`).

### `_USER_UPDATABLE_FIELDS`
مجموعه فیلدهایی که اجازه دارند در عبارت `UPDATE` به‌صورت پویا استفاده شوند (زیرمجموعه‌ای از فیلدهای بالا، بدون `telegram_id` و ستون‌های زمانی).

> **نکته امنیتی:** پیش‌تر نام فیلد مستقیم داخل f-string قرار می‌گرفت که باعث آسیب‌پذیری SQL injection می‌شد. الان هر فیلدی قبل از استفاده در کوئری، با این دو `frozenset` بررسی و در صورت نامعتبر بودن `ValueError` صادر می‌شود.

### `_LIMIT_VOLUME`
متغیر ماژول‌سطح که سقف پیش‌فرض دانلود برای کاربران تازه‌ثبت‌نام‌شده را نگه می‌دارد و با `set_limit_volume` قابل تغییر است.

## توابع کمکی داخلی

### `async _fetchone(query, params=())  -> dict | None`
یک ردیف اجرا می‌کند و آن را به `dict` تبدیل می‌کند؛ اگر نتیجه‌ای نبود `None` برمی‌گرداند.

### `async _fetchall(query, params=()) -> list[dict]`
همه ردیف‌های نتیجه را به‌صورت لیستی از `dict` برمی‌گرداند.

### `async _execute(query, params=()) -> bool`
یک کوئری تغییردهنده (INSERT/UPDATE/DELETE) اجرا می‌کند و `True`/`False` بر اساس `cursor.rowcount > 0` برمی‌گرداند.

### `async set_limit_volume(limit_volume: float)`
مقدار سراسری `_LIMIT_VOLUME` را تنظیم می‌کند (برای استفاده هنگام افزودن کاربر جدید در `add_user`).

### `async _get_user_field(tg_id, field, default=None) -> Any`
مقدار یک فیلد از جدول `users` را برای کاربر مشخص برمی‌گرداند.

- ابتدا `field` را در برابر `_USER_READABLE_FIELDS` بررسی می‌کند؛ در غیر این صورت `ValueError`.
- اگر کاربر پیدا نشود، مقدار `default` برگردانده می‌شود.

### `async _update_user_field(tg_id, field, value) -> bool`
یک فیلد از جدول `users` را آپدیت کرده و همزمان `updated_at` را به‌روزرسانی می‌کند.

- ابتدا `field` را در برابر `_USER_UPDATABLE_FIELDS` بررسی می‌کند؛ در غیر این صورت `ValueError`.
- تمام توابع `set_*` ساده این تابع را صدا می‌زنند تا از تکرار کد و خطر SQL injection جلوگیری شود.

## وضعیت وجود کاربر / بن

### `async is_user_exist(tg_id) -> bool`
بررسی می‌کند آیا کاربری با این `telegram_id` وجود دارد.

### `async add_user(tg_id) -> bool`
کاربر جدید با `INSERT OR IGNORE` اضافه می‌کند؛ مقدار اولیه `limit_download` از `_LIMIT_VOLUME` گرفته می‌شود.
در صورت افزودن موفق، لاگ `info` ثبت می‌شود.

### `async check_admin(tg_id) -> bool`
بررسی می‌کند آیا کاربر `is_admin = 1` دارد.

### `async check_ban(tg_id) -> bool`
بررسی می‌کند آیا کاربر `is_banned = 1` دارد.

## وضعیت (State)

### `async set_state(tg_id, state) -> bool`
وضعیت گفتگوی کاربر را تغییر می‌دهد (از طریق `_update_user_field`) و لاگ `debug` ثبت می‌کند.

### `async get_state(tg_id) -> str`
وضعیت فعلی کاربر را برمی‌گرداند؛ در صورت نبود مقدار، `"home"`.

## شناسه بله

### `async get_bale_id(tg_id) -> int | None`
شناسه بله متصل به کاربر تلگرامی را برمی‌گرداند.

### `async set_bale_id(tg_id, bale_id) -> bool`
شناسه بله را برای کاربر ثبت می‌کند.

### `async get_telegram_ids_by_bale_id(bale_id) -> list[int]`
تمام `telegram_id`هایی که به یک `bale_id` مشخص وصل شده‌اند را برمی‌گرداند.

## سهمیه دانلود

### `async get_downloaded_volume(tg_id) -> float`
حجم دانلود مصرف‌شده کاربر (بر حسب GB) را برمی‌گرداند.

### `async set_downloaded_volume(tg_id, volume) -> bool`
حجم دانلود مصرف‌شده را مستقیماً تنظیم می‌کند.

### `async get_limit_download(tg_id) -> float`
سقف مجاز دانلود کاربر را برمی‌گرداند.

### `async set_limit_download(tg_id, limit) -> bool`
سقف مجاز دانلود کاربر را تنظیم می‌کند و لاگ `debug` ثبت می‌کند.

### `async reserve_download_quota(tg_id, file_size_bytes) -> bool`
به‌صورت atomic بررسی می‌کند و سهمیه لازم برای یک فایل را رزرو می‌کند.

**چرا atomic بودن لازم است:**
اگر یک `SELECT` جدا از `UPDATE` اجرا شود، وقتی کاربر چند فایل را هم‌زمان ارسال کند race condition رخ می‌دهد. با `get_async_db_immediate` (که `BEGIN IMMEDIATE` می‌زند)، این بلوک خواندن-سپس-نوشتن به‌صورت سریالی و امن اجرا می‌شود.

**رفتار:**
- اگر `file_size_bytes` خالی یا `<= 0` باشد، مستقیماً `True` برمی‌گرداند.
- حجم فایل به گیگابایت تبدیل می‌شود.
- ردیف کاربر با `SELECT ... FOR UPDATE` منطقی (از طریق قفل IMMEDIATE) خوانده می‌شود.
- اگر کاربر پیدا نشود: لاگ `warning` و `False`.
- اگر `limit_download != 0` و حجم جدید از سقف بیشتر شود: لاگ `info` و `False` (سهمیه کافی نیست).
- در غیر این صورت: `downloaded_volume` جدید ذخیره شده و `True` برگردانده می‌شود.

### `async release_download_quota(tg_id, file_size_bytes) -> bool`
سهمیه رزروشده را در صورت شکست ارسال/آپلود، به‌صورت atomic برمی‌گرداند (کم می‌کند).

- مشابه `reserve_download_quota` از `get_async_db_immediate` استفاده می‌کند.
- `downloaded_volume` جدید هرگز کمتر از `0.0` نمی‌شود (`max(0.0, ...)`).
- اگر کاربر پیدا نشود: لاگ `warning` و `False`.

### `async set_limit_download_all(limit) -> None`
سقف دانلود همه کاربران را یک‌جا (بدون شرط `WHERE`) به مقدار `limit` تغییر می‌دهد.

> از `_update_user_field` استفاده نمی‌شود چون آن تابع مخصوص به‌روزرسانی تک‌کاربر است.

## مسدودسازی (Ban)

### `async ban_user(tg_id) -> bool`
`is_banned` را `1` می‌کند و در صورت موفقیت لاگ `warning` ثبت می‌شود.

### `async unban_user(tg_id) -> bool`
`is_banned` را `0` می‌کند و در صورت موفقیت لاگ `info` ثبت می‌شود.

## ادمین

### `async set_admin(tg_id) -> bool`
`is_admin` را `1` می‌کند و لاگ `info` ثبت می‌شود.

### `async unset_admin(tg_id) -> bool`
`is_admin` را `0` می‌کند و لاگ `info` ثبت می‌شود.

## آمار

### `async get_top_users(limit: int = 10) -> list[dict]`
کاربران با بیشترین حجم دانلود را برمی‌گرداند، مرتب‌شده نزولی بر اساس `downloaded_volume`.

خروجی هر آیتم شامل `tg_id`, `bale_id`, `downloaded_volume` (رند شده به دو رقم اعشار) است.

### `async get_all_telegram_ids() -> list[int]`
تمام `telegram_id`های موجود در جدول `users` را برمی‌گرداند (برای مثال جهت ارسال پیام همگانی).

## اطلاعات اتصال Arvan/S3

### `async get_access_key(tg_id) -> str | None` / `async set_access_key(tg_id, access_key) -> bool`
خواندن/نوشتن کلید دسترسی S3 کاربر.

### `async get_secret_key(tg_id) -> str | None` / `async set_secret_key(tg_id, secret_key) -> bool`
خواندن/نوشتن کلید محرمانه S3 کاربر.

### `async get_bale_token(tg_id) -> str` / `async set_bale_token(tg_id, bale_token) -> bool`
خواندن/نوشتن توکن ربات بله کاربر (پیش‌فرض هنگام نبود مقدار: رشته خالی).

### `async get_s3_endpoint(tg_id) -> str | None` / `async set_s3_endpoint(tg_id, s3_endpoint) -> bool`
خواندن/نوشتن آدرس endpoint سرویس S3 کاربر.
