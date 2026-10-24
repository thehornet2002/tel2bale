from db.model_async import (
    reserve_download_quota,
    release_download_quota,
    commit_download_quota,
    get_user_quota_info,
    reset_user_download_quota,
)


async def check_and_update_quota(user_id: int, file_size_bytes: int | None, reservation_id: str | None = None) -> bool:
    """Atomic quota reservation with optional idempotency reservation tracking."""
    return await reserve_download_quota(user_id, file_size_bytes, reservation_id=reservation_id)


async def rollback_quota(user_id: int, file_size_bytes: int | None, reservation_id: str | None = None) -> bool:
    """Idempotent quota rollback preventing double-refunds."""
    return await release_download_quota(user_id, file_size_bytes, reservation_id=reservation_id)


async def finalize_quota(reservation_id: str | None) -> bool:
    """Commit quota reservation so it cannot be rolled back."""
    return await commit_download_quota(reservation_id)


async def get_quota_details(user_id: int) -> dict:
    """Return user quota consumption and remaining allowance."""
    return await get_user_quota_info(user_id)


async def has_remaining_quota(user_id: int) -> bool:
    """Check if user has remaining download allowance."""
    info = await get_user_quota_info(user_id)
    if info["is_unlimited"]:
        return True
    return info["remaining_gb"] > 0
