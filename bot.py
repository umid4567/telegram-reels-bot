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

# 1. Firebase sozlamalari
cred_path = "/opt/render/project/src/firebase-key.json"
firebase_url = "https://uzreels-bot-default-rtdb.europe-west1.firebasedatabase.app/"

if not firebase_admin._apps:
    if os.path.exists(cred_path):
        cred = credentials.Certificate(cred_path)
        firebase_admin.initialize_app(cred, {'databaseURL': firebase_url})
    else:
        logging.error("MUHIM: firebase-key.json topilmadi!")

TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = 7748146680 

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
    await message.answer(f"Salom {message.from_user.full_name}!", reply_markup=builder.as_markup())

# --- MUHIM O'ZGARISH SHU YERDA ---
@dp.message(F.video)
async def handle_video(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return

    wait_msg = await message.reply("⏳ Video linkka aylantirilmoqda...")
    
    try:
        # 1. Telegramdan fayl yo'lini olish
        file_id = message.video.file_id
        file = await bot.get_file(file_id)
        file_path = file.file_path
        
        # 2. To'g'ridan-to'g'ri yuklab olish linkini yasash
        # DIQQAT: Bu link vaqtinchalik (bir necha soat ishlaydi)
        download_url = f"https://api.telegram.org/file/bot{TOKEN}/{file_path}"
        
        # 3. Firebase-ga yozish
        ref = db.reference('videos')
        ref.push({
            'url': download_url, # Endi bu yerda file_id emas, haqiqiy link bor
            'user': message.from_user.full_name,
            'caption': message.caption or "Yangi video",
            'date': message.date.strftime("%Y-%m-%d %H:%M")
        })
        
        await wait_msg.edit_text("✅ Video muvaffaqiyatli Web App-ga qo'shildi!")
    except Exception as e:
        logging.error(f"Xato: {e}")
        await wait_msg.edit_text(f"Xato yuz berdi: {e}")

async def main():
    app = web.Application()
    app.router.add_get('/', handle)
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.getenv("PORT", 10000))
    site = web.TCPSite(runner, '0.0.0.0', port)
    await asyncio.gather(site.start(), dp.start_polling(bot))

if __name__ == "__main__":
    asyncio.run(main())
