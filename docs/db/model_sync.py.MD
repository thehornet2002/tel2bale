# docs /db/model_sync.py

این فایل شامل توابع sync برای ساخت جدول‌های دیتابیس و مدیریت اولیه کاربران است.
از `get_db()` در `db_sync.py` برای اجرای کوئری‌ها استفاده می‌کند.

## جدول‌ها

### `create_tables() -> None`
جدول `users` را در صورت عدم وجود می‌سازد (`CREATE TABLE IF NOT EXISTS`).

**ستون‌های جدول `users`:**
- `id`: کلید اصلی، `AUTOINCREMENT`
- `telegram_id`: شناسه تلگرام کاربر، `UNIQUE` و `NOT NULL`
- `bale_id`: شناسه بله کاربر (پیش‌فرض `NULL`)
- `is_banned`: وضعیت مسدودیت (پیش‌فرض `0`)
- `is_admin`: وضعیت ادمین بودن (پیش‌فرض `0`)
- `state`: وضعیت فعلی کاربر در گفتگو (پیش‌فرض `'home'`)
- `bale_token`: توکن ربات بله کاربر
- `s3_endpoint`, `access_key`, `secret_key`: اطلاعات اتصال به S3
- `downloaded_volume`: حجم دانلود مصرف‌شده (پیش‌فرض `0`)
- `limit_download`: سقف مجاز دانلود (پیش‌فرض `0`)
- `created_at`, `updated_at`: زمان ایجاد و آخرین بروزرسانی (پیش‌فرض `datetime('now','localtime')`)

پس از ساخت موفق جدول‌ها، یک لاگ `info` ثبت می‌شود.

## کاربران

### `add_user(telegram_id: int, is_admin: bool = False) -> bool`
یک کاربر جدید به جدول `users` اضافه می‌کند.

- از `INSERT OR IGNORE` استفاده می‌کند تا در صورت تکراری بودن `telegram_id` خطایی رخ ندهد.
- بررسی می‌کند که آیا واقعاً ردیفی درج شده (`cursor.rowcount > 0`).

**خروجی:**
- `True` → کاربر با موفقیت اضافه شد (کاربر جدید بود)
- `False` → کاربر از قبل وجود داشت

در صورت افزودن موفق، یک لاگ `info` با شناسه کاربر ثبت می‌شود.
