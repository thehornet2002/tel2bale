# docs /handlers/handler_helpers/message_helpers/s3_handler.py

این فایل مراحل سه‌گانه دریافت اطلاعات S3 از کاربر (Access Key، Secret Key، Endpoint) و اعتبارسنجی نهایی آن‌ها را پیاده‌سازی می‌کند.

## توابع

### `async set_s3_access_key(message, user_id)`
گام اول: دریافت Access Key.

- مقدار متن پیام با `model_async.set_access_key` ذخیره می‌شود.
- state به `'set_s3_secret_key'` تغییر می‌کند.
- از کاربر خواسته می‌شود Secret Key را وارد کند.

### `async set_s3_secret_key(message, user_id)`
گام دوم: دریافت Secret Key.

- مقدار متن پیام با `model_async.set_secret_key` ذخیره می‌شود.
- state به `'set_s3_endpoint'` تغییر می‌کند.
- از کاربر خواسته می‌شود آدرس Endpoint را به‌صورت لینک وارد کند.

### `async set_s3_endpoint(message, user_id)`
گام سوم و نهایی: دریافت Endpoint، اعتبارسنجی کامل اطلاعات S3 و ذخیره نهایی.

**رفتار:**
- لینک وارد شده با `validate_link` اعتبارسنجی می‌شود؛ اگر نامعتبر باشد، پیام خطا ارسال و تابع خارج می‌شود.
- `access_key` و `secret_key` ذخیره‌شده قبلی خوانده می‌شوند.
- صحت مجموعه (access_key, secret_key, endpoint_url) با `s3_service.verify_credentials` بررسی می‌شود.
- اگر معتبر نباشد:
  - `access_key` و `secret_key` پاک می‌شوند (`None`).
  - state به `'home'` بازمی‌گردد.
  - پیام خطا («لطفا مشخصات S3 معتبر وارد کنید») ارسال می‌شود.
- اگر معتبر باشد:
  - آدرس endpoint با `model_async.set_s3_endpoint` ذخیره می‌شود.
  - state به `'home'` بازمی‌گردد.
  - پیام موفقیت ارسال می‌شود.
