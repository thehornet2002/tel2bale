from db.model_async import reserve_download_quota, release_download_quota


async def check_and_update_quota(user_id: int, file_size_bytes: int | None) -> bool:
    """Atomic quota reservation avoiding race conditions during concurrent transfers."""
    return await reserve_download_quota(user_id, file_size_bytes)


async def rollback_quota(user_id: int, file_size_bytes: int | None) -> bool:
    """Roll back reserved download quota if transfer fails."""
    return await release_download_quota(user_id, file_size_bytes)
