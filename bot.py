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

# 1. Firebase sertifikat fayli yo'li (Render Secret File yo'li)
cred_path = "/opt/render/project/src/firebase-key.json"
firebase_url = "https://uzreels-bot-default-rtdb.europe-west1.firebasedatabase.app/"

# 2. Firebase-ni sertifikat bilan ishga tushirish
if not firebase_admin._apps:
    if os.path.exists(cred_path):
        cred = credentials.Certificate(cred_path)
        firebase_admin.initialize_app(cred, {'databaseURL': firebase_url})
    else:
        # Agar fayl hali yaratilmagan bo'lsa, xato bermasligi uchun log yozamiz
        logging.error("MUHIM: firebase-key.json fayli topilmadi! Render-da Secret File yarating.")

TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = 7748146680 

bot = Bot(token=TOKEN)
dp = Dispatcher()
logging.basicConfig(level=logging.INFO)

# Render uchun veb-server
async def handle(request):
    return web.Response(text="Bot muvaffaqiyatli ishlamoqda!")

@dp.message(CommandStart())
async def start(message: types.Message):
    builder = InlineKeyboardBuilder()
    web_url = "https://umid4567.github.io/telegram-reels-bot/" 
    
    builder.row(types.InlineKeyboardButton(
        text="🎬 Reels ko'rish", 
        web_app=WebAppInfo(url=web_url))
    )
    
    await message.answer(
        f"Salom {message.from_user.full_name}!\n\nMen admin panel botman. Menga video yuborsangiz, uni bazaga qo'shaman.", 
        reply_markup=builder.as_markup()
    )

# Video qabul qilish qismi
@dp.message(F.video)
async def handle_video(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        await message.reply("Kechirasiz, faqat admin video qo'sha oladi.")
        return

    # Telegram video ID-sini olish
    video_id = message.video.file_id
    
    try:
        # Firebase-ga ma'lumotni yozish
        ref = db.reference('videos')
        ref.push({
            'url': video_id, 
            'user': message.from_user.full_name,
            'caption': message.caption or "Yangi video",
            'date': message.date.strftime("%Y-%m-%d %H:%M")
        })
        await message.reply("✅ Zo'r! Video Firebase bazasiga qo'shildi.")
    except Exception as e:
        logging.error(f"Firebase xatosi: {e}")
        await message.reply(f"Xato yuz berdi: {e}")

async def main():
    app = web.Application()
    app.router.add_get('/', handle)
    runner = web.AppRunner(app)
    await runner.setup()
    
    port = int(os.getenv("PORT", 10000))
    site = web.TCPSite(runner, '0.0.0.0', port)
    
    await asyncio.gather(
        site.start(),
        dp.start_polling(bot)
    )

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logging.info("Bot to'xtatildi")
