from db.model_async import get_downloaded_volume, get_limit_download, set_downloaded_volume




async def check_and_update_quota(user_id: int, file_size_bytes: int) -> bool:
    """
    بررسی می‌کند که آیا کاربر حجم مجاز برای ارسال این فایل را دارد یا خیر.
    اگر حجم داشت، دیتابیس را آپدیت کرده و True برمی‌گرداند.
    """
    if file_size_bytes == 0 or file_size_bytes is None:
        return True

    file_size_gb = file_size_bytes / (1024 ** 3)
    downloaded_volume = await get_downloaded_volume(user_id)
    limit_download = await get_limit_download(user_id)

    # اگر کاربر محدودیت دارد (صفر نیست) و از حجم مجاز عبور کرده است
    if limit_download != 0 and (downloaded_volume + file_size_gb) > limit_download:
        return False

    # آپدیت حجم مصرفی در دیتابیس
    await set_downloaded_volume(user_id, downloaded_volume + file_size_gb)
    return True