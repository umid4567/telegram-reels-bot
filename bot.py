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
from datetime import datetime

logging.basicConfig(level=logging.INFO)

cred_path = "/opt/render/project/src/firebase-key.json"
firebase_url = "https://uzreels-bot-default-rtdb.europe-west1.firebasedatabase.app/"

if not firebase_admin._apps:
    if os.path.exists(cred_path):
        cred = credentials.Certificate(cred_path)
        firebase_admin.initialize_app(cred, {'databaseURL': firebase_url})

TOKEN = os.getenv("BOT_TOKEN")
bot = Bot(token=TOKEN)
dp = Dispatcher()

async def handle(request):
    return web.Response(text="UzReels Bot is active!")

def get_embed_url(url):
    # YouTube Shorts va Video
    if "youtube.com" in url or "youtu.be" in url:
        if "shorts/" in url:
            video_id = url.split("shorts/")[1].split("?")[0]
            return f"https://www.youtube.com/embed/{video_id}?autoplay=1&rel=0&loop=1&playlist={video_id}"
        elif "v=" in url:
            video_id = url.split("v=")[1].split("&")[0]
            return f"https://www.youtube.com/embed/{video_id}?autoplay=1"
    # Instagram Reels va Post
    elif "instagram.com" in url:
        clean_url = url.split("?")[0]
        if not clean_url.endswith("/"): clean_url += "/"
        # caption=0 ortiqcha yozuvlarni olib tashlaydi
        return f"{clean_url}embed/?captioned=0"
    return url

@dp.message(CommandStart())
async def start(message: types.Message):
    web_url = "https://umid4567.github.io/telegram-reels-bot/"
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="🎬 UzReels-ni ochish", web_app=WebAppInfo(url=web_url)))
    await message.answer(f"Salom! Link yuboring (YouTube/Instagram).", reply_markup=builder.as_markup())

@dp.message(F.text.contains("http"))
async def process_link(message: types.Message):
    builder = InlineKeyboardBuilder()
    for cat in ["Futbol", "Qiziqarli", "Texno", "Boshqa"]:
        builder.button(text=cat, callback_data=f"save_{cat}")
    builder.adjust(2)
    await message.reply("Ruknni tanlang:", reply_markup=builder.as_markup())

@dp.callback_query(F.data.startswith("save_"))
async def save_link(callback: types.CallbackQuery):
    cat = callback.data.split("_")[1]
    original_msg = callback.message.reply_to_message
    
    if not original_msg:
        await callback.message.edit_text("❌ Xato: Asl link topilmadi.")
        return

    embed_url = get_embed_url(original_msg.text)
    
    try:
        db.reference('videos').push({
            'url': embed_url,
            'user': callback.from_user.full_name,
            'caption': original_msg.caption or "",
            'category': cat,
            'date': datetime.now().strftime("%Y-%m-%d %H:%M")
        })
        await callback.message.edit_text(f"✅ '{cat}' rukniga saqlandi!")
    except Exception as e:
        await callback.message.edit_text(f"❌ Xato: {e}")

async def main():
    app = web.Application()
    app.router.add_get('/', handle)
    runner = web.AppRunner(app)
    await runner.setup()
    
    port = int(os.getenv("PORT", 10000))
    site = web.TCPSite(runner, '0.0.0.0', port)
    
    await bot.delete_webhook(drop_pending_updates=True)
    await site.start()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
