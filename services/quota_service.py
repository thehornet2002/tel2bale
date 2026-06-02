from db.model_async import reserve_download_quota, release_download_quota


async def check_and_update_quota(user_id: int, file_size_bytes: int | None) -> bool:
    """
    بررسی اتمیک سهمیه کاربر و reserve کردن مصرف.

    این تابع دیگر SELECT و UPDATE جداگانه انجام نمی‌دهد؛ بنابراین اگر کاربر
    چند فایل را هم‌زمان بفرستد، مصرف دانلود به‌درستی و بدون race condition
    ثبت می‌شود.
    """
    return await reserve_download_quota(user_id, file_size_bytes)


async def rollback_quota(user_id: int, file_size_bytes: int | None) -> bool:
    """اگر انتقال بعد از reserve شدن سهمیه شکست خورد، مصرف را برمی‌گرداند."""
    return await release_download_quota(user_id, file_size_bytes)
