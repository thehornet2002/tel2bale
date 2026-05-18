import aiohttp
from config import BALE_BOT_TOKEN

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
