from __future__ import annotations

import asyncio
import json
import mimetypes
import os
import uuid
from typing import Any

import aiohttp

from config import BALE_PROXY_URL


class BaleServiceError(Exception):
    """خطای قابل تشخیص برای سرویس بله"""


class BaleService:
    def __init__(self):
        self.session: aiohttp.ClientSession | None = None
        self._session_lock = asyncio.Lock()

    async def start(self):
        async with self._session_lock:
            if not self.session or self.session.closed:
                timeout = aiohttp.ClientTimeout(
                    total=120,
                    connect=20,
                    sock_connect=20,
                    sock_read=120,
                )
                self.session = aiohttp.ClientSession(timeout=timeout)

    async def close(self):
        async with self._session_lock:
            if self.session and not self.session.closed:
                await self.session.close()

    async def _request(
        self,
        bale_bot_token: str,
        endpoint: str,
        method: str = "POST",
        *,
        max_retries: int = 2,
        **kwargs: Any,
    ):
        if not self.session or self.session.closed:
            await self.start()

        url = f"https://tapi.bale.ai/bot{bale_bot_token}/{endpoint}"

        if BALE_PROXY_URL:
            kwargs.setdefault("proxy", BALE_PROXY_URL)

        last_error: Exception | None = None

        for attempt in range(max_retries + 1):
            try:
                assert self.session is not None

                async with self.session.request(method, url, **kwargs) as resp:
                    text = await resp.text()

                    data = None
                    try:
                        data = json.loads(text) if text else {}
                    except json.JSONDecodeError:
                        data = None

                    if resp.status == 429:
                        retry_after = 1

                        if isinstance(data, dict):
                            retry_after = (
                                data.get("parameters", {}).get("retry_after")
                                or data.get("retry_after")
                                or 1
                            )

                        if attempt < max_retries:
                            await asyncio.sleep(float(retry_after))
                            continue

                    if resp.status in {500, 502, 503, 504} and attempt < max_retries:
                        await asyncio.sleep(1 + attempt)
                        continue

                    if resp.status != 200:
                        raise BaleServiceError(
                            f"خطای ارتباط با بله (HTTP {resp.status})\n{text}"
                        )

                    if not isinstance(data, dict):
                        raise BaleServiceError(
                            f"پاسخ نامعتبر از سرور بله:\n{text}"
                        )

                    if not data.get("ok", False):
                        raise BaleServiceError(
                            data.get("description", "خطای ناشناخته از سمت بله")
                        )

                    return data.get("result")

            except aiohttp.ClientError as e:
                last_error = e

                if attempt < max_retries:
                    await asyncio.sleep(1 + attempt)
                    continue

                raise BaleServiceError(
                    f"خطا در اتصال به سرورهای بله:\n{e}"
                ) from e

        if last_error:
            raise BaleServiceError(str(last_error))

        raise BaleServiceError("خطای ناشناخته در ارتباط با بله")

    def _make_unique_filename(
        self,
        filename: str | None = None,
        default_ext: str = ".bin",
    ) -> str:
        ext = ""

        if filename:
            _, ext = os.path.splitext(filename)

        if not ext:
            ext = default_ext

        if not ext.startswith("."):
            ext = "." + ext

        return f"{uuid.uuid4().hex}{ext.lower()}"

    def _guess_content_type(
        self,
        filename: str | None,
        content_type: str | None,
        default_content_type: str,
    ) -> str:
        if content_type:
            return content_type

        if filename:
            guessed, _ = mimetypes.guess_type(filename)
            if guessed:
                return guessed

        return default_content_type

    async def _send_file(
        self,
        *,
        bale_bot_token: str,
        endpoint: str,
        field_name: str,
        chat_id: int,
        file_obj,
        filename: str | None,
        content_type: str | None,
        default_ext: str,
        default_content_type: str,
        caption: str | None = None,
    ):
        data = aiohttp.FormData()
        data.add_field("chat_id", str(chat_id))

        safe_filename = self._make_unique_filename(
            filename=filename,
            default_ext=default_ext,
        )

        final_content_type = self._guess_content_type(
            filename=filename,
            content_type=content_type,
            default_content_type=default_content_type,
        )

        try:
            file_obj.seek(0)
        except Exception:
            pass

        data.add_field(
            field_name,
            file_obj,
            filename=safe_filename,
            content_type=final_content_type,
        )

        if caption:
            data.add_field("caption", caption)

        return await self._request(
            bale_bot_token,
            endpoint,
            data=data,
        )

    async def send_message(
        self,
        bale_bot_token: str,
        chat_id: int,
        text: str,
    ):
        payload = {
            "chat_id": chat_id,
            "text": text,
        }

        return await self._request(
            bale_bot_token,
            "sendMessage",
            json=payload,
        )

    async def send_photo(
        self,
        bale_bot_token: str,
        chat_id: int,
        photo,
        caption: str | None = None,
        filename: str | None = None,
        content_type: str | None = None,
    ):
        return await self._send_file(
            bale_bot_token=bale_bot_token,
            endpoint="sendPhoto",
            field_name="photo",
            chat_id=chat_id,
            file_obj=photo,
            filename=filename,
            content_type=content_type,
            default_ext=".jpg",
            default_content_type="image/jpeg",
            caption=caption,
        )

    async def send_video(
        self,
        bale_bot_token: str,
        chat_id: int,
        video,
        caption: str | None = None,
        filename: str | None = None,
        content_type: str | None = None,
    ):
        return await self._send_file(
            bale_bot_token=bale_bot_token,
            endpoint="sendVideo",
            field_name="video",
            chat_id=chat_id,
            file_obj=video,
            filename=filename,
            content_type=content_type,
            default_ext=".mp4",
            default_content_type="video/mp4",
            caption=caption,
        )

    async def send_audio(
        self,
        bale_bot_token: str,
        chat_id: int,
        audio,
        caption: str | None = None,
        filename: str | None = None,
        content_type: str | None = None,
    ):
        return await self._send_file(
            bale_bot_token=bale_bot_token,
            endpoint="sendAudio",
            field_name="audio",
            chat_id=chat_id,
            file_obj=audio,
            filename=filename,
            content_type=content_type,
            default_ext=".mp3",
            default_content_type="audio/mpeg",
            caption=caption,
        )

    async def send_voice(
        self,
        bale_bot_token: str,
        chat_id: int,
        voice,
        caption: str | None = None,
        filename: str | None = None,
        content_type: str | None = None,
    ):
        return await self._send_file(
            bale_bot_token=bale_bot_token,
            endpoint="sendVoice",
            field_name="voice",
            chat_id=chat_id,
            file_obj=voice,
            filename=filename,
            content_type=content_type,
            default_ext=".ogg",
            default_content_type="audio/ogg",
            caption=caption,
        )

    async def send_document(
        self,
        bale_bot_token: str,
        chat_id: int,
        document,
        filename: str | None = None,
        caption: str | None = None,
        content_type: str | None = None,
    ):
        return await self._send_file(
            bale_bot_token=bale_bot_token,
            endpoint="sendDocument",
            field_name="document",
            chat_id=chat_id,
            file_obj=document,
            filename=filename,
            content_type=content_type,
            default_ext=".bin",
            default_content_type="application/octet-stream",
            caption=caption,
        )

    async def send_animation(
        self,
        bale_bot_token: str,
        chat_id: int,
        animation,
        caption: str | None = None,
        filename: str | None = None,
        content_type: str | None = None,
    ):
        return await self._send_file(
            bale_bot_token=bale_bot_token,
            endpoint="sendAnimation",
            field_name="animation",
            chat_id=chat_id,
            file_obj=animation,
            filename=filename,
            content_type=content_type,
            default_ext=".mp4",
            default_content_type="video/mp4",
            caption=caption,
        )

    async def send_video_note(
        self,
        bale_bot_token: str,
        chat_id: int,
        video_note,
        filename: str | None = None,
        content_type: str | None = None,
    ):
        return await self._send_file(
            bale_bot_token=bale_bot_token,
            endpoint="sendVideoNote",
            field_name="video_note",
            chat_id=chat_id,
            file_obj=video_note,
            filename=filename,
            content_type=content_type,
            default_ext=".mp4",
            default_content_type="video/mp4",
            caption=None,
        )

    async def send_location(
        self,
        bale_bot_token: str,
        chat_id: int,
        latitude: float,
        longitude: float,
    ):
        payload = {
            "chat_id": chat_id,
            "latitude": latitude,
            "longitude": longitude,
        }

        return await self._request(
            bale_bot_token,
            "sendLocation",
            json=payload,
        )

    async def send_contact(
        self,
        bale_bot_token: str,
        chat_id: int,
        phone_number: str,
        first_name: str,
        last_name: str = "",
    ):
        payload = {
            "chat_id": chat_id,
            "phone_number": phone_number,
            "first_name": first_name,
        }

        if last_name:
            payload["last_name"] = last_name

        return await self._request(
            bale_bot_token,
            "sendContact",
            json=payload,
        )

    async def verify_token(self, bale_bot_token: str) -> bool:
        try:
            await self._request(
                bale_bot_token,
                "getMe",
                method="GET",
                max_retries=0,
            )
            return True
        except Exception:
            return False


bale_bot = BaleService()