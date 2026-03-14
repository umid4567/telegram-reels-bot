import os
import logging
import asyncio
import firebase_admin
from firebase_admin import credentials, db
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart
from aiogram.types import WebAppInfo
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiohttp import web

# Firebase-ni ulash
# Diqqat: Bu yerda hech narsani o'zgartirmang, bazani sozlash pastda
firebase_url = "https://uzreels-bot-default-rtdb.europe-west1.firebasedatabase.app/"

if not firebase_admin._apps:
    cred = credentials.Certificate(None) # Renderda sertifikatsiz ishlash uchun
    firebase_admin.initialize_app(cred, {'databaseURL': firebase_url})

TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = 123456789 # BU YERGA O'ZINGIZNING TELEGRAM ID-INGIZNI YOZING!

bot = Bot(token=TOKEN)
dp = Dispatcher()
logging.basicConfig(level=logging.INFO)

async def handle(request):
    return web.Response(text="Bot ishlamoqda!")

@dp.message(CommandStart())
async def start(message: types.Message):
    builder = InlineKeyboardBuilder()
    web_url = "https://umid4567.github.io/telegram-reels-bot/" 
    builder.row(types.InlineKeyboardButton(text="🎬 Reels ko'rish", web_app=WebAppInfo(url=web_url)))
    await message.answer(f"Salom! Video yuborsangiz, uni bazaga qo'shaman.", reply_markup=builder.as_markup())

# Botga video yuborilganda ushlab qolish
@dp.message(F.video)
async def handle_video(message: types.Message):
    # Faqat admin (siz) video qo'sha olishi uchun
    video_id = message.video.file_id
    
    # Bazaga yozish
    ref = db.reference('videos')
    ref.push({
        'url': video_id, # Telegram file_id si
        'user': message.from_user.full_name,
        'caption': message.caption or "Ajoyib video!"
    })
    
    await message.reply("✅ Video bazaga muvaffaqiyatli qo'shildi!")

async def main():
    app = web.Application()
    app.router.add_get('/', handle)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', int(os.getenv("PORT", 10000)))
    await asyncio.gather(site.start(), dp.start_polling(bot))

if __name__ == "__main__":
    asyncio.run(main())
