# docs /quota_service.py

این فایل مسئول مدیریت «سهمیه دانلود» کاربر است.  
هدف آن اطمینان از این است که هنگام ارسال هم‌زمان چند فایل، مصرف سهمیه به شکل درست و بدون race condition ثبت شود.

## نقش کلی فایل

- بررسی و reserve کردن سهمیه مصرف دانلود قبل از شروع انتقال
- آزادسازی/rollback سهمیه در صورت شکست عملیات بعد از reserve

---

## توابع

### `async check_and_update_quota(user_id: int, file_size_bytes: int | None) -> bool`
این تابع سهمیه کاربر را برای دانلود یک فایل (با حجم مشخص) بررسی و مصرف را **reserve** می‌کند.

ویژگی‌های مهم:
- به صورت اتمیک توسط تابع `reserve_download_quota` انجام می‌شود.
- چون عملیات reserve به صورت اتمیک انجام می‌گیرد:
  - اگر کاربر چند فایل را هم‌زمان بفرستد،
  - مصرف دانلود به درستی ثبت می‌شود و race condition رخ نمی‌دهد.

پارامترها:
- `user_id`: شناسه کاربر
- `file_size_bytes`: حجم فایل به بایت (ممکن است `None` باشد)

خروجی:
- `bool` که نشان می‌دهد reserve سهمیه با موفقیت انجام شده است یا نه.

---

### `async rollback_quota(user_id: int, file_size_bytes: int | None) -> bool`
اگر بعد از reserve شدن سهمیه، انتقال/عملیات دانلود شکست بخورد، این تابع سهمیه را برمی‌گرداند.

- این کار با فراخوانی `release_download_quota` انجام می‌شود.
- خروجی: `bool` که نشان می‌دهد rollback با موفقیت انجام شده است یا نه.

پارامترها:
- `user_id`: شناسه کاربر
- `file_size_bytes`: حجم فایلی که reserve شده بود (ممکن است `None` باشد)

---

## وابستگی‌ها

- `reserve_download_quota` از `db.model_async`
  - reserve کردن اتمیک سهمیه مصرف دانلود
- `release_download_quota` از `db.model_async`
  - برگرداندن سهمیه در صورت نیاز (rollback)