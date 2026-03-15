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

# 1. Loggingni yoqish (xatolarni ko'rish uchun)
logging.basicConfig(level=logging.INFO)

# 2. Firebase sozlamalari
cred_path = "/opt/render/project/src/firebase-key.json"
firebase_url = "https://uzreels-bot-default-rtdb.europe-west1.firebasedatabase.app/"

if not firebase_admin._apps:
    if os.path.exists(cred_path):
        cred = credentials.Certificate(cred_path)
        firebase_admin.initialize_app(cred, {'databaseURL': firebase_url})
    else:
        logging.error("Firebase key topilmadi!")

TOKEN = os.getenv("BOT_TOKEN")
bot = Bot(token=TOKEN)
dp = Dispatcher()

# Render uchun oddiy web sahifa
async def handle(request):
    return web.Response(text="UzReels Bot is active!")

# Linkni Embed (pleyer) holatiga keltirish
def get_embed_url(url):
    if "youtube.com" in url or "youtu.be" in url:
        if "shorts/" in url:
            video_id = url.split("shorts/")[1].split("?")[0]
            return f"https://www.youtube.com/embed/{video_id}?autoplay=1&rel=0"
        elif "v=" in url:
            video_id = url.split("v=")[1].split("&")[0]
            return f"https://www.youtube.com/embed/{video_id}?autoplay=1"
    elif "instagram.com" in url:
        if "/reels/" in url or "/reel/" in url or "/p/" in url:
            clean_url = url.split("?")[0]
            if not clean_url.endswith("/"): clean_url += "/"
            return f"{clean_url}embed/"
    return url

@dp.message(CommandStart())
async def start(message: types.Message):
    web_url = "https://umid4567.github.io/telegram-reels-bot/"
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="🎬 UzReels-ni ochish", web_app=WebAppInfo(url=web_url)))
    await message.answer(f"Salom {message.from_user.full_name}!\nYouTube Shorts yoki Instagram linkini yuboring.", reply_markup=builder.as_markup())

@dp.message(F.text.contains("http"))
async def process_link(message: types.Message):
    builder = InlineKeyboardBuilder()
    for cat in ["Futbol", "Qiziqarli", "Texno", "Boshqa"]:
        builder.button(text=cat, callback_data=f"save_{cat}")
    builder.adjust(2)
    await message.reply("Link qabul qilindi. Ruknni tanlang:", reply_markup=builder.as_markup())

@dp.callback_query(F.data.startswith("save_"))
async def save_link(callback: types.CallbackQuery):
    cat = callback.data.split("_")[1]
    # callback.message.reply_to_message orqali asl linkni olamiz
    original_msg = callback.message.reply_to_message
    
    if not original_msg or not original_msg.text:
        await callback.message.edit_text("❌ Xatolik: Asl xabar topilmadi.")
        return

    embed_url = get_embed_url(original_msg.text)
    video_type = 'youtube' if 'youtube' in embed_url else 'instagram'
    
    try:
        db.reference('videos').push({
            'url': embed_url,
            'type': video_type,
            'user': callback.from_user.full_name,
            'category': cat,
            'date': datetime.now().strftime("%Y-%m-%d %H:%M")
        })
        await callback.message.edit_text(f"✅ Video '{cat}' rukniga muvaffaqiyatli saqlandi!")
    except Exception as e:
        await callback.message.edit_text(f"❌ Firebase xatosi: {e}")

async def main():
    # Web serverni sozlash (Render uchun)
    app = web.Application()
    app.router.add_get('/', handle)
    runner = web.AppRunner(app)
    await runner.setup()
    
    port = int(os.getenv("PORT", 10000))
    site = web.TCPSite(runner, '0.0.0.0', port)
    
    logging.info(f"Bot start port: {port}")
    await site.start()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
