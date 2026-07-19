# docs /handlers/handler_helpers/callback_helpers/admin/admin_mgmt_handler.py

این فایل هندلرهای callback مربوط به افزودن و حذف ادمین را پیاده‌سازی می‌کند. هر دو تابع با دکوریتور `admin_required` محافظت شده‌اند.

## توابع

### `async add_admin(message, user_id) -> None`
شروع فرآیند افزودن ادمین جدید.

- state روی `"add_admin_send_id"` تنظیم می‌شود.
- از ادمین خواسته می‌شود ID عددی تلگرام ادمین جدید را وارد کند.

### `async delete_admin(message, user_id) -> None`
شروع فرآیند حذف یک ادمین.

- state روی `"delete_admin_send_id"` تنظیم می‌شود.
- لیست `ADMIN_IDS` (از `config.py`) به همراه شماره ردیف نمایش داده می‌شود تا ادمین بتواند شناسه موردنظر را انتخاب/وارد کند.
- کیبورد بازگشت به پنل مدیریت (`build_back_management_keyboard`) نمایش داده می‌شود.
