import os
import asyncio
import aiohttp
import logging
from datetime import datetime
from aiohttp import web
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart
from aiogram.types import WebAppInfo, InlineKeyboardButton, InlineKeyboardMarkup, InlineQueryResultVideo
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from supabase import create_client, Client
import firebase_admin
from firebase_admin import credentials, db

logging.basicConfig(level=logging.INFO)

# --- SOZLAMALAR ---
SUPABASE_URL = "https://tgzywqgimxwkavmdwgnc.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InRnenl3cWdpbXh3a2F2bWR3Z25jIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzM2NzAwNjgsImV4cCI6MjA4OTI0NjA2OH0.VRP6mp1RL2jmU1I4mjpHV87DK_i81CA7Zmtbdgg_jjI"
TOKEN = os.getenv("BOT_TOKEN")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

if not firebase_admin._apps:
    cred = credentials.Certificate("firebase-key.json")
    firebase_admin.initialize_app(cred, {'databaseURL': "https://uzreels-bot-default-rtdb.europe-west1.firebasedatabase.app/"})

bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()

class VideoUpload(StatesGroup):
    waiting_for_caption = State()
    waiting_for_category = State()

@dp.message(CommandStart())
async def start(m: types.Message):
    args = m.text.split()
    video_id = args[1] if len(args) > 1 else None
    base_url = "https://umid4567.github.io/telegram-reels-bot/"
    web_url = f"{base_url}?start={video_id}" if video_id else base_url
    
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎬 Videoni ko'rish" if video_id else "🎬 UzReels-ni ochish", web_app=WebAppInfo(url=web_url))]
    ])
    await m.answer("UzReels-ga xush kelibsiz!", reply_markup=kb)

@dp.message(F.video)
async def process_video(m: types.Message, state: FSMContext):
    await state.update_data(video_id=m.video.file_id)
    await m.answer("📝 Video uchun tavsif yozing:")
    await state.set_state(VideoUpload.waiting_for_caption)

@dp.message(VideoUpload.waiting_for_caption)
async def process_caption(m: types.Message, state: FSMContext):
    await state.update_data(caption=m.text)
    btns = [[InlineKeyboardButton(text="Yumor", callback_data="cat_yumor"), InlineKeyboardButton(text="Ta'lim", callback_data="cat_talim")]]
    await m.answer("📂 Kategoriyani tanlang:", reply_markup=InlineKeyboardMarkup(inline_keyboard=btns))
    await state.set_state(VideoUpload.waiting_for_category)

@dp.callback_query(F.data.startswith("cat_"))
async def save_video(call: types.CallbackQuery, state: FSMContext):
    cat = call.data.split("_")[1]
    data = await state.get_data()
    status = await call.message.edit_text("⏳ Tezkor yuklanmoqda...")
    
    try:
        # Aiohttp orqali tezkor yuklash
        file = await bot.get_file(data['video_id'])
        file_url = f"https://api.telegram.org/file/bot{TOKEN}/{file.file_path}"
        
        async with aiohttp.ClientSession() as session:
            async with session.get(file_url) as resp:
                if resp.status == 200:
                    content = await resp.read()
                    f_name = f"v_{datetime.now().strftime('%H%M%S')}.mp4"
                    
                    # Supabase-ga yuborish
                    supabase.storage.from_("videos").upload(f_name, content, {"content-type": "video/mp4"})
                    url_obj = supabase.storage.from_("videos").get_public_url(f_name)
                    final_url = url_obj.public_url if hasattr(url_obj, 'public_url') else str(url_obj)
                    
                    # Firebase-ga yozish
                    db.reference('videos').push({
                        'file_url': final_url,
                        'user': call.from_user.username or call.from_user.full_name,
                        'caption': data['caption'],
                        'category': cat,
                        'channel_link': f"https://t.me/{call.from_user.username}" if call.from_user.username else "https://t.me/telegram"
                    })
                    await status.edit_text("✅ Muvaffaqiyatli yuklandi!")
    except Exception as e:
        await status.edit_text(f"❌ Xatolik: {e}")
    await state.clear()

async def handle(r): return web.Response(text="Bot is Active")

async def main():
    app = web.Application()
    app.router.add_get("/", handle)
    runner = web.AppRunner(app); await runner.setup()
    await web.TCPSite(runner, "0.0.0.0", int(os.environ.get("PORT", 10000))).start()
    
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
