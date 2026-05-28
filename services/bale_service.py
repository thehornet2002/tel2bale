import aiohttp
from config import BALE_BOT_TOKEN
import json
from collections import defaultdict


media_groups = defaultdict(list)


async def send_verify_code(chat_id: int, code: str):
    url = f"https://tapi.bale.ai/bot{BALE_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": chat_id, "text": f"کد تایید شما: {code}"}
    headers = {"Content-Type": "application/json"}
    timeout = aiohttp.ClientTimeout(total=10)

    async with aiohttp.ClientSession(timeout=timeout) as session:
        async with session.post(url, json=payload, headers=headers) as resp:
            text = await resp.text()
            if resp.status != 200:
                raise Exception(f"HTTP {resp.status}: {text}")
            data = await resp.json()
            if not data.get("ok"):
                raise Exception(f"Bale API Error {data.get('error_code')}: {data.get('description')}")
            return data["result"]


async def send_message(chat_id:int, message:str):
    url = f"https://tapi.bale.ai/bot{BALE_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": chat_id, "text": message}
    headers = {"Content-Type": "application/json"}
    timeout = aiohttp.ClientTimeout(total=10)

    async with aiohttp.ClientSession(timeout=timeout) as session:
        async with session.post(url, json=payload, headers=headers) as resp:
            text = await resp.text()
            if resp.status != 200:
                raise Exception(f"HTTP {resp.status}: {text}")
            data = await resp.json()
            if not data.get("ok"):
                raise Exception(f"Bale API Error {data.get('error_code')}: {data.get('description')}")
            return data["result"]



async def send_photo(chat_id: int, photo: bytes, caption: str = None):
    url = f"https://tapi.bale.ai/bot{BALE_BOT_TOKEN}/sendPhoto"
    timeout = aiohttp.ClientTimeout(total=30)
    async with aiohttp.ClientSession(timeout=timeout) as session:
        data = aiohttp.FormData()
        data.add_field("chat_id", str(chat_id))
        data.add_field("photo", photo, filename="photo.jpg", content_type="image/jpeg")
        if caption:
            data.add_field("caption", caption)
        async with session.post(url, data=data) as resp:
            text = await resp.text()
            if resp.status != 200:
                raise Exception(f"HTTP {resp.status}: {text}")
            result = await resp.json()
            if not result.get("ok"):
                raise Exception(f"Bale API Error: {result.get('description')}")
            return result["result"]


async def send_video(chat_id: int, video: bytes, caption: str = None):
    url = f"https://tapi.bale.ai/bot{BALE_BOT_TOKEN}/sendVideo"
    timeout = aiohttp.ClientTimeout(total=60)
    async with aiohttp.ClientSession(timeout=timeout) as session:
        data = aiohttp.FormData()
        data.add_field("chat_id", str(chat_id))
        data.add_field("video", video, filename="video.mp4", content_type="video/mp4")
        if caption:
            data.add_field("caption", caption)
        async with session.post(url, data=data) as resp:
            text = await resp.text()
            if resp.status != 200:
                raise Exception(f"HTTP {resp.status}: {text}")
            result = await resp.json()
            if not result.get("ok"):
                raise Exception(f"Bale API Error: {result.get('description')}")
            return result["result"]

async def send_audio(chat_id: int, audio: bytes, caption: str = None):
    url = f"https://tapi.bale.ai/bot{BALE_BOT_TOKEN}/sendAudio"
    timeout = aiohttp.ClientTimeout(total=60)
    async with aiohttp.ClientSession(timeout=timeout) as session:
        data = aiohttp.FormData()
        data.add_field("chat_id", str(chat_id))
        data.add_field("audio", audio, filename="audio.mp3", content_type="audio/mpeg")
        if caption:
            data.add_field("caption", caption)
        async with session.post(url, data=data) as resp:
            text = await resp.text()
            if resp.status != 200:
                raise Exception(f"HTTP {resp.status}: {text}")
            result = await resp.json()
            if not result.get("ok"):
                raise Exception(f"Bale API Error: {result.get('description')}")
            return result["result"]


async def send_voice(chat_id: int, voice: bytes, caption: str = None):
    url = f"https://tapi.bale.ai/bot{BALE_BOT_TOKEN}/sendVoice"
    timeout = aiohttp.ClientTimeout(total=30)
    async with aiohttp.ClientSession(timeout=timeout) as session:
        data = aiohttp.FormData()
        data.add_field("chat_id", str(chat_id))
        data.add_field("voice", voice, filename="voice.ogg", content_type="audio/ogg")
        if caption:
            data.add_field("caption", caption)
        async with session.post(url, data=data) as resp:
            text = await resp.text()
            if resp.status != 200:
                raise Exception(f"HTTP {resp.status}: {text}")
            result = await resp.json()
            if not result.get("ok"):
                raise Exception(f"Bale API Error: {result.get('description')}")
            return result["result"]


async def send_document(chat_id: int, document: bytes, filename: str, caption: str = None):
    url = f"https://tapi.bale.ai/bot{BALE_BOT_TOKEN}/sendDocument"
    timeout = aiohttp.ClientTimeout(total=60)
    async with aiohttp.ClientSession(timeout=timeout) as session:
        data = aiohttp.FormData()
        data.add_field("chat_id", str(chat_id))
        data.add_field("document", document, filename=filename, content_type="application/octet-stream")
        if caption:
            data.add_field("caption", caption)
        async with session.post(url, data=data) as resp:
            text = await resp.text()
            if resp.status != 200:
                raise Exception(f"HTTP {resp.status}: {text}")
            result = await resp.json()
            if not result.get("ok"):
                raise Exception(f"Bale API Error: {result.get('description')}")
            return result["result"]

async def send_animation(chat_id: int, animation: bytes, caption: str = None):
    url = f"https://tapi.bale.ai/bot{BALE_BOT_TOKEN}/sendAnimation"
    timeout = aiohttp.ClientTimeout(total=60)
    async with aiohttp.ClientSession(timeout=timeout) as session:
        data = aiohttp.FormData()
        data.add_field("chat_id", str(chat_id))
        data.add_field("animation", animation, filename="animation.gif", content_type="video/mp4")
        if caption:
            data.add_field("caption", caption)
        async with session.post(url, data=data) as resp:
            text = await resp.text()
            if resp.status != 200:
                raise Exception(f"HTTP {resp.status}: {text}")
            result = await resp.json()
            if not result.get("ok"):
                raise Exception(f"Bale API Error: {result.get('description')}")
            return result["result"]

async def send_video_note(chat_id: int, video_note: bytes):
    url = f"https://tapi.bale.ai/bot{BALE_BOT_TOKEN}/sendVideoNote"
    timeout = aiohttp.ClientTimeout(total=60)
    async with aiohttp.ClientSession(timeout=timeout) as session:
        data = aiohttp.FormData()
        data.add_field("chat_id", str(chat_id))
        data.add_field("video_note", video_note, filename="video_note.mp4", content_type="video/mp4")
        async with session.post(url, data=data) as resp:
            text = await resp.text()
            if resp.status != 200:
                raise Exception(f"HTTP {resp.status}: {text}")
            result = await resp.json()
            if not result.get("ok"):
                raise Exception(f"Bale API Error: {result.get('description')}")
            return result["result"]


async def send_location(chat_id: int, latitude: float, longitude: float):
    url = f"https://tapi.bale.ai/bot{BALE_BOT_TOKEN}/sendLocation"
    payload = {
        "chat_id": chat_id,
        "latitude": latitude,
        "longitude": longitude
    }
    headers = {"Content-Type": "application/json"}
    timeout = aiohttp.ClientTimeout(total=10)
    async with aiohttp.ClientSession(timeout=timeout) as session:
        async with session.post(url, json=payload, headers=headers) as resp:
            text = await resp.text()
            if resp.status != 200:
                raise Exception(f"HTTP {resp.status}: {text}")
            result = await resp.json()
            if not result.get("ok"):
                raise Exception(f"Bale API Error: {result.get('description')}")
            return result["result"]

async def send_contact(chat_id: int, phone_number: str, first_name: str, last_name: str = None):
    url = f"https://tapi.bale.ai/bot{BALE_BOT_TOKEN}/sendContact"
    payload = {
        "chat_id": chat_id,
        "phone_number": phone_number,
        "first_name": first_name + ' ' + last_name,
    }
    headers = {"Content-Type": "application/json"}
    timeout = aiohttp.ClientTimeout(total=10)
    async with aiohttp.ClientSession(timeout=timeout) as session:
        async with session.post(url, json=payload, headers=headers) as resp:
            text = await resp.text()
            if resp.status != 200:
                raise Exception(f"HTTP {resp.status}: {text}")
            result = await resp.json()
            if not result.get("ok"):
                raise Exception(f"Bale API Error: {result.get('description')}")
            return result["result"]


async def send_media_group(chat_id: int, media_list: list[dict]):
    url = f"https://tapi.bale.ai/bot{BALE_BOT_TOKEN}/sendMediaGroup"

    timeout = aiohttp.ClientTimeout(total=60)

    async with aiohttp.ClientSession(timeout=timeout) as session:

        data = aiohttp.FormData()
        data.add_field("chat_id", str(chat_id))

        media_json = []

        for i, item in enumerate(media_list):

            key = f"file_{i}"

            if item["type"] == "photo":
                filename = f"{key}.jpg"
                content_type = "image/jpeg"

            elif item["type"] == "video":
                filename = f"{key}.mp4"
                content_type = "video/mp4"

            else:
                continue

            data.add_field(
                key,
                item["bytes"],
                filename=filename,
                content_type=content_type
            )

            media_json.append({
                "type": item["type"],
                "media": f"attach://{key}",
                "caption": item.get("caption", "")
            })

        data.add_field(
            "media",
            json.dumps(media_json, ensure_ascii=False)
        )

        async with session.post(url, data=data) as resp:

            text = await resp.text()

            if resp.status != 200:
                raise Exception(f"HTTP {resp.status}: {text}")

            result = await resp.json()

            if not result.get("ok"):
                raise Exception(
                    f"Bale API Error: {result.get('description')}"
                )

            return result["result"]