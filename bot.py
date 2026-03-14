import os
import logging
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart
from aiogram.types import WebAppInfo
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiohttp import web # Port muammosini hal qilish uchun

TOKEN = os.getenv("BOT_TOKEN")
logging.basicConfig(level=logging.INFO)

bot = Bot(token=TOKEN)
dp = Dispatcher()

# Oddiy veb-server (Render port so'ragani uchun)
async def handle(request):
    return web.Response(text="Bot is running!")

@dp.message(CommandStart())
async def start(message: types.Message):
    builder = InlineKeyboardBuilder()
    web_url = "https://umid4567.github.io/telegram-reels-bot/" 
    
    builder.row(types.InlineKeyboardButton(
        text="🎬 Reels ko'rish", 
        web_app=WebAppInfo(url=web_url))
    )
    
    await message.answer(
        f"Salom {message.from_user.full_name}!\n\nUzReels-ga xush kelibsiz!",
        reply_markup=builder.as_markup()
    )

async def main():
    # Veb-serverni fonda ishga tushirish
    app = web.Application()
    app.router.add_get('/', handle)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', int(os.getenv("PORT", 10000)))
    
    # Ham serverni, ham botni birga yurgizish
    await asyncio.gather(
        site.start(),
        dp.start_polling(bot)
    )

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logging.info("Bot to'xtatildi")
