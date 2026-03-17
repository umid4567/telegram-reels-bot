import os
import asyncio
import requests
import logging
from datetime import datetime
from aiohttp import web

from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart
from aiogram.types import WebAppInfo, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from supabase import create_client, Client
import firebase_admin
from firebase_admin import credentials, db

# Loglar
logging.basicConfig(level=logging.INFO)

# --- SOZLAMALAR ---
SUPABASE_URL = "https://tgzywqgimxwkavmdwgnc.supabase.co"
SUPABASE_KEY = "EY..." # O'zingizni kalitingizni qoldiring
TOKEN = os.getenv("BOT_TOKEN")

# Ma'lumotlar bazasi
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

if not firebase_admin._apps:
    cred = credentials.Certificate("firebase-key.json")
    firebase_admin.initialize_app(cred, {
        'databaseURL': "https://uzreels-bot-default-rtdb.europe-west1.firebasedatabase.app/"
    })

bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()

# --- FSM (Holatlar) ---
class VideoUpload(StatesGroup):
    waiting_for_caption = State()
    waiting_for_category = State()

# --- KLAVIATURALAR ---
def get_category_keyboard():
    buttons = [
        [InlineKeyboardButton(text="Yangiliklar", callback_data="cat_yangiliklar"),
         InlineKeyboardButton(text="Yumor", callback_data="cat_yumor")],
        [InlineKeyboardButton(text="Ta'lim", callback_data="cat_talim"),
         InlineKeyboardButton(text="Texno", callback_data="cat_texno")],
        [InlineKeyboardButton(text="Qiziqarli", callback_data="cat_qiziqarli"),
         InlineKeyboardButton(text="Boshqa", callback_data="cat_boshqa")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

# --- SOXTA SERVER (Render uchun) ---
async def handle(request): return web.Response(text="Bot is running!")
async def start_web_server():
    app = web.Application()
    app.router.add_get("/", handle)
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.environ.get("PORT", 10000))
    await web.TCPSite(runner, "0.0.0.0", port).start()

# --- BOT TRANSAKSIYALARI ---

@dp.message(CommandStart())
async def start(message: types.Message):
    web_url = "https://umid4567.github.io/telegram-reels-bot/"
    builder = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎬 UzReels-ni ochish", web_app=WebAppInfo(url=web_url))]
    ])
    await message.answer(f"Salom! Video yuboring va men uni platformaga joylayman.", reply_markup=builder)

# 1. Video yuborilganda
@dp.message(F.video)
async def process_video(message: types.Message, state: FSMContext):
    # Videoni vaqtincha saqlash
    await state.update_data(video_file_id=message.video.file_id)
    await message.answer("📝 Video uchun qisqacha tavsif (caption) yozing:")
    await state.set_state(VideoUpload.waiting_for_caption)

# 2. Tavsif yozilganda
@dp.message(VideoUpload.waiting_for_caption)
async def process_caption(message: types.Message, state: FSMContext):
    await state.update_data(caption=message.text)
    await message.answer("📂 Kategoriyani tanlang:", reply_markup=get_category_keyboard())
    await state.set_state(VideoUpload.waiting_for_category)

# 3. Kategoriya tanlanganda va yuklash
@dp.callback_query(F.data.startswith("cat_"))
async def process_category(callback: types.CallbackQuery, state: FSMContext):
    category = callback.data.split("_")[1]
    data = await state.get_data()
    caption = data.get('caption')
    file_id = data.get('video_file_id')

    await callback.message.edit_text(f"⏳ {category.capitalize()} kategoriyasiga yuklanmoqda...")

    try:
        # Supabase-ga yuklash qismi
        file = await bot.get_file(file_id)
        video_url_tg = f"https://api.telegram.org/file/bot{TOKEN}/{file.file_path}"
        video_content = requests.get(video_url_tg).content
        
        file_name = f"reel_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4"
        supabase.storage.from_("videos").upload(path=file_name, file=video_content, file_options={"content-type": "video/mp4"})
        
        video_public_url = supabase.storage.from_("videos").get_public_url(file_name)
        if not isinstance(video_public_url, str): video_public_url = video_public_url.public_url

        # Firebase-ga saqlash
        db.reference('videos').push({
            'file_url': video_public_url,
            'user': callback.from_user.username or callback.from_user.full_name,
            'caption': caption,
            'category': category,
            'channel_link': f"https://t.me/{callback.from_user.username}" if callback.from_user.username else "",
            'date': datetime.now().strftime("%Y-%m-%d %H:%M")
        })

        await callback.message.answer("✅ Video muvaffaqiyatli UzReels-ga qo'shildi!")
        await state.clear()
        
    except Exception as e:
        await callback.message.answer(f"❌ Xatolik: {e}")
        await state.clear()

# --- ASOSIY ---
async def main():
    asyncio.create_task(start_web_server())
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
