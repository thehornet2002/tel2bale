from pyrogram.types import Message
from db.model_acync import get_send_attempts, get_cooldown, set_send_attempts, set_cooldown, set_verify_code
from utils.code_generator import generate_random_code
from services.bale_service import send_verify_code
import time


async def enter_bale_id(message:Message, user_id:int):
    if not message.text.isdigit():
            await message.reply_text("لطفا فقط شناسه عددی ارسال کنید.")
            return
    id_num = int(message.text)
    attempts = await get_send_attempts(user_id)
    now = int(time.time())
    cooldown = await get_cooldown(user_id)
    if attempts >= 3:
        #cooldown check
        if now >= cooldown:
                await set_send_attempts(user_id,0)
        else:
            message_txt = str.format('لطفا صبر کنید و %d ثانیه دیگر دوباره تلاش کنید.',now-cooldown)
            await message.reply_text(message_txt)
    else:
        if attempts == 2:
            await set_cooldown(user_id,str(time.time()+900))
        await set_send_attempts(user_id,attempts+1)
        code = await generate_random_code()
        await set_verify_code(user_id,code,str(time.time()+120))
        await send_verify_code(id_num,str(code))
        await message.reply_text('کد احراز هویت برای اکانت بله شما ارسال شد.')