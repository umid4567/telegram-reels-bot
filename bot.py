import os
import logging
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart
from aiogram.types import WebAppInfo
from aiogram.utils.keyboard import InlineKeyboardBuilder

# Tokenni Render-dagi Environment Variables-dan oladi
# Bu xavfsizlik uchun eng to'g'ri yo'l
TOKEN = os.getenv("BOT_TOKEN") 

# Logging sozlamalari
logging.basicConfig(level=logging.INFO)

bot = Bot(token=TOKEN)
dp = Dispatcher()

@dp.message(CommandStart())
async def start(message: types.Message):
    builder = InlineKeyboardBuilder()
    
    # GitHub Pages-da jonlantirilgan Mini App manzili
    web_url = "https://umid4567.github.io/telegram-reels-bot/" 
    
    builder.row(types.InlineKeyboardButton(
        text="🎬 Reels ko'rish", 
        web_app=WebAppInfo(url=web_url))
    )
    
    await message.answer(
        f"Salom {message.from_user.full_name}!\n\n"
        "UzReels Mini App-ga xush kelibsiz! Qisqa videolarni ko'rish uchun pastdagi tugmani bosing:",
        reply_markup=builder.as_markup()
    )

async def main():
    # Botni ishga tushirish
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logging.info("Bot to'xtatildi")
