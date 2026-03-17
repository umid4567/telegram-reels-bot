import os
import asyncio
import requests
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

def get_category_keyboard():
    btns = [
        [InlineKeyboardButton(text="Yangiliklar", callback_data="cat_yangiliklar"), InlineKeyboardButton(text="Yumor", callback_data="cat_yumor")],
        [InlineKeyboardButton(text="Ta'lim", callback_data="cat_talim"), InlineKeyboardButton(text="Texno", callback_data="cat_texno")],
        [InlineKeyboardButton(text="Qiziqarli", callback_data="cat_qiziqarli"), InlineKeyboardButton(text="Boshqa", callback_data="cat_boshqa")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=btns)

@dp.message(CommandStart())
async def start(m: types.Message):
    args = m.text.split()
    video_id = args[1] if len(args) > 1 else None
    
    # Web App linkiga start parametrini qo'shish
    base_url = "https://umid4567.github.io/telegram-reels-bot/"
    web_url = f"{base_url}?start={video_id}" if video_id else base_url
    
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎬 Videoni ko'rish" if video_id else "🎬 UzReels-ni ochish", web_app=WebAppInfo(url=web_url))]
    ])
    
    txt = "Sizga yangi video yuborishdi! Ko'rish uchun bosing 👇" if video_id else "UzReels-ga xush kelibsiz! Video yuboring."
    await m.answer(txt, reply_markup=kb)

# --- INLINE QUERY ---
@dp.inline_query()
async def inline_handler(query: types.InlineQuery):
    videos_ref = db.reference('videos').get()
    results = []
    if videos_ref:
        video_list = [{"id": k, **v} for k, v in videos_ref.items()]
        # Qidiruv maydoniga ID yozilgan bo'lsa yoki oxirgi videolar
        q = query.query.strip()
        items_to_show = [v for v in video_list if v['id'] == q] if q else video_list[-10:]
        
        for item in reversed(items_to_show):
            # Botga qaytadigan link
            bot_me = await bot.get_me()
            share_link = f"https://t.me/{bot_me.username}?start={item['id']}"
            
            results.append(InlineQueryResultVideo(
                id=item['id'],
                video_url=item['file_url'],
                mime_type="video/mp4",
                thumbnail_url="https://raw.githubusercontent.com/umid4567/telegram-reels-bot/main/thumb.jpg",
                title=item.get('caption', 'UzReels'),
                caption=f"🎬 {item.get('caption', '')}\n\nKo'rish uchun: {share_link}"
            ))
    await query.answer(results, is_personal=True, cache_time=5)

@dp.message(F.video)
async def process_video(m: types.Message, state: FSMContext):
    await state.update_data(video_id=m.video.file_id)
    await m.answer("📝 Video uchun tavsif yozing:")
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
    status = await call.message.edit_text("⏳ Yuklanmoqda...")
    
    try:
        file = await bot.get_file(data['video_id'])
        content = requests.get(f"https://api.telegram.org/file/bot{TOKEN}/{file.file_path}").content
        f_name = f"r_{datetime.now().strftime('%H%M%S')}.mp4"
        supabase.storage.from_("videos").upload(f_name, content, {"content-type": "video/mp4"})
        url = supabase.storage.from_("videos").get_public_url(f_name)
        
        db.reference('videos').push({
            'file_url': url.public_url if hasattr(url, 'public_url') else str(url),
            'user': call.from_user.username or call.from_user.full_name,
            'caption': data['caption'],
            'category': cat,
            'channel_link': f"https://t.me/{call.from_user.username}" if call.from_user.username else "https://t.me/telegram"
        })
        await status.edit_text("✅ UzReels-ga qo'shildi!")
    except Exception as e:
        await status.edit_text(f"❌ Xato: {e}")
    await state.clear()

async def handle(r): return web.Response(text="Running")
async def main():
    app = web.Application()
    app.router.add_get("/", handle)
    runner = web.AppRunner(app); await runner.setup()
    await web.TCPSite(runner, "0.0.0.0", int(os.environ.get("PORT", 10000))).start()
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
