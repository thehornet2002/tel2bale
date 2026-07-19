# docs /s3_service.py

این فایل مسئول آپلود فایل در فضای S3 (سازگار با AWS) و تولید لینک موقت برای دانلود است.  
همچنین صحت credentials را با یک درخواست سبک اعتبارسنجی می‌کند. برای جلوگیری از تداخل نام فایل‌ها، نام فایل با UUID تولید می‌شود و در صورت پر بودن/محدودیت ذخیره‌سازی، باکت تخلیه شده و تلاش دوباره انجام می‌شود.

## نقش کلی فایل

- اتصال به S3 با `aioboto3`
- آپلود فایل با نام یکتا (UUID + پسوند)
- ساخت لینک موقت (presigned URL)
- مدیریت خطای ظرفیت/محدودیت با تخلیه باکت و retry
- حذف فایل موقت از دیسک بعد از پایان عملیات
- اعتبارسنجی `access_key` و `secret_key`

---

## وابستگی‌ها

- `aioboto3` : کلاینت async برای S3
- `botocore.exceptions.ClientError` : هندل خطاهای S3
- `os` : کار با فایل سیستم
- `uuid` : تولید نام یکتا برای object key
- `utils.logger.get_logger` : لاگ‌گیری

---

## تابع‌ها

### `async create_connection(access_key: str, secret_key: str) -> aioboto3.Session`
یک session برای دسترسی به S3 می‌سازد.

- ورودی‌ها:
  - `access_key`
  - `secret_key`
- خروجی: `aioboto3.Session` آماده برای ساخت کلاینت

---

### `async empty_bucket(s3_client, bucket_name: str)`
تابع کمکی برای حذف تمام فایل‌های یک باکت.

رفتار:
- با `list_objects_v2` فایل‌ها را صفحه‌بندی می‌کند (paginator)
- برای هر صفحه:
  - لیست `Key`ها را می‌سازد
  - با `delete_objects` دسته‌ای حذف می‌کند
- لاگ وضعیت را چاپ می‌کند
- در صورت خطا، خطا را `raise` می‌کند تا عملیات اصلی متوقف شود

---

### `async upload_file(session, file_path: str, endpoint_url: str, object_key: str, bucket_name="my-telegram-bot", content_type="application/octet-stream", expires_in=3600) -> str`
مهم‌ترین تابع فایل است و کل جریان آپلود و لینک دانلود را انجام می‌دهد.

> نکته: در این کد پارامتر `object_key` عملاً برای ساخت کلید استفاده نشده و به‌جایش `unique_object_key` از روی UUID ساخته می‌شود.

مراحل:
1. **چک وجود فایل**
   - اگر فایل وجود نداشته باشد: `"❌ فایل برای آپلود یافت نشد."` برمی‌گرداند.

2. **محاسبه حجم برای لاگ**
   - حجم فایل از `os.path.getsize` گرفته می‌شود (برای گزارش، نه برای کنترل منطق).

3. **تولید نام یکتا**
   - پسوند از روی `file_path` گرفته می‌شود.
   - `unique_object_key = f"{uuid.uuid4().hex}{ext}"`

4. **ساخت کلاینت S3**
   - با `session.client("s3", endpoint_url=endpoint_url)` یک کلاینت async می‌سازد.

5. **بررسی وجود باکت / ساخت باکت**
   - با `head_bucket` وجود باکت را چک می‌کند.
   - اگر وجود نداشت (`404` یا `NoSuchBucket`):
     - با `create_bucket` باکت را می‌سازد.

6. **آپلود با try/except برای خطاهای ظرفیت**
   - فایل را به صورت باینری (`open(file_path, "rb")`) باز می‌کند.
   - با `put_object` آپلود می‌کند:
     - `Bucket=bucket_name`
     - `Key=unique_object_key`
     - `Body=file_data`
     - `ContentType=content_type`
   - اگر خطا از جنس ظرفیت/ذخیره ناکافی باشد:
     - `QuotaExceeded`, `InsufficientStorage`, `RequestLimitExceeded`, `403`
     - لاگ هشدار می‌زند
     - با `empty_bucket` باکت را تخلیه می‌کند
     - `file_data.seek(0)` می‌زند تا دوباره از ابتدا قابل خواندن باشد
     - سپس یک بار دیگر `put_object` را امتحان می‌کند
   - اگر خطای دیگری باشد، خطا را throw می‌کند.

7. **ساخت لینک موقت دانلود**
   - با `generate_presigned_url('get_object', Params={Bucket, Key}, ExpiresIn=expires_in)`
   - خروجی: `file_url`

8. **هندل خطاهای کلی**
   - `ClientError`:
     - پیام خطا را از `e.response` استخراج می‌کند و با متن `"❌ خطای S3"` برمی‌گرداند
   - خطای غیرمنتظره:
     - با `"❌ خطای غیرمنتظره"` برمی‌گرداند

9. **پاکسازی فایل موقت (finally)**
   - در هر شرایطی، اگر فایل روی دیسک وجود داشته باشد:
     - `os.remove(file_path)`
     - لاگ cleanup موفق/ناموفق را ثبت می‌کند

خروجی:
- لینک presigned (اگر آپلود موفق باشد)
- یا رشته خطا (اگر ناموفق باشد)

---

### `async verify_credentials(access_key: str, secret_key: str, endpoint_url: str) -> bool`
صحت `access_key` و `secret_key` را با یک درخواست سبک بررسی می‌کند.

رفتار:
- با `create_connection` session می‌سازد
- یک کلاینت `s3` می‌سازد
- با `list_buckets()` اجازه دسترسی را تست می‌کند (نیاز به bucket name ندارد)
- اگر موفق باشد: `True`
- اگر `ClientError` رخ دهد:
  - لاگ warning می‌زند
  - `False` برمی‌گرداند
- اگر خطای عمومی رخ دهد:
  - لاگ error می‌زند
  - `False` برمی‌گرداند
