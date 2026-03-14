import logging
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart
from aiogram.types import WebAppInfo
from aiogram.utils.keyboard import InlineKeyboardBuilder

# BotFather'dan olgan tokeningizni buni o'rniga qo'ying
TOKEN = "SIZNING_BOT_TOKENINGIZ" 

bot = Bot(token=TOKEN)
dp = Dispatcher()
logging.basicConfig(level=logging.INFO)

@dp.message(CommandStart())
async def start(message: types.Message):
    builder = InlineKeyboardBuilder()
    
    # DIQQAT: Bu yerga .git emas, balki Pages linkini qo'yamiz
    web_url = "https://umid4567.github.io/telegram-reels-bot/" 
    
    builder.row(types.InlineKeyboardButton(
        text="🎬 Reels ko'rish", 
        web_app=WebAppInfo(url=web_url))
    )
    
    await message.answer(
        f"Salom {message.from_user.full_name}!\n\n"
        "Telegram Mini App orqali Reels ko'rishga tayyormisiz?",
        reply_markup=builder.as_markup()
    )

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Bot to'xtatildi")
