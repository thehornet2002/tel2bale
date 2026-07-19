# docs /db/db_async.py

این فایل نسخه async فایل `db_sync.py` است و با کتابخانه `aiosqlite` اتصال غیرمسدودکننده به SQLite برقرار می‌کند.
تمام توابع async دیتابیس (`model_async.py`) از این فایل استفاده می‌کنند.

## ثابت‌ها

### `DB_NAME = "bot.db"`
نام فایل دیتابیس، مشابه نسخه sync.

## توابع

### `async create_async_connection(isolation_level: str = "") -> aiosqlite.Connection`
یک اتصال async جدید به دیتابیس می‌سازد.

- اتصال با `aiosqlite.connect(DB_NAME, isolation_level=isolation_level)` باز می‌شود.
- `row_factory` روی `aiosqlite.Row` تنظیم می‌شود.
- `PRAGMA journal_mode=WAL` و `PRAGMA foreign_keys=ON` فعال می‌شوند.
- خطاها لاگ شده و دوباره raise می‌شوند.

### `get_async_db()` (async context manager)
مدیریت خودکار اتصال و تراکنش معمولی (deferred locking پیش‌فرض SQLite).

**رفتار:**
- اتصال با `create_async_connection()` ساخته می‌شود.
- اتصال `yield` می‌شود.
- در پایان موفق: `commit()`.
- در صورت خطا: `rollback()`، لاگ و raise مجدد.
- در `finally`: اتصال بسته می‌شود.

**استفاده:**
```python
async with get_async_db() as db:
    await db.execute(...)
```

### `get_async_db_immediate()` (async context manager)
نسخه‌ای با قفل `BEGIN IMMEDIATE` برای عملیات atomic از نوع «خواندن سپس نوشتن».

**چرا لازم است:**
- در `get_async_db` معمولی قفل به‌صورت deferred گرفته می‌شود؛ اگر دو coroutine هم‌زمان یک `SELECT` بزنند و سپس هر دو `UPDATE` کنند، ممکن است race condition رخ دهد (مثلاً یک ردیف دو بار پردازش شود).
- با `BEGIN IMMEDIATE` پیش از هر عملیات، فوراً write-lock گرفته می‌شود تا فقط یک coroutine در آن لحظه اجازه اجرای بلوک را داشته باشد.

**رفتار:**
- اتصال با `isolation_level=None` (حالت autocommit) ساخته می‌شود تا تراکنش به‌صورت دستی با `BEGIN`/`COMMIT`/`ROLLBACK` کنترل شود.
- `BEGIN IMMEDIATE` اجرا می‌شود.
- اتصال `yield` می‌شود.
- در پایان موفق: `COMMIT` صریح اجرا می‌شود.
- در صورت خطا: `ROLLBACK` اجرا شده و خطا دوباره raise می‌شود.
- در `finally`: اتصال بسته می‌شود.

**استفاده:**
```python
async with get_async_db_immediate() as db:
    row = await (await db.execute("SELECT ...")).fetchone()
    await db.execute("UPDATE ...")
```
