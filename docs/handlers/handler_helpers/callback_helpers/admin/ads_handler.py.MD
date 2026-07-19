# docs /handlers/handler_helpers/callback_helpers/admin/ads_handler.py

این فایل هندلرهای callback مربوط به مدیریت کانال‌های تبلیغاتی اجباری (join channels) را پیاده‌سازی می‌کند. هر دو تابع با `admin_required` محافظت شده‌اند.

## توابع

### `async set_join_ads(message, user_id) -> None`
شروع فرآیند افزودن یک کانال تبلیغاتی جدید.

- state روی `"enter_join_ads_channel"` تنظیم می‌شود.
- از ادمین خواسته می‌شود ID کانال (مثل `tel2bale`) را وارد کند.

### `async delete_join_ads(message, user_id) -> None`
شروع فرآیند حذف یک کانال تبلیغاتی موجود.

- state روی `"enter_delete_join_ads"` تنظیم می‌شود.
- لیست کانال‌های موجود (`ADS_CHANNELS` از `config.py`) نمایش داده می‌شود تا ادمین کانال موردنظر برای حذف را انتخاب/وارد کند.
