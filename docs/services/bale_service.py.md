## نقش کلی فایل

- مدیریت `aiohttp.ClientSession` برای درخواست‌های HTTP
- اجرای درخواست‌های استاندارد به API بله با یک تابع مشترک (`_request`)
- ارسال پیام متنی و مدیاها به یک `chat_id`
- تولید نام فایل یکتا با `uuid` هنگام ارسال فایل‌ها
- پشتیبانی از proxy از طریق `config.BALE_PROXY_URL`

## ساختار اصلی
### `bale_bot = BaleService()`
یک نمونه آماده از کلاس `BaleService` می‌سازد تا بتوان در سایر بخش‌های پروژه مستقیم از آن استفاده کرد.

---

## کلاس BaleService

### `__init__(self)`
- `self.session` را `None` می‌کند تا در زمان نیاز، session ساخته شود.

## چرخه عمر اتصال

### `async start(self)`
- اگر session وجود نداشته باشد یا بسته شده باشد:
  - یک `aiohttp.ClientSession` با `timeout(total=100)` می‌سازد
- نتیجه: session برای ارسال درخواست‌ها آماده می‌شود.

### `async close(self)`
- اگر session باز باشد، آن را `await self.session.close()`
- نتیجه: منابع شبکه آزاد می‌شوند.

---

## تابع داخلی درخواست‌ها

### `async _request(self, bale_bot_token, endpoint, method="POST", **kwargs)`
این تابع موتور اصلی ارسال است و همه متدهای دیگر از آن استفاده می‌کنند.

- راه‌اندازی session:
  - در صورت نیاز `await self.start()` اجرا می‌شود.
- ساخت URL:
  - `https://tapi.bale.ai/bot{bale_bot_token}/{endpoint}`
- تنظیم proxy:
  - اگر `BALE_PROXY_URL` مقدار داشته باشد، `kwargs["proxy"]` ست می‌شود.
- ارسال درخواست:
  - `async with self.session.request(...) as resp:`
  - متن پاسخ را می‌خواند (`await resp.text()`)
- مدیریت خطاها:
  - اگر `resp.status != 200`:
    - خطا با `HTTP status` و متن پاسخ
  - اگر JSON قابل parse نباشد:
    - خطا با متن پاسخ
  - اگر `data["ok"]` برابر `False` باشد:
    - خطا با `data["description"]` یا پیام پیش‌فرض
  - اگر `aiohttp.ClientError` رخ دهد:
    - خطای ارتباطی با بله
- خروجی:
  - مقدار `data["result"]` را برمی‌گرداند.

---

## توابع ارسال پیام متنی

### `async send_message(self, bale_bot_token, chat_id, text)`
- endpoint: `sendMessage`
- payload JSON:
  - `chat_id`
  - `text`
- ارسال:
  - `return await self._request(..., "sendMessage", json=payload)`

---

## توابع ارسال مدیا (با multipart/form-data)

> در این توابع از `aiohttp.FormData()` استفاده می‌شود و برای هر فایل یک نام یکتا با `uuid.uuid4().hex` ساخته می‌شود تا برخورد نام فایل پیش نیاید.

### `async send_photo(self, bale_bot_token, chat_id, photo, caption: str | None = None)`
- endpoint: `sendPhoto`
- fieldها:
  - `chat_id`
  - `photo` با:
    - `filename = unique_name + ".jpg"`
    - `content_type = "image/jpeg"`
  - `caption` (اختیاری)
- ارسال:
  - `sendPhoto` با `data=data`

### `async send_video(self, bale_bot_token, chat_id, video, caption: str | None = None)`
- endpoint: `sendVideo`
- field فایل: `video`
- `filename = unique_name + ".mp4"`
- `content_type = "video/mp4"`
- `caption` (اختیاری)

### `async send_audio(self, bale_bot_token, chat_id, audio, caption: str | None = None)`
- endpoint: `sendAudio`
- field فایل: `audio`
- `filename = unique_name + ".mp3"`
- `content_type = "audio/mpeg"`
- `caption` (اختیاری)

### `async send_voice(self, bale_bot_token, chat_id, voice, caption: str | None = None)`
- endpoint: `sendVoice`
- field فایل: `voice`
- `filename = unique_name + ".ogg"`
- `content_type = "audio/ogg"`
- `caption` (اختیاری)

### `async send_document(self, bale_bot_token, chat_id, document, filename: str, caption: str | None = None)`
- endpoint: `sendDocument`
- fieldها:
  - `chat_id`
  - `document` با:
    - `filename` دقیقاً همان ورودی `filename`
    - `content_type = "application/octet-stream"`
  - `caption` (اختیاری)

### `async send_animation(self, bale_bot_token, chat_id, animation, caption: str | None = None)`
- endpoint: `sendAnimation`
- field فایل: `animation`
- `filename = unique_name + ".gif"`
- در کد: `content_type = "video/mp4"`
- `caption` (اختیاری)

### `async send_video_note(self, bale_bot_token, chat_id, video_note)`
- endpoint: `sendVideoNote`
- field فایل: `video_note`
- `filename = unique_name + ".mp4"`
- `content_type = "video/mp4"`
- بدون caption

---

## توابع ارسال داده‌های ساختاریافته

### `async send_location(self, bale_bot_token, chat_id, latitude: float, longitude: float)`
- endpoint: `sendLocation`
- payload JSON:
  - `chat_id`
  - `latitude`
  - `longitude`
- ارسال:
  - `sendLocation` با `json=payload`

### `async send_contact(self, bale_bot_token, chat_id, phone_number: str, first_name: str, last_name: str = "")`
- endpoint: `sendContact`
- payload JSON:
  - `chat_id`
  - `phone_number`
  - `first_name = f"{first_name} {last_name}".strip()`
- ارسال:
  - `sendContact` با `json=payload`

---

## اعتبارسنجی توکن

### `async verify_token(self, bale_bot_token) -> bool`
- با فراخوانی:
  - `_request(bale_bot_token, "getMe", method="GET")`
- نتیجه:
  - اگر خطایی رخ ندهد: `True`
  - اگر هر خطایی رخ دهد: `False`

---