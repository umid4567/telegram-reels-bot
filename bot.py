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

# Firebase sozlamalari
cred_path = "firebase-key.json" # Fayl asosiy papkada bo'lishi kerak
firebase_url = "https://uzreels-bot-default-rtdb.europe-west1.firebasedatabase.app/"

if not firebase_admin._apps:
    if os.path.exists(cred_path):
        cred = credentials.Certificate(cred_path)
        firebase_admin.initialize_app(cred, {'databaseURL': firebase_url})

TOKEN = os.getenv("BOT_TOKEN")
bot = Bot(token=TOKEN)
dp = Dispatcher()

async def handle(request):
    return web.Response(text="Bot is running!")

def get_embed_url(url):
    video_id = ""
    if "shorts/" in url:
        video_id = url.split("shorts/")[1].split("?")[0]
    elif "v=" in url:
        video_id = url.split("v=")[1].split("&")[0]
    
    if video_id:
        # Loop va Autoplay uchun embed link
        return f"https://www.youtube.com/embed/{video_id}?rel=0&iv_load_policy=3&showinfo=0&controls=1&loop=1&playlist={video_id}"
    return None

@dp.message(CommandStart())
async def start(message: types.Message):
    web_url = "https://umid4567.github.io/telegram-reels-bot/"
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="🎬 Shorts ko'rish", web_app=WebAppInfo(url=web_url)))
    await message.answer(f"Salom {message.from_user.full_name}!\nYouTube Shorts linkini yuboring.", reply_markup=builder.as_markup())

@dp.message(F.text.contains("http"))
async def process_link(message: types.Message):
    if "youtube" not in message.text and "youtu.be" not in message.text:
        await message.reply("Iltimos, faqat YouTube linkini yuboring!")
        return

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
        await callback.message.edit_text("❌ Xatolik: Link topilmadi.")
        return

    embed_url = get_embed_url(original_msg.text)
    if not embed_url:
        await callback.message.edit_text("❌ Noto'g'ri YouTube linki.")
        return
    
    try:
        db.reference('videos').push({
            'url': embed_url,
            'user': callback.from_user.username or callback.from_user.full_name,
            'category': cat,
            'caption': original_msg.caption or "",
            'date': datetime.now().strftime("%Y-%m-%d %H:%M")
        })
        await callback.message.edit_text(f"✅ Saqlandi! Rukn: {cat}")
    except Exception as e:
        await callback.message.edit_text(f"❌ Firebase xatosi: {e}")

async def main():
    app = web.Application()
    app.router.add_get('/', handle)
    runner = web.AppRunner(app)
    await runner.setup()
    
    port = int(os.getenv("PORT", 10000))
    site = web.TCPSite(runner, '0.0.0.0', port)
    
    await bot.delete_webhook(drop_pending_updates=True)
    await site.start()
    
    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()
        await runner.cleanup()

if __name__ == "__main__":
    asyncio.run(main())
