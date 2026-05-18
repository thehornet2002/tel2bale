from pyrogram.types import Message
from db.model_acync import get_send_attempts, get_cooldown, set_send_attempts, set_cooldown, set_verify_code, set_state, get_verify_code, set_verified, check_admin,save_support_message
from utils.code_generator import generate_random_code
from services.bale_service import send_verify_code
from utils.keyboards import build_start_keyboard, build_back_keyboard
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
            await message.reply_text(message_txt, reply_markup=build_back_keyboard())
    else:
        if attempts == 2:
            await set_cooldown(user_id,str(int(time.time())+900))
        await set_send_attempts(user_id,attempts+1)
        code = await generate_random_code()
        await set_verify_code(user_id,code,str(int(time.time())+120))
        await send_verify_code(id_num,str(code))
        await set_state(user_id, 'enter_verify_code')
        await message.reply_text(
             'کد احراز هویت برای اکانت بله شما ارسال شد. لطفا کد را وارد کنید',
             reply_markup=build_back_keyboard()
             )


async def enter_verify_code(message: Message, user_id:int):
    if not message.text.isdigit():
        await message.reply_text("لطفا فقط عدد وارد کنید.")
        return
    client_code = int(message.text)
    verify_code, verify_expire = await get_verify_code(user_id)
    if int(verify_expire) >= int(time.time()):
        if verify_code == client_code:
            await set_verified(user_id,True)
            await set_state(user_id,'home')
            await set_send_attempts(user_id,0)
            await set_verify_code(user_id,0,"")
            await set_cooldown(user_id,'')
            await message.reply_text(
                'احراز هویت شما با موفقیت انجام شد',
                reply_markup=build_start_keyboard(await check_admin(user_id))
            )
        else:
             await message.reply_text(
                'کد را اشتباه وارد کردید. لطفا دوباره کد را وارد کنید:',
                build_back_keyboard()
            )
    else:
        await message.reply_text(
            'زمان ارسال کد به پایان رسیده لطفا دوباره تلاش کنید',
            reply_markup=build_back_keyboard()
        )


async def send_support_message(message:Message, user_id:int):
        await save_support_message(user_id,message_text=str(message.text))
        await message.reply_text(
             'پیام شما با موفقیت ارسال شد',
             reply_markup=build_back_keyboard()
        )