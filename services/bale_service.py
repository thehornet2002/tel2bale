import asyncio
import aiohttp
import inspect
import uuid

from config import BALE_PROXY_URL


# تایم‌اوت درخواست‌های سبک (متن، لوکیشن، مخاطب و ...)
LIGHT_TIMEOUT = aiohttp.ClientTimeout(
    total=30,
    connect=10,
)

# تایم‌اوت درخواست‌های سنگین (عکس/ویدیو/صدا/فایل/انیمیشن/ویدیونوت)
# total را بسیار بزرگ می‌گذاریم تا آپلود فایل‌های حجیم روی اینترنت کند هم
# به‌خاطر timeout قطع نشود (که علت اصلی «ارسال ناقص» بود).
MEDIA_TIMEOUT = aiohttp.ClientTimeout(
    total=600,          # حداکثر ۱۰ دقیقه برای کل عملیات آپلود
    connect=15,          # اتصال اولیه باید سریع برقرار شود
    sock_read=120,        # بین دو بسته‌ی داده حداکثر این‌قدر صبر کن
)

# خطاهایی که موقتی و قابل تلاش‌مجدد هستند
RETRYABLE_EXCEPTIONS = (
    aiohttp.ClientPayloadError,
    aiohttp.ClientConnectionError,
    aiohttp.ServerDisconnectedError,
    aiohttp.ServerTimeoutError,
    asyncio.TimeoutError,
)

MAX_RETRIES = 3
RETRY_BACKOFF_BASE = 1.5  # ثانیه


class BaleService:
    def __init__(self):
        self.session = None

    async def start(self):
        if not self.session or self.session.closed:
            # timeout پیش‌فرض سشن را روی حالت سبک می‌گذاریم،
            # و برای درخواست‌های رسانه‌ای در هر فراخوانی override می‌کنیم.
            connector = aiohttp.TCPConnector(
                limit=50,
                ttl_dns_cache=300,
                enable_cleanup_closed=True,
            )
            self.session = aiohttp.ClientSession(
                timeout=LIGHT_TIMEOUT,
                connector=connector,
            )

    async def close(self):
        if self.session and not self.session.closed:
            await self.session.close()

    @staticmethod
    async def _to_bytes(file_obj) -> bytes:
        """
        هر ورودی (bytes، file-like با read()، async file-like، یا مسیر) را
        به bytes کامل تبدیل می‌کند.

        این مرحله بسیار مهم است: اگر یک file handle یا BytesIO قبلاً
        (مثلاً برای بررسی حجم) خوانده شده باشد، pointer آن روی انتها مانده
        و بدون این تبدیل، محتوای ارسالی به بله خالی یا ناقص می‌شود.
        همچنین با تبدیل کامل به bytes، aiohttp از ابتدا طول دقیق فایل
        (Content-Length) را می‌داند و به‌جای chunked encoding نامطمئن،
        یک درخواست کامل و قابل‌اعتماد می‌سازد.
        """
        if file_obj is None:
            raise Exception("فایل ارسالی خالی است.")

        if isinstance(file_obj, (bytes, bytearray)):
            data = bytes(file_obj)

        elif isinstance(file_obj, str):
            # مسیر فایل روی دیسک
            with open(file_obj, "rb") as f:
                data = f.read()

        elif hasattr(file_obj, "read"):
            # اگر فایل seek پشتیبانی می‌کند، اول به ابتدای آن برگرد
            if hasattr(file_obj, "seek"):
                try:
                    seek_result = file_obj.seek(0)
                    if inspect.isawaitable(seek_result):
                        await seek_result
                except Exception:
                    pass  # بعضی استریم‌ها seek ندارند؛ ادامه می‌دهیم

            read_result = file_obj.read()
            if inspect.isawaitable(read_result):
                data = await read_result
            else:
                data = read_result

            if isinstance(data, str):
                data = data.encode("utf-8")
        else:
            raise Exception(
                "نوع ورودی فایل پشتیبانی نمی‌شود "
                "(باید bytes، مسیر فایل یا شیء دارای read باشد)."
            )

        if not data:
            raise Exception(
                "محتوای فایل خالی است؛ احتمالاً pointer فایل قبلاً "
                "خوانده و به انتها رسیده بوده است."
            )

        return data

    async def _request(
        self,
        bale_bot_token: str,
        endpoint: str,
        method: str = "POST",
        is_media: bool = False,
        **kwargs
    ):
        if not self.session or self.session.closed:
            await self.start()

        url = f"https://tapi.bale.ai/bot{bale_bot_token}/{endpoint}"

        if BALE_PROXY_URL:
            kwargs.setdefault("proxy", BALE_PROXY_URL)

        # برای درخواست‌های رسانه‌ای، تایم‌اوت طولانی‌تر را override می‌کنیم
        request_timeout = MEDIA_TIMEOUT if is_media else LIGHT_TIMEOUT

        last_error = None

        for attempt in range(1, MAX_RETRIES + 1):
            try:
                async with self.session.request(
                    method,
                    url,
                    timeout=request_timeout,
                    **kwargs
                ) as resp:
                    text = await resp.text()

                    if resp.status != 200:
                        raise Exception(
                            f"خطای ارتباط با بله (HTTP {resp.status})\n{text}"
                        )

                    try:
                        data = await resp.json()
                    except Exception:
                        raise Exception(
                            f"پاسخ نامعتبر از سرور بله:\n{text}"
                        )

                    if not data.get("ok", False):
                        raise Exception(
                            data.get(
                                "description",
                                "خطای ناشناخته از سمت بله"
                            )
                        )

                    return data.get("result")

            except RETRYABLE_EXCEPTIONS as e:
                last_error = e
                if attempt == MAX_RETRIES:
                    break
                # اگر FormData حاوی فایل bytes بود، در تلاش بعدی هم قابل
                # ارسال مجدد است چون یک بار برای همیشه در حافظه خوانده شده.
                await asyncio.sleep(RETRY_BACKOFF_BASE * attempt)
                continue

            except aiohttp.ClientError as e:
                raise Exception(f"خطا در اتصال به سرورهای بله:\n{e}")

        raise Exception(
            f"ارسال به بله پس از {MAX_RETRIES} تلاش ناموفق بود "
            f"(احتمالاً به‌دلیل قطعی یا کندی شبکه):\n{last_error}"
        )

    async def _build_media_form(
        self,
        chat_id: int,
        field_name: str,
        file_obj,
        filename: str,
        content_type: str,
        caption: str | None = None,
    ) -> aiohttp.FormData:
        file_bytes = await self._to_bytes(file_obj)

        data = aiohttp.FormData()
        data.add_field("chat_id", str(chat_id))
        data.add_field(
            field_name,
            file_bytes,
            filename=filename,
            content_type=content_type,
        )
        if caption:
            data.add_field("caption", caption)

        return data

    async def send_message(
        self,
        bale_bot_token: str,
        chat_id: int,
        text: str
    ):
        payload = {
            "chat_id": chat_id,
            "text": text
        }

        return await self._request(
            bale_bot_token,
            "sendMessage",
            json=payload
        )

    async def send_photo(
        self,
        bale_bot_token: str,
        chat_id: int,
        photo,
        caption: str | None = None
    ):
        unique_name = f"{uuid.uuid4().hex}.jpg"
        data = await self._build_media_form(
            chat_id, "photo", photo, unique_name, "image/jpeg", caption
        )

        return await self._request(
            bale_bot_token,
            "sendPhoto",
            data=data,
            is_media=True,
        )

    async def send_video(
        self,
        bale_bot_token: str,
        chat_id: int,
        video,
        caption: str | None = None
    ):
        unique_name = f"{uuid.uuid4().hex}.mp4"
        data = await self._build_media_form(
            chat_id, "video", video, unique_name, "video/mp4", caption
        )

        return await self._request(
            bale_bot_token,
            "sendVideo",
            data=data,
            is_media=True,
        )

    async def send_audio(
        self,
        bale_bot_token: str,
        chat_id: int,
        audio,
        caption: str | None = None
    ):
        unique_name = f"{uuid.uuid4().hex}.mp3"
        data = await self._build_media_form(
            chat_id, "audio", audio, unique_name, "audio/mpeg", caption
        )

        return await self._request(
            bale_bot_token,
            "sendAudio",
            data=data,
            is_media=True,
        )

    async def send_voice(
        self,
        bale_bot_token: str,
        chat_id: int,
        voice,
        caption: str | None = None
    ):
        unique_name = f"{uuid.uuid4().hex}.ogg"
        data = await self._build_media_form(
            chat_id, "voice", voice, unique_name, "audio/ogg", caption
        )

        return await self._request(
            bale_bot_token,
            "sendVoice",
            data=data,
            is_media=True,
        )

    async def send_document(
        self,
        bale_bot_token: str,
        chat_id: int,
        document,
        filename: str,
        caption: str | None = None
    ):
        data = await self._build_media_form(
            chat_id,
            "document",
            document,
            filename,
            "application/octet-stream",
            caption,
        )

        return await self._request(
            bale_bot_token,
            "sendDocument",
            data=data,
            is_media=True,
        )

    async def send_animation(
        self,
        bale_bot_token: str,
        chat_id: int,
        animation,
        caption: str | None = None
    ):
        unique_name = f"{uuid.uuid4().hex}.gif"
        data = await self._build_media_form(
            chat_id, "animation", animation, unique_name, "video/mp4", caption
        )

        return await self._request(
            bale_bot_token,
            "sendAnimation",
            data=data,
            is_media=True,
        )

    async def send_video_note(
        self,
        bale_bot_token: str,
        chat_id: int,
        video_note
    ):
        unique_name = f"{uuid.uuid4().hex}.mp4"
        data = await self._build_media_form(
            chat_id, "video_note", video_note, unique_name, "video/mp4", None
        )

        return await self._request(
            bale_bot_token,
            "sendVideoNote",
            data=data,
            is_media=True,
        )

    async def send_location(
        self,
        bale_bot_token: str,
        chat_id: int,
        latitude: float,
        longitude: float
    ):
        payload = {
            "chat_id": chat_id,
            "latitude": latitude,
            "longitude": longitude
        }

        return await self._request(
            bale_bot_token,
            "sendLocation",
            json=payload
        )

    async def send_contact(
        self,
        bale_bot_token: str,
        chat_id: int,
        phone_number: str,
        first_name: str,
        last_name: str = ""
    ):
        payload = {
            "chat_id": chat_id,
            "phone_number": phone_number,
            "first_name": f"{first_name} {last_name}".strip()
        }

        return await self._request(
            bale_bot_token,
            "sendContact",
            json=payload
        )

    async def verify_token(self, bale_bot_token: str) -> bool:
        """
        بررسی صحت bot_token با فراخوانی getMe.

        Returns:
            True  → token معتبر است
            False → token نامعتبر یا خطا در اتصال
        """
        try:
            await self._request(bale_bot_token, "getMe", method="GET")
            return True
        except Exception:
            return False


bale_bot = BaleService()