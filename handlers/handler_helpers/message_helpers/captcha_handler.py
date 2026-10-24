"""
Advanced anti-spam security captcha challenge handler.
Supports 5 difficulty levels, custom lengths (4-10), and 20-minute lockouts for 5 failed attempts or expirations.
"""
import io
import time
from pyrogram.types import Message
from db import model_async
from services.captcha_service import generate_captcha
from utils.keyboards import build_captcha_keyboard, build_back_keyboard

_CAPTCHA_STORE: dict[int, dict] = {}
_PENDING_FILE_MESSAGES: dict[int, Message] = {}

# Failure and suspension tracking
_USER_CAPTCHA_FAILS: dict[int, int] = {}
_USER_CAPTCHA_LOCKS: dict[int, float] = {}


def set_pending_file_message(user_id: int, message: Message) -> None:
    _PENDING_FILE_MESSAGES[user_id] = message


def get_pending_file_message(user_id: int) -> Message | None:
    return _PENDING_FILE_MESSAGES.get(user_id)


def clear_pending_file_message(user_id: int) -> None:
    _PENDING_FILE_MESSAGES.pop(user_id, None)


def check_user_captcha_lock(user_id: int) -> tuple[bool, int]:
    """
    Check if user is currently suspended from captcha attempts.
    Returns: (is_locked: bool, remaining_seconds: int)
    """
    now = time.time()
    lock_until = _USER_CAPTCHA_LOCKS.get(user_id, 0)
    if lock_until > now:
        return True, int(lock_until - now)

    if user_id in _USER_CAPTCHA_LOCKS:
        _USER_CAPTCHA_LOCKS.pop(user_id, None)
        _USER_CAPTCHA_FAILS[user_id] = 0
    return False, 0


def record_captcha_failure(user_id: int) -> tuple[int, bool, int]:
    """
    Increment failure count (wrong answers or expired captchas).
    If total fails reach 5, locks user out for 20 minutes (1200s).
    Returns: (current_fails: int, is_locked: bool, remaining_seconds: int)
    """
    fails = _USER_CAPTCHA_FAILS.get(user_id, 0) + 1
    _USER_CAPTCHA_FAILS[user_id] = fails

    if fails >= 5:
        lock_until = time.time() + 1200
        _USER_CAPTCHA_LOCKS[user_id] = lock_until
        _USER_CAPTCHA_FAILS[user_id] = 0
        return fails, True, 1200

    return fails, False, 0


def reset_captcha_failures(user_id: int) -> None:
    """Reset failure counter upon successful verification."""
    _USER_CAPTCHA_FAILS[user_id] = 0
    _USER_CAPTCHA_LOCKS.pop(user_id, None)


def _cleanup_captcha_store() -> None:
    now = time.time()
    expired = [
        uid for uid, item in _CAPTCHA_STORE.items()
        if now - item.get("created_at", 0) > 300
    ]
    for uid in expired:
        _CAPTCHA_STORE.pop(uid, None)
        _PENDING_FILE_MESSAGES.pop(uid, None)
        # Expired without answering counts as a failure
        record_captcha_failure(uid)

    if len(_CAPTCHA_STORE) > 1000:
        oldest = sorted(_CAPTCHA_STORE.items(), key=lambda x: x[1].get("created_at", 0))[:500]
        for uid, _ in oldest:
            _CAPTCHA_STORE.pop(uid, None)
            _PENDING_FILE_MESSAGES.pop(uid, None)


async def issue_captcha(message: Message, user_id: int, tag: str | int, refreshes_left: int = 3) -> None:
    # 1. Check if user is currently locked for 20 minutes
    is_locked, remaining_secs = check_user_captcha_lock(user_id)
    if is_locked:
        mins = remaining_secs // 60
        secs = remaining_secs % 60
        await model_async.set_state(user_id, "home")
        await message.reply_text(
            "⛔️ **دسترسی شما موقتاً مسدود شده است!**\n\n"
            "به دلیل ۵ بار تلاش ناموفق یا انقضای کد امنیتی، حساب شما به مدت ۲۰ دقیقه قفل شده است.\n\n"
            f"⏳ زمان باقیمانده تا رفع مسدودیت: **{mins:02d}:{secs:02d}**",
            reply_markup=build_back_keyboard()
        )
        return

    _cleanup_captcha_store()

    # Load dynamic difficulty & length from settings
    difficulty = model_async.get_captcha_difficulty()
    length = model_async.get_captcha_length()

    code, img_bytes = generate_captcha(difficulty=difficulty, length=length)

    _CAPTCHA_STORE[user_id] = {
        "code": code,
        "tag": str(tag),
        "refreshes_left": refreshes_left,
        "created_at": time.time(),
        "attempts": 0,
    }
    await model_async.set_state(user_id, f"captcha_verify_{tag}")

    fails = _USER_CAPTCHA_FAILS.get(user_id, 0)
    warning_str = f"\n⚠️ خطاهای ثبت‌شده: {fails} از ۵ (در صورت رسیدن به ۵، ۲۰ دقیقه مسدود می‌شوید)" if fails > 0 else ""

    caption = (
        "🔒 **کد امنیتی تایید هویت**\n\n"
        f"جهت جلوگیری از ارسال هرزنامه، لطفاً **{length}** کاراکتر داخل تصویر را به صورت انگلیسی ارسال کنید:\n"
        "*(حروف بزرگ/کوچک فرقی ندارد - مهلت ورود: ۵ دقیقه)*"
        f"{warning_str}"
    )
    bio = io.BytesIO(img_bytes)
    bio.name = "captcha.png"
    client = getattr(message, "_client", None)
    chat_id = getattr(getattr(message, "chat", None), "id", user_id) or user_id

    try:
        if client:
            await client.send_photo(
                chat_id=chat_id,
                photo=bio,
                caption=caption,
                reply_markup=build_captcha_keyboard(refreshes_left)
            )
        else:
            await message.reply_photo(
                photo=bio,
                caption=caption,
                reply_markup=build_captcha_keyboard(refreshes_left)
            )
    except Exception as e:
        logger.warning(f"[CAPTCHA] Failed to send captcha photo: {e}")
        try:
            await message.reply_photo(
                photo=bio,
                caption=caption,
                reply_markup=build_captcha_keyboard(refreshes_left)
            )
        except Exception as e2:
            logger.error(f"[CAPTCHA] Fallback reply_photo also failed: {e2}")


async def refresh_captcha_handler(message: Message, user_id: int) -> None:
    is_locked, remaining_secs = check_user_captcha_lock(user_id)
    if is_locked:
        mins = remaining_secs // 60
        secs = remaining_secs % 60
        await message.reply_text(
            f"⛔️ حساب شما مسدود است. لطفاً {mins} دقیقه و {secs} ثانیه دیگر مجدداً تلاش فرمایید.",
            reply_markup=build_back_keyboard()
        )
        return

    data = _CAPTCHA_STORE.get(user_id)
    if not data:
        await message.reply_text("نشست امنیتی منقضی شده است. لطفاً مجدداً اقدام کنید.", reply_markup=build_back_keyboard())
        return

    refreshes = data.get("refreshes_left", 3) - 1
    if refreshes < 0:
        await message.reply_text("⛔️ سقف مجاز دریافت تصویر امنیتی جدید به پایان رسید.", reply_markup=build_back_keyboard())
        return

    tag = data.get("tag", "default")
    await issue_captcha(message, user_id, tag, refreshes_left=refreshes)


async def verify_captcha_answer(message: Message, user_id: int, answer: str) -> bool:
    is_locked, remaining_secs = check_user_captcha_lock(user_id)
    if is_locked:
        mins = remaining_secs // 60
        secs = remaining_secs % 60
        await model_async.set_state(user_id, "home")
        await message.reply_text(
            "⛔️ **دسترسی مسدود است!**\n"
            f"به دلیل ۵ خطای متوالی، باید {mins} دقیقه و {secs} ثانیه دیگر صبر کنید.",
            reply_markup=build_back_keyboard()
        )
        return False

    data = _CAPTCHA_STORE.get(user_id)
    if not data:
        await message.reply_text("نشست کپچا منقضی شده است. لطفاً دوباره تلاش کنید.", reply_markup=build_back_keyboard())
        await model_async.set_state(user_id, "home")
        return False

    # Check timeout (5 minutes)
    if time.time() - data["created_at"] > 300:
        _CAPTCHA_STORE.pop(user_id, None)
        fails, locked, secs = record_captcha_failure(user_id)
        if locked:
            await model_async.set_state(user_id, "home")
            await message.reply_text(
                "⛔️ **مهلت پاسخ منقضی شد و به سقف ۵ خطای مجاز رسیدید!**\n\n"
                "حساب شما به مدت ۲۰ دقیقه مسدود شد.",
                reply_markup=build_back_keyboard()
            )
            return False

        await message.reply_text(
            f"⏳ مهلت ۵ دقیقه‌ای شما برای حل کد امنیتی به پایان رسید (خطای {fails} از ۵).\n"
            "تصویر جدید زیر تولید شد:"
        )
        await issue_captcha(message, user_id, data["tag"], refreshes_left=data["refreshes_left"])
        return False

    expected = data["code"]
    if answer.strip().upper() == expected.upper():
        _CAPTCHA_STORE.pop(user_id, None)
        reset_captcha_failures(user_id)
        return True

    # Incorrect answer
    data["attempts"] += 1
    fails, locked, secs = record_captcha_failure(user_id)

    if locked:
        _CAPTCHA_STORE.pop(user_id, None)
        await model_async.set_state(user_id, "home")
        await message.reply_text(
            "⛔️ **۵ بار پاسخ اشتباه وارد شد!**\n\n"
            "به دلیل نقض تدابیر امنیتی ضد اسپم، حساب شما به مدت **۲۰ دقیقه** مسدود گردید.\n"
            "پس از پایان این زمان می‌توانید مجدداً اقدام فرمایید.",
            reply_markup=build_back_keyboard()
        )
        return False

    if data["attempts"] >= 3:
        await message.reply_text(
            f"⚠️ تعداد تلاش‌های این تصویر تکمیل شد (خطای کل: {fails} از ۵).\n"
            "تصویر جدیدی برای شما تولید شد:"
        )
        refreshes = max(0, data["refreshes_left"] - 1)
        await issue_captcha(message, user_id, data["tag"], refreshes_left=refreshes)
        return False

    await message.reply_text(
        f"❌ کد وارد شده اشتباه است (خطای کل: {fails} از ۵).\n"
        "لطفاً دوباره با دقت کاراکترهای تصویر را وارد کنید:"
    )
    return False
