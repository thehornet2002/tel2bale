# docs /handlers/handler_helpers/message_helpers/profile_handler.py

هندلر پیام مربوط به تغییر عکس پروفایل حساب/رباتی که پیام از طریق آن ارسال شده است. فقط ادمین‌ها اجازه دسترسی دارند (`admin_only`).

## توابع

### `async set_profile_photo_send_photo(message, user_id)`
دریافت عکس ارسالی و تنظیم آن به‌عنوان عکس پروفایل.

**رفتار:**
- اگر پیام حاوی عکس نباشد: پیام خطا ارسال شده و state به `'management'` بازمی‌گردد (سپس تابع خارج می‌شود).
- عکس با `message.download()` روی دیسک محلی ذخیره می‌شود.
- تمام عکس‌های پروفایل فعلی («me») با `get_chat_photos` پیمایش و با `delete_profile_photos` حذف می‌شوند.
- عکس جدید با `set_profile_photo(photo=path)` تنظیم می‌شود.
- پیام موفقیت ارسال و state به `'management'` بازمی‌گردد.
- در صورت بروز خطا: پیام خطا با متن استثنا ارسال شده و state باز هم به `'management'` بازمی‌گردد.
- در `finally`: فایل موقت دانلودشده از دیسک حذف می‌شود تا فضای اضافی باقی نماند.
