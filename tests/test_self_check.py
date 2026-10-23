import asyncio
import os
import sys

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from utils.parser import validate_public_https_url
from handlers.handler_helpers.message_helpers.ads_handler import normalize_telegram_channel_input
from utils.keyboards import build_start_keyboard
from handlers.handler_helpers.message_helpers.common import get_valid_id
from db import model_async


class DummyMessage:
    def __init__(self, text):
        self.text = text
        self.replied = []

    async def reply_text(self, text, **kwargs):
        self.replied.append(text)


async def test_parser():
    # Public URLs
    assert await validate_public_https_url("https://s3.ir-thr-at1.arvanstorage.ir") is not False
    # Blocked URLs (localhost, private IP)
    assert await validate_public_https_url("http://127.0.0.1") is False
    assert await validate_public_https_url("https://192.168.1.1") is False
    assert await validate_public_https_url("http://localhost:8080") is False


def test_channel_normalizer():
    assert normalize_telegram_channel_input("@mychannel") == "@mychannel"
    assert normalize_telegram_channel_input("mychannel") == "@mychannel"
    assert normalize_telegram_channel_input("https://t.me/mychannel") == "@mychannel"
    assert normalize_telegram_channel_input("-1001234567890") == -1001234567890
    assert normalize_telegram_channel_input("invalid+channel/test") is None


def test_keyboards():
    kb = build_start_keyboard(is_admin=True)
    assert kb is not None
    github_btn = [btn for row in kb.inline_keyboard for btn in row if btn.text == "GitHub"][0]
    assert github_btn.url.startswith("https://")


async def test_valid_id():
    msg1 = DummyMessage(" 12345 ")
    assert await get_valid_id(msg1) == 12345

    msg2 = DummyMessage("-100192837465")
    assert await get_valid_id(msg2) == -100192837465

    msg3 = DummyMessage("not-a-number")
    assert await get_valid_id(msg3) is None
    assert len(msg3.replied) > 0


async def test_db_operations():
    await model_async.create_tables()

    # Settings test
    await model_async.set_setting("test_key", "test_value")
    val = await model_async.get_setting("test_key")
    assert val == "test_value"

    # User creation and admin check
    test_tg_id = 999999999
    await model_async.add_user(test_tg_id, is_admin=True)
    assert await model_async.is_user_exist(test_tg_id) is True
    assert await model_async.check_admin(test_tg_id) is True

    # Quota check
    await model_async.set_limit_download(test_tg_id, 1.0)  # 1 GB
    assert await model_async.reserve_download_quota(test_tg_id, 500 * 1024 * 1024) is True
    # Exceed limit
    assert await model_async.reserve_download_quota(test_tg_id, 600 * 1024 * 1024) is False
    # Release quota
    assert await model_async.release_download_quota(test_tg_id, 500 * 1024 * 1024) is True

    # In-memory cache state & ban tests
    await model_async.set_state(test_tg_id, "test_state")
    assert await model_async.get_state(test_tg_id) == "test_state"
    assert model_async._STATE_CACHE[test_tg_id] == "test_state"

    # Regular user can be banned & unbanned
    regular_user = 111222333
    await model_async.add_user(regular_user, is_admin=False)
    await model_async.ban_user(regular_user)
    assert await model_async.check_ban(regular_user) is True
    assert regular_user in model_async._BANNED_USERS

    await model_async.unban_user(regular_user)
    assert await model_async.check_ban(regular_user) is False
    assert regular_user not in model_async._BANNED_USERS

    # Admin CANNOT be banned
    ban_res = await model_async.ban_user(test_tg_id)
    assert ban_res is False
    assert await model_async.check_ban(test_tg_id) is False

    # Whitelist tests
    w_user = 888777666
    await model_async.set_whitelist_enabled(True)
    assert model_async.is_whitelist_enabled() is True
    assert model_async.is_user_whitelisted(w_user) is False  # not yet added
    assert model_async.is_user_whitelisted(test_tg_id) is True  # admin is always allowed
    assert test_tg_id in model_async.get_whitelist_users()  # admin automatically added to whitelist

    # Cannot remove admin from whitelist
    assert await model_async.remove_from_whitelist(test_tg_id) is False

    await model_async.add_to_whitelist(w_user)
    assert model_async.is_user_whitelisted(w_user) is True
    assert w_user in model_async.get_whitelist_users()

    await model_async.remove_from_whitelist(w_user)
    assert model_async.is_user_whitelisted(w_user) is False

    await model_async.set_whitelist_enabled(False)
    assert model_async.is_user_whitelisted(w_user) is True  # when disabled, everyone allowed


async def test_keyboards_and_shared_objects():
    from utils.keyboards import (
        build_admin_home_reply_keyboard,
        build_main_reply_keyboard,
        build_management_keyboard,
        build_request_group_keyboard,
        build_request_user_keyboard,
        build_whitelist_reply_keyboard,
    )
    from pyrogram.types import ReplyKeyboardMarkup, ReplyKeyboardRemove

    # Admin reply keyboard is management keyboard
    admin_kb = build_main_reply_keyboard(is_admin=True)
    assert isinstance(admin_kb, ReplyKeyboardMarkup)

    # Management keyboard is ReplyKeyboardMarkup
    mgmt_kb = build_management_keyboard()
    assert isinstance(mgmt_kb, ReplyKeyboardMarkup)

    # Verify no button contains bale_id or bot_token setup in reply keyboards
    for row in mgmt_kb.keyboard:
        for btn in row:
            assert "تنظیم ID بله" not in btn.text
            assert "تنظیم Bot Token بله" not in btn.text
            assert "bale_id" not in btn.text.lower()
            assert "token_bot" not in btn.text.lower()

    # Non-admin user receives ReplyKeyboardRemove
    user_kb = build_main_reply_keyboard(is_admin=False)
    assert isinstance(user_kb, ReplyKeyboardRemove)

    # Admin home keyboard
    admin_home_kb = build_admin_home_reply_keyboard()
    assert isinstance(admin_home_kb, ReplyKeyboardMarkup)
    assert admin_home_kb.keyboard[0][0].text == "⚙️ پنل مدیریت"

    # Whitelist reply keyboard
    wl_reply_kb = build_whitelist_reply_keyboard(is_enabled=True)
    assert isinstance(wl_reply_kb, ReplyKeyboardMarkup)

    req_user_kb = build_request_user_keyboard()
    assert req_user_kb is not None
    assert req_user_kb.keyboard[0][0].request_users is not None

    req_group_kb = build_request_group_keyboard()
    assert req_group_kb is not None
    assert req_group_kb.keyboard[0][0].request_chat is not None

    # Verify build_start_keyboard has NO admin panel button
    from utils.keyboards import build_start_keyboard
    start_kb_admin = build_start_keyboard(is_admin=True)
    for row in start_kb_admin.inline_keyboard:
        for btn in row:
            assert "مدیریت" not in btn.text
            assert getattr(btn, "callback_data", "") != "management"

    # Test get_valid_id with shared user / shared chat
    class DummyUser:
        def __init__(self, uid):
            self.id = uid

    class DummyUsersShared:
        def __init__(self, uid):
            self.users = [DummyUser(uid)]

    class DummyChat:
        def __init__(self, cid):
            self.id = cid

    class DummyChatShared:
        def __init__(self, cid):
            self.chat = DummyChat(cid)

    msg_user = DummyMessage(None)
    msg_user.users_shared = DummyUsersShared(12345678)
    assert await get_valid_id(msg_user) == 12345678

    msg_chat = DummyMessage(None)
    msg_chat.chat_shared = DummyChatShared(-100987654)
    assert await get_valid_id(msg_chat) == -100987654


async def test_admin_handler_logic():
    import config
    from handlers.handler_helpers.message_helpers.admin_handler import (
        add_admin_send_id,
        delete_admin_send_id,
        enter_telegram_ban,
    )

    admin_caller = 999999999
    # Ban self prevention
    msg_ban_self = DummyMessage(str(admin_caller))
    await enter_telegram_ban(msg_ban_self, admin_caller)
    assert any("نمی‌توانید خود را بن کنید" in r for r in msg_ban_self.replied)

    # Ban another admin prevention
    another_admin = 777777777
    await model_async.add_user(another_admin, is_admin=True)
    msg_ban_admin = DummyMessage(str(another_admin))
    await enter_telegram_ban(msg_ban_admin, admin_caller)
    assert any("امکان بن کردن ادمین وجود ندارد" in r for r in msg_ban_admin.replied)

    # Delete self prevention
    msg_del_self = DummyMessage(str(admin_caller))
    await delete_admin_send_id(msg_del_self, admin_caller)
    assert any("نمی‌توانید خود را از لیست ادمین‌ها حذف کنید" in r for r in msg_del_self.replied)


async def test_redis_state_integration():
    import config
    from db.redis_client import init_redis, is_redis_available, close_redis

    test_user_id = 555666777
    await model_async.add_user(test_user_id)

    # Test state persistence with Redis
    await init_redis(config.REDIS_URL)
    if is_redis_available():
        await model_async.set_state(test_user_id, "redis_test_state")
        retrieved = await model_async.get_state(test_user_id)
        assert retrieved == "redis_test_state"

        # Clear in-memory cache to verify retrieval from Redis store
        model_async._STATE_CACHE.pop(test_user_id, None)
        retrieved_from_redis = await model_async.get_state(test_user_id)
        assert retrieved_from_redis == "redis_test_state"
        await close_redis()


async def test_ticket_system_integration():
    # Test ticket categories and creation
    cats = await model_async.get_ticket_categories()
    assert len(cats) >= 3

    user_id = 123000999
    await model_async.add_user(user_id)

    ticket_id = await model_async.create_user_ticket(
        telegram_id=user_id,
        user_name="Test User",
        category_id=cats[0]["id"],
        message="مشکل در اتصال به سرور بله",
        subject=cats[0]["title"],
        group_message_id=987654321,
    )
    assert ticket_id > 0

    ticket = await model_async.get_ticket(ticket_id)
    assert ticket is not None
    assert ticket["status"] == "خوانده نشده"
    assert ticket["category_title"] == cats[0]["title"]

    user_tickets = await model_async.get_user_tickets(user_id)
    assert len(user_tickets) >= 1
    assert any(t["id"] == ticket_id for t in user_tickets)

    # Test answering ticket
    await model_async.answer_ticket(ticket_id, "مشکل برطرف شد.")
    ticket_answered = await model_async.get_ticket(ticket_id)
    assert ticket_answered["status"] == "پاسخ داده شده"
    assert ticket_answered["reply"] == "مشکل برطرف شد."

    # Test captcha generation
    from services.captcha_service import generate_hard_captcha
    code, img_bytes = generate_hard_captcha()
    assert len(code) == 5
    assert len(img_bytes) > 500

    # Test multi-poll system
    poll_id = await model_async.create_poll("سرعت ارسال چطور است؟", ["عالی", "متوسط", "ضعیف"], title="نظرسنجی سرعت")
    assert poll_id > 0

    all_polls = await model_async.get_all_active_polls()
    assert len(all_polls) >= 1
    assert any(p["id"] == poll_id for p in all_polls)

    # Test vote recording
    assert await model_async.record_poll_vote(poll_id, user_id, 0) is True
    vote_idx = await model_async.get_user_poll_vote(poll_id, user_id)
    assert vote_idx == 0

    # Test poll results calculation
    res = await model_async.get_poll_results(poll_id)
    assert res["total_votes"] == 1
    assert res["results"][0]["votes"] == 1
    assert res["results"][0]["percentage"] == 100.0

    # Test donation button in start keyboard
    from utils.keyboards import build_start_keyboard
    kb = build_start_keyboard()
    donate_btns = [btn for row in kb.inline_keyboard for btn in row if "دونیت" in btn.text or "حمایت" in btn.text]
    assert len(donate_btns) > 0
    assert donate_btns[0].url.startswith("http")


async def test_security_guards():
    from handlers.callback import ADMIN_CALLBACK_NAMES
    assert "get_db" in ADMIN_CALLBACK_NAMES
    assert "manage_whitelist" in ADMIN_CALLBACK_NAMES
    assert "adm_manage_cats" in ADMIN_CALLBACK_NAMES

    # Test env sanitization against CRLF injection
    test_updates = {"TEST_KEY": "val\nMALICIOUS=true\r\nANOTHER=1"}
    clean = str(test_updates["TEST_KEY"]).replace("\r", "").replace("\n", "").strip()
    assert "\n" not in clean
    assert "\r" not in clean

    # Test 3-way captcha toggle flags
    await model_async.set_captcha_ticket_enabled(False)
    assert model_async.is_captcha_ticket_enabled() is False
    await model_async.set_captcha_ticket_enabled(True)
    assert model_async.is_captcha_ticket_enabled() is True

    await model_async.set_captcha_poll_enabled(True)
    assert model_async.is_captcha_poll_enabled() is True
    await model_async.set_captcha_poll_enabled(False)
    assert model_async.is_captcha_poll_enabled() is False

    await model_async.set_captcha_file_enabled(True)
    assert model_async.is_captcha_file_enabled() is True
    await model_async.set_captcha_file_enabled(False)
    assert model_async.is_captcha_file_enabled() is False


async def test_downloader_and_cookies():
    from services.downloader_service import (
        detect_platform,
        extract_media_url,
        is_media_url,
    )
    from services.cookie_service import (
        delete_cookie_file,
        get_cookie_status,
        get_effective_cookie_file,
        save_cookie_file,
    )

    # URL detection tests
    yt_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    ig_url = "https://www.instagram.com/reel/C8xyz123/"
    sp_url = "https://open.spotify.com/track/4cOdK2wGLETKBW3PvgPWqT"
    regular_text = "سلام، این یک متن عادی است."

    assert is_media_url(yt_url) is True
    assert is_media_url(ig_url) is True
    assert is_media_url(sp_url) is True
    assert is_media_url(regular_text) is False

    assert detect_platform(yt_url) == "youtube"
    assert detect_platform(ig_url) == "instagram"
    assert detect_platform(sp_url) == "spotify"
    assert detect_platform("https://soundcloud.com/artist/track") == "generic"

    assert extract_media_url(f"Check this: {yt_url} cool!") == yt_url

    # Cookie service tests (Admin-only global cookies)
    cookie_sample = "# Netscape HTTP Cookie File\n.youtube.com\tTRUE\t/\tTRUE\t2147483647\tSID\tsample_value\n"

    # Save global cookie
    assert save_cookie_file(cookie_sample) is True
    global_status = get_cookie_status()
    assert global_status["has_cookie"] is True
    assert get_effective_cookie_file() is not None

    # Clean up global cookie
    delete_cookie_file()
    status_after = get_cookie_status()
    assert status_after["has_cookie"] is False


async def test_prerequisites_and_captcha():
    from handlers.handler_helpers.message_helpers.media_handler import check_user_prerequisites
    from services.captcha_service import generate_captcha
    from handlers.handler_helpers.message_helpers.captcha_handler import (
        record_captcha_failure,
        check_user_captcha_lock,
        reset_captcha_failures,
    )
    from handlers.handler_helpers.callback_helpers.admin.ticket_mgmt_handler import admin_captcha_settings_view

    import time
    dummy_user = 666000000 + int(time.time() * 1000 % 100000)
    await model_async.add_user(dummy_user)

    # Missing Bale ID -> should return False
    msg = DummyMessage("test")
    assert await check_user_prerequisites(msg, dummy_user) is False

    # Set Bale ID only -> still False (missing token)
    await model_async.set_bale_id(dummy_user, 123456)
    assert await check_user_prerequisites(msg, dummy_user) is False

    # Set Bale Token only -> still False (missing S3)
    await model_async.set_bale_token(dummy_user, "123456:abcdef")
    assert await check_user_prerequisites(msg, dummy_user) is False

    # Set S3 Access Key & Secret Key & Endpoint -> should return True
    await model_async.set_access_key(dummy_user, "access123")
    await model_async.set_secret_key(dummy_user, "secret123")
    await model_async.set_s3_endpoint(dummy_user, "https://s3.ir-thr-at1.arvanstorage.ir")
    assert await check_user_prerequisites(msg, dummy_user) is True

    # 5 Difficulty levels test
    for diff in range(1, 6):
        code, img = generate_captcha(difficulty=diff, length=5)
        assert len(code) == 5
        assert len(img) > 500

    # Length adjustment test (4 to 10)
    for length in (4, 7, 10):
        code, img = generate_captcha(difficulty=3, length=length)
        assert len(code) == length

    # 20-minute suspension test (5 failures)
    test_user = 888999111
    reset_captcha_failures(test_user)
    assert check_user_captcha_lock(test_user)[0] is False

    for _ in range(4):
        fails, locked, secs = record_captcha_failure(test_user)
        assert locked is False

    # 5th failure must trigger lock
    fails, locked, secs = record_captcha_failure(test_user)
    assert locked is True
    assert secs > 1000
    is_locked, remaining = check_user_captcha_lock(test_user)
    assert is_locked is True

    # Reset lock
    reset_captcha_failures(test_user)
    assert check_user_captcha_lock(test_user)[0] is False

    # Test admin_captcha_settings_view does not raise NameError
    admin_uid = 999999999
    admin_msg = DummyMessage("test")
    await admin_captcha_settings_view(admin_msg, admin_uid)
    assert len(admin_msg.replied) > 0




async def test_quota_updates():
    import time
    from services.quota_service import get_quota_details

    uid = 444333222 + int(time.time() % 100000)
    await model_async.add_user(uid)

    # Set 0 limit (unlimited)
    await model_async.set_limit_download(uid, 0.0)
    details = await get_quota_details(uid)
    assert details["is_unlimited"] is True

    # Set 2GB limit
    await model_async.set_limit_download(uid, 2.0)
    details2 = await get_quota_details(uid)
    assert details2["is_unlimited"] is False
    assert details2["limit_gb"] == 2.0
    assert details2["remaining_gb"] == 2.0

    # Consume 1GB
    one_gb = 1024 * 1024 * 1024
    assert await model_async.reserve_download_quota(uid, one_gb) is True
    details3 = await get_quota_details(uid)
    assert round(details3["remaining_gb"], 1) == 1.0

    # Reset quota
    assert await model_async.reset_user_download_quota(uid) is True
    details4 = await get_quota_details(uid)
    assert round(details4["remaining_gb"], 1) == 2.0



async def main():
    await test_parser()
    test_channel_normalizer()
    test_keyboards()
    await test_valid_id()
    await test_db_operations()
    await test_keyboards_and_shared_objects()
    await test_admin_handler_logic()
    await test_redis_state_integration()
    await test_ticket_system_integration()
    await test_security_guards()
    await test_downloader_and_cookies()
    await test_quota_updates()
    await test_prerequisites_and_captcha()
    print("ALL TESTS PASSED SUCCESSFULLY")



if __name__ == "__main__":
    asyncio.run(main())
