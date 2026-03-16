import os
import asyncio
import requests
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart
from aiogram.types import WebAppInfo
from supabase import create_client, Client
import firebase_admin
from firebase_admin import credentials, db
from datetime import datetime

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

bot = Bot(token=TOKEN)
dp = Dispatcher()

@dp.message(CommandStart())
async def start(message: types.Message):
    web_url = "https://umid4567.github.io/telegram-reels-bot/"
    builder = types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text="🎬 UzReels-ni ochish", web_app=WebAppInfo(url=web_url))]
    ])
    await message.answer("Salom! Menga video yuboring, men uni UzReels-ga qo'shaman.", reply_markup=builder)

@dp.message(F.video)
async def handle_video(message: types.Message):
    wait_msg = await message.answer("⏳ Video Supabase-ga yuklanmoqda...")
    
    try:
        # 1. Telegramdan videoni yuklab olish
        file_id = message.video.file_id
        file = await bot.get_file(file_id)
        file_path = f"https://api.telegram.org/file/bot{TOKEN}/{file.file_path}"
        
        video_response = requests.get(file_path)
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
        video_url = res # Supabase public linki
        
        # 4. Firebase Database-ga yozish (Web App o'qishi uchun)
        db.reference('videos').push({
            'file_url': video_url,
            'user': message.from_user.username or message.from_user.full_name,
            'caption': message.caption or "",
            'date': datetime.now().strftime("%Y-%m-%d %H:%M")
        })
        
        await wait_msg.edit_text("✅ Video muvaffaqiyatli UzReels-ga qo'shildi!")
        
    except Exception as e:
        await wait_msg.edit_text(f"❌ Xatolik yuz berdi: {str(e)}")

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
