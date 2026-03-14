import os
import logging
import asyncio
import firebase_admin
from firebase_admin import db
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart
from aiogram.types import WebAppInfo
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiohttp import web

# Firebase-ni ulash (Sertifikatsiz, faqat URL orqali)
firebase_url = "https://uzreels-bot-default-rtdb.europe-west1.firebasedatabase.app/"

if not firebase_admin._apps:
    # Test rejimi uchun faqat databaseURL kifoya
    firebase_admin.initialize_app(options={'databaseURL': firebase_url})

TOKEN = os.getenv("BOT_TOKEN")
# Sizning Telegram ID-ingiz kiritildi
ADMIN_ID = 7748146680 

bot = Bot(token=TOKEN)
dp = Dispatcher()
logging.basicConfig(level=logging.INFO)

# Render portini ushlash uchun oddiy sahifa
async def handle(request):
    return web.Response(text="Bot ishlamoqda!")

@dp.message(CommandStart())
async def start(message: types.Message):
    builder = InlineKeyboardBuilder()
    # Sizning GitHub Pages manzilingiz
    web_url = "https://umid4567.github.io/telegram-reels-bot/" 
    
    builder.row(types.InlineKeyboardButton(
        text="🎬 Reels ko'rish", 
        web_app=WebAppInfo(url=web_url))
    )
    
    await message.answer(
        f"Salom {message.from_user.full_name}!\nVideo yuborsangiz, uni bazaga qo'shaman.", 
        reply_markup=builder.as_markup()
    )

# Botga video yuborilganda ushlab qolish
@dp.message(F.video)
async def handle_video(message: types.Message):
    # Faqat siz video qo'sha olishingiz uchun tekshiruv
    if message.from_user.id != ADMIN_ID:
        await message.reply("Kechirasiz, faqat admin video qo'sha oladi.")
        return

    video_id = message.video.file_id
    
    try:
        # Firebase bazasiga yozish
        ref = db.reference('videos')
        ref.push({
            'url': video_id, 
            'user': message.from_user.full_name,
            'caption': message.caption or "Ajoyib video!",
            'timestamp': {'.sv': 'timestamp'} # Vaqtni belgilash
        })
        await message.reply("✅ Video bazaga muvaffaqiyatli qo'shildi!")
    except Exception as e:
        logging.error(f"Xatolik yuz berdi: {e}")
        await message.reply(f"Xato yuz berdi: {e}")

async def main():
    # Veb-server (Render uchun)
    app = web.Application()
    app.router.add_get('/', handle)
    runner = web.AppRunner(app)
    await runner.setup()
    
    # Portni Render'dan olish yoki 10000 ishlatish
    port = int(os.getenv("PORT", 10000))
    site = web.TCPSite(runner, '0.0.0.0', port)
    
    logging.info(f"Bot va server {port}-portda ishga tushmoqda...")
    
    # Ham serverni, ham botni baravar ishga tushirish
    await asyncio.gather(
        site.start(),
        dp.start_polling(bot)
    )

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logging.info("Bot to'xtatildi")
