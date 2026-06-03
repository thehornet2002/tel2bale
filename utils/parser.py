import re
from urllib.parse import urlparse

async def validate_link(s: str):
    """
    دریافت یک رشته، بررسی کامل اینکه آیا لینک است یا خیر.
    در صورت درست بودن، لینک نرمال‌شده (با scheme در صورت نیاز) برگردانده می‌شود،
    در غیر این صورت False برمی‌گردد.
    """
    if not s or not isinstance(s, str):
        return False

    s = s.strip()

    # اگر scheme وجود نداشت، برای بررسی اولیه http اضافه می‌کنیم (برای parse صحیح)
    parsed = urlparse(s if re.match(r'^[a-zA-Z][a-zA-Z0-9+\-.]*://', s) else 'http://' + s)

    # باید scheme و netloc داشته باشیم
    if not parsed.scheme or not parsed.netloc:
        return False

    # ساده‌ترین چک برای دامنه: حداقل یک نقطه در host و کاراکترهای مجاز
    host = parsed.netloc.split('@')[-1].split(':')[0]  # حذف احتمال credential یا پورت
    if not re.match(r'^[A-Za-z0-9\-\._~%]+(\.[A-Za-z0-9\-\._~%]+)+$', host):
        return False

    # اختیاری: چک کردن طول بخش‌ها و اینکه host با عدد خالص (IP) نباشد مگر نوع IP معتبر باشد
    # اگر نیاز به پشتیبانی IP هست، می‌توان بررسی IP اضافه کرد.

    # بازگرداندن لینک نرمال‌شده: اگر ورودی scheme نداشت، scheme://host/... را برمی‌گردانیم (http پیش‌فرض)
    normalized = parsed.geturl()
    return normalized