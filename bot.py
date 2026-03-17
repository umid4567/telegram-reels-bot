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

def get_category_keyboard():
    btns = [
        [InlineKeyboardButton(text="Yangiliklar", callback_data="cat_yangiliklar"), InlineKeyboardButton(text="Yumor", callback_data="cat_yumor")],
        [InlineKeyboardButton(text="Ta'lim", callback_data="cat_talim"), InlineKeyboardButton(text="Texno", callback_data="cat_texno")],
        [InlineKeyboardButton(text="Qiziqarli", callback_data="cat_qiziqarli"), InlineKeyboardButton(text="Boshqa", callback_data="cat_boshqa")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=btns)

@dp.message(CommandStart())
async def start(m: types.Message):
    web_url = "https://umid4567.github.io/telegram-reels-bot/"
    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🎬 UzReels-ni ochish", web_app=WebAppInfo(url=web_url))]])
    await m.answer("Salom! Video yuboring va men uni UzReels-ga joylayman.", reply_markup=kb)

@dp.message(F.video)
async def process_video(m: types.Message, state: FSMContext):
    await state.update_data(video_id=m.video.file_id)
    await m.answer("📝 Video uchun qisqacha tavsif yozing:")
    await state.set_state(VideoUpload.waiting_for_caption)

@dp.message(VideoUpload.waiting_for_caption)
async def process_caption(m: types.Message, state: FSMContext):
    await state.update_data(caption=m.text)
    await m.answer("📂 Kategoriyani tanlang:", reply_markup=get_category_keyboard())
    await state.set_state(VideoUpload.waiting_for_category)

@dp.callback_query(F.data.startswith("cat_"))
async def save_video(call: types.CallbackQuery, state: FSMContext):
    cat = call.data.split("_")[1]
    data = await state.get_data()
    
    # Yuklash boshlanganini ko'rsatish
    status_msg = await call.message.edit_text("⏳ Yuklanmoqda, iltimos kuting...")
    
    try:
        file = await bot.get_file(data['video_id'])
        content = requests.get(f"https://api.telegram.org/file/bot{TOKEN}/{file.file_path}").content
        f_name = f"r_{datetime.now().strftime('%H%M%S')}.mp4"
        
        # Supabase yuklash
        supabase.storage.from_("videos").upload(f_name, content, {"content-type": "video/mp4"})
        url_res = supabase.storage.from_("videos").get_public_url(f_name)
        
        # URL formatini tekshirish
        final_url = url_res.public_url if hasattr(url_res, 'public_url') else str(url_res)
        
        db.reference('videos').push({
            'file_url': final_url,
            'user': call.from_user.username or call.from_user.full_name,
            'caption': data['caption'],
            'category': cat,
            'channel_link': f"https://t.me/{call.from_user.username}" if call.from_user.username else "https://t.me/telegram"
        })
        await status_msg.edit_text("✅ Video muvaffaqiyatli UzReels-ga joylandi!")
    except Exception as e:
        await status_msg.edit_text(f"❌ Xato: {e}")
    await state.clear()

# --- SERVER QISMI ---
async def handle(request): 
    return web.Response(text="UzReels Bot is Alive!")

async def main():
    # 1. Web serverni ishga tushirish (Render to'xtab qolmasligi uchun)
    app = web.Application()
    app.router.add_get("/", handle)
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.environ.get("PORT", 10000))
    await web.TCPSite(runner, "0.0.0.0", port).start()

    # 2. Konfliktni oldini olish uchun eski webhooklarni o'chirish
    await bot.delete_webhook(drop_pending_updates=True)
    
    # 3. Polling boshlash
    logging.info("Bot ishga tushdi...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logging.info("Bot to'xtatildi.")
