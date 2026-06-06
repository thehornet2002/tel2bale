import aiohttp

from config import BALE_PROXY_URL


class BaleService:
    def __init__(self):
        self.session = None

    async def start(self):
        if not self.session or self.session.closed:
            timeout = aiohttp.ClientTimeout(total=100)
            self.session = aiohttp.ClientSession(timeout=timeout)

    async def close(self):
        if self.session and not self.session.closed:
            await self.session.close()

    async def _request(
        self,
        bale_bot_token: str,
        endpoint: str,
        method: str = "POST",
        **kwargs
    ):
        if not self.session or self.session.closed:
            await self.start()

        url = f"https://tapi.bale.ai/bot{bale_bot_token}/{endpoint}"

        # اگر proxy بله در .env تنظیم نشده باشد، مقدار None است و aiohttp بدون proxy کار می‌کند.
        if BALE_PROXY_URL:
            kwargs.setdefault("proxy", BALE_PROXY_URL)

        try:
            async with self.session.request(method, url, **kwargs) as resp:
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

        except aiohttp.ClientError as e:
            raise Exception(
                f"خطا در اتصال به سرورهای بله:\n{e}"
            )

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
        data = aiohttp.FormData()
        data.add_field("chat_id", str(chat_id))
        unique_name = f"{uuid.uuid4().hex}{ext}" 
        data.add_field(
            "photo",
            photo,
            filename=unique_name+".jpg",
            content_type="image/jpeg"
        )

        if caption:
            data.add_field("caption", caption)

        return await self._request(
            bale_bot_token,
            "sendPhoto",
            data=data
        )

    async def send_video(
        self,
        bale_bot_token: str,
        chat_id: int,
        video,
        caption: str | None = None
    ):
        data = aiohttp.FormData()
        data.add_field("chat_id", str(chat_id))
        unique_name = f"{uuid.uuid4().hex}{ext}" 
        data.add_field(
            "video",
            video,
            filename= unique_name + ".mp4",
            content_type="video/mp4"
        )

        if caption:
            data.add_field("caption", caption)

        return await self._request(
            bale_bot_token,
            "sendVideo",
            data=data
        )

    async def send_audio(
        self,
        bale_bot_token: str,
        chat_id: int,
        audio,
        caption: str | None = None
    ):
        data = aiohttp.FormData()
        data.add_field("chat_id", str(chat_id))
        unique_name = f"{uuid.uuid4().hex}{ext}" 
        data.add_field(
            "audio",
            audio,
            filename=unique_name + ".mp3",
            content_type="audio/mpeg"
        )

        if caption:
            data.add_field("caption", caption)

        return await self._request(
            bale_bot_token,
            "sendAudio",
            data=data
        )

    async def send_voice(
        self,
        bale_bot_token: str,
        chat_id: int,
        voice,
        caption: str | None = None
    ):
        data = aiohttp.FormData()
        data.add_field("chat_id", str(chat_id))
        unique_name = f"{uuid.uuid4().hex}{ext}" 
        data.add_field(
            "voice",
            voice,
            filename= unique_name + ".ogg",
            content_type="audio/ogg"
        )

        if caption:
            data.add_field("caption", caption)

        return await self._request(
            bale_bot_token,
            "sendVoice",
            data=data
        )

    async def send_document(
        self,
        bale_bot_token: str,
        chat_id: int,
        document,
        filename: str,
        caption: str | None = None
    ):
        data = aiohttp.FormData()
        data.add_field("chat_id", str(chat_id))
        data.add_field(
            "document",
            document,
            filename=filename,
            content_type="application/octet-stream"
        )

        if caption:
            data.add_field("caption", caption)

        return await self._request(
            bale_bot_token,
            "sendDocument",
            data=data
        )

    async def send_animation(
        self,
        bale_bot_token: str,
        chat_id: int,
        animation,
        caption: str | None = None
    ):
        data = aiohttp.FormData()
        data.add_field("chat_id", str(chat_id))
        unique_name = f"{uuid.uuid4().hex}{ext}" 
        data.add_field(
            "animation",
            animation,
            filename= unique_name + ".gif",
            content_type="video/mp4"
        )

        if caption:
            data.add_field("caption", caption)

        return await self._request(
            bale_bot_token,
            "sendAnimation",
            data=data
        )

    async def send_video_note(
        self,
        bale_bot_token: str,
        chat_id: int,
        video_note
    ):
        data = aiohttp.FormData()
        data.add_field("chat_id", str(chat_id))
        unique_name = f"{uuid.uuid4().hex}{ext}" 
        data.add_field(
            "video_note",
            video_note,
            filename= unique_name+".mp4",
            content_type="video/mp4"
        )

        return await self._request(
            bale_bot_token,
            "sendVideoNote",
            data=data
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