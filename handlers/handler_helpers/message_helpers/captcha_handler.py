"""
مدیریت چالش کپچا امنیتی پیشرفته قبل از ارسال تیکت (الگوبرداری از Senfi)
"""
import io
import time
from pyrogram.types import Message
from db import model_async
from services.captcha_service import generate_hard_captcha
from utils.keyboards import build_captcha_keyboard, build_back_keyboard

_CAPTCHA_STORE: dict[int, dict] = {}
_PENDING_FILE_MESSAGES: dict[int, Message] = {}


def set_pending_file_message(user_id: int, message: Message) -> None:
    _PENDING_FILE_MESSAGES[user_id] = message


def get_pending_file_message(user_id: int) -> Message | None:
    return _PENDING_FILE_MESSAGES.get(user_id)


def clear_pending_file_message(user_id: int) -> None:
    _PENDING_FILE_MESSAGES.pop(user_id, None)


def _cleanup_captcha_store() -> None:
    now = time.time()
    expired = [uid for uid, item in _CAPTCHA_STORE.items() if now - item.get("created_at", 0) > 600]
    for uid in expired:
        _CAPTCHA_STORE.pop(uid, None)
        _PENDING_FILE_MESSAGES.pop(uid, None)
    if len(_CAPTCHA_STORE) > 1000:
        oldest = sorted(_CAPTCHA_STORE.items(), key=lambda x: x[1].get("created_at", 0))[:500]
        for uid, _ in oldest:
            _CAPTCHA_STORE.pop(uid, None)
            _PENDING_FILE_MESSAGES.pop(uid, None)


async def issue_captcha(message: Message, user_id: int, tag: str | int, refreshes_left: int = 3) -> None:
    _cleanup_captcha_store()
    code, img_bytes = generate_hard_captcha()
    _CAPTCHA_STORE[user_id] = {
        "code": code,
        "tag": str(tag),
        "refreshes_left": refreshes_left,
        "created_at": time.time(),
        "attempts": 0,
    }
    await model_async.set_state(user_id, f"captcha_verify_{tag}")

    caption = (
        "🔒 **کد امنیتی تایید هویت**\n\n"
        "جهت جلوگیری از ارسال هرزنامه، لطفاً ۵ کاراکتر داخل تصویر را به صورت انگلیسی ارسال کنید:\n"
        "*(حروف بزرگ/کوچک فرقی ندارد - مهلت ورود: ۵ دقیقه)*"
    )
    bio = io.BytesIO(img_bytes)
    bio.name = "captcha.png"
    await message.reply_photo(
        photo=bio,
        caption=caption,
        reply_markup=build_captcha_keyboard(refreshes_left)
    )


async def refresh_captcha_handler(message: Message, user_id: int) -> None:
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
    data = _CAPTCHA_STORE.get(user_id)
    if not data:
        await message.reply_text("نشست کپچا منقضی شده است. لطفاً دوباره تلاش کنید.", reply_markup=build_back_keyboard())
        await model_async.set_state(user_id, "home")
        return False

    if time.time() - data["created_at"] > 300:
        await message.reply_text("⏳ مهلت ۵ دقیقه‌ای شما برای حل کد امنیتی به پایان رسیده است. لطفاً کد جدید زیر را وارد کنید:")
        await issue_captcha(message, user_id, data["tag"], refreshes_left=data["refreshes_left"])
        return False

    expected = data["code"]
    if answer.strip().upper() == expected.upper():
        _CAPTCHA_STORE.pop(user_id, None)
        return True

    data["attempts"] += 1
    if data["attempts"] >= 3:
        await message.reply_text("⚠️ تعداد تلاش‌های ناموفق شما تکمیل شد. تصویر جدید تولید شد:")
        refreshes = max(0, data["refreshes_left"] - 1)
        await issue_captcha(message, user_id, data["tag"], refreshes_left=refreshes)
        return False

    await message.reply_text("❌ کد وارد شده اشتباه است. لطفاً دوباره با دقت وارد کنید:")
    return False
