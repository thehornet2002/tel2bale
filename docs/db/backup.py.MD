# docs /db/backup.py

این فایل مسئول ساخت نسخه پشتیبان (backup) از دیتابیس SQLite پروژه است.

## نقش کلی فایل

- ساخت backup سالم و سازگار از فایل `bot.db` حتی در حالت `WAL`
- ارائه نسخه sync و نسخه async (برای استفاده داخل handlerها بدون بلاک کردن event loop)

## توابع

### `create_database_backup(db_path=DB_NAME, backup_dir="backups", prefix="bot_backup") -> str`
یک backup کامل از دیتابیس می‌سازد و مسیر فایل backup را برمی‌گرداند.

**چرا از `sqlite3` backup API استفاده می‌شود:**
وقتی SQLite در حالت `WAL` باشد، کپی ساده فایل `bot.db` کافی نیست، چون ممکن است بخشی از تغییرات هنوز در `bot.db-wal` باشد و کپی مستقیم ناقص/خراب شود. متد `Connection.backup()` یک snapshot سالم و سازگار می‌سازد.

**رفتار:**
- اگر فایل دیتابیس مبدأ وجود نداشته باشد: `FileNotFoundError`.
- پوشه `backup_dir` در صورت نبود ساخته می‌شود.
- نام فایل backup با timestamp (`%Y%m%d_%H%M%S`) و `prefix` ساخته می‌شود.
- دو اتصال sqlite (مبدأ و مقصد) با `timeout=30` و `PRAGMA busy_timeout = 5000` باز می‌شوند.
- `source.backup(destination)` اجرا و سپس `destination.commit()` می‌شود.
- در صورت موفقیت: لاگ `info` با مسیر backup ثبت می‌شود.
- در صورت خطا:
  - خطا با `logger.exception` ثبت می‌شود.
  - اگر فایل backup ناقص ساخته شده باشد، حذف می‌شود.
  - خطا دوباره raise می‌شود.
- در `finally`: هر دو اتصال (در صورت باز بودن) بسته می‌شوند.

### `async create_database_backup_async(db_path=DB_NAME, backup_dir="backups", prefix="bot_backup") -> str`
نسخه async تابع بالا، برای استفاده داخل handlerهای async.

- چون ساخت backup یک عملیات sync و مسدودکننده است، با `asyncio.to_thread(...)` در یک ترد جدا اجرا می‌شود تا event loop اصلی ربات بلاک نشود.
- همان آرگومان‌ها و همان مقدار خروجی (مسیر فایل backup) را دارد.
