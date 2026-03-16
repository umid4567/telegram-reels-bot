import os
import asyncio
import requests
import logging
from datetime import datetime
from aiohttp import web  # Render port xatosi bermasligi uchun

from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart
from aiogram.types import WebAppInfo
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from supabase import create_client, Client
import firebase_admin
from firebase_admin import credentials, db

# Loglarni sozlash
logging.basicConfig(level=logging.INFO)

# --- SOZLAMALAR ---
SUPABASE_URL = "https://tgzywqgimxwkavmdwgnc.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InRnenl3cWdpbXh3a2F2bWR3Z25jIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzM2NzAwNjgsImV4cCI6MjA4OTI0NjA2OH0.VRP6mp1RL2jmU1I4mjpHV87DK_i81CA7Zmtbdgg_jjI"
TOKEN = os.getenv("BOT_TOKEN")

# Klientlarni ishga tushirish
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

if not firebase_admin._apps:
    # firebase-key.json faylingiz GitHub-da borligiga ishonch hosil qiling
    cred = credentials.Certificate("firebase-key.json")
    firebase_admin.initialize_app(cred, {
        'databaseURL': "https://uzreels-bot-default-rtdb.europe-west1.firebasedatabase.app/"
    })

bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()

# --- SOXTA VEB-SERVER (Render uchun) ---
async def handle(request):
    return web.Response(text="Bot is running!")

async def start_web_server():
    app = web.Application()
    app.router.add_get("/", handle)
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.environ.get("PORT", 10000))
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    logging.info(f"Veb-server {port}-portda ishga tushdi")

# --- BOT FUNKSIYALARI ---
@dp.message(CommandStart())
async def start(message: types.Message):
    web_url = "https://umid4567.github.io/telegram-reels-bot/"
    builder = types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text="🎬 UzReels-ni ochish", web_app=WebAppInfo(url=web_url))]
    ])
    await message.answer(f"Salom, <b>{message.from_user.full_name}</b>!\nMenga video yuboring, men uni UzReels-ga qo'shaman.", reply_markup=builder)

@dp.message(F.video)
async def handle_video(message: types.Message):
    wait_msg = await message.answer("⏳ Video Supabase Storage-ga yuklanmoqda...")
    
    try:
        # 1. Telegramdan videoni xotiraga yuklab olish
        file_id = message.video.file_id
        file = await bot.get_file(file_id)
        file_url = f"https://api.telegram.org/file/bot{TOKEN}/{file.file_path}"
        
        video_response = requests.get(file_url)
        if video_response.status_code != 200:
            raise Exception("Telegram-dan yuklab bo'lmadi")
        
        video_content = video_response.content
        
        # 2. Supabase Storage-ga yuklash
        file_name = f"reel_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4"
        
        supabase.storage.from_("videos").upload(
            path=file_name,
            file=video_content,
            file_options={"content-type": "video/mp4"}
        )
        
        # 3. Public URL olish
        res = supabase.storage.from_("videos").get_public_url(file_name)
        video_url = res
        
        # 4. Firebase-ga yozish
        db.reference('videos').push({
            'file_url': video_url,
            'user': message.from_user.username or message.from_user.full_name,
            'caption': message.caption or "",
            'date': datetime.now().strftime("%Y-%m-%d %H:%M")
        })
        
        await wait_msg.edit_text("✅ Video muvaffaqiyatli UzReels-ga qo'shildi!")
        
    except Exception as e:
        logging.error(f"Xatolik: {e}")
        await wait_msg.edit_text(f"❌ Xatolik yuz berdi: {str(e)}")

# --- ASOSIY ISHGA TUSHIRISH ---
async def main():
    # Bir vaqtning o'zida ham veb-serverni, ham botni ishga tushiramiz
    asyncio.create_task(start_web_server())
    
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logging.info("Bot to'xtatildi")
