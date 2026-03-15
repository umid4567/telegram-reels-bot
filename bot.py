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

# 1. Firebase sozlamalari
cred_path = "/opt/render/project/src/firebase-key.json"
firebase_url = "https://uzreels-bot-default-rtdb.europe-west1.firebasedatabase.app/"

if not firebase_admin._apps:
    if os.path.exists(cred_path):
        cred = credentials.Certificate(cred_path)
        firebase_admin.initialize_app(cred, {'databaseURL': firebase_url})

TOKEN = os.getenv("BOT_TOKEN")
bot = Bot(token=TOKEN)
dp = Dispatcher()
logging.basicConfig(level=logging.INFO)

async def handle(request):
    return web.Response(text="UzReels Bot is Running!")

@dp.message(CommandStart())
async def start(message: types.Message):
    args = message.text.split()
    web_url = "https://umid4567.github.io/telegram-reels-bot/"
    
    if len(args) > 1:
        web_url += f"?start={args[1]}"

    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="🎬 UzReels-ni ochish", web_app=WebAppInfo(url=web_url)))
    await message.answer(f"Salom {message.from_user.full_name}!\nUzReels-da eng sara videolarni tomosha qiling.", reply_markup=builder.as_markup())

@dp.message(F.video)
async def ask_category(message: types.Message):
    builder = InlineKeyboardBuilder()
    categories = ["Futbol", "Qiziqarli", "Texno", "Boshqa"]
    for cat in categories:
        builder.button(text=cat, callback_data=f"c_{cat}")
    builder.adjust(2)
    await message.reply("Ushbu video qaysi ruknga tegishli?", reply_markup=builder.as_markup())

@dp.callback_query(F.data.startswith("c_"))
async def save_video_final(callback: types.CallbackQuery):
    cat = callback.data.split("_")[1]
    msg = callback.message.reply_to_message
    
    try:
        # Videoni Telegram serveridagi yo'lini olish
        file = await bot.get_file(msg.video.file_id)
        # To'g'ridan-to'g'ri yuklash havolasi
        download_url = f"https://api.telegram.org/file/bot{TOKEN}/{file.file_path}"
        
        caption = msg.caption or ""
        author = msg.from_user.full_name
        
        # Kanal nomini captiondan qidirish
        for word in caption.split():
            if word.startswith("@"):
                author = word
                break

        ref = db.reference('videos')
        ref.push({
            'url': download_url,
            'user': author,
            'caption': caption,
            'category': cat,
            'likes': {},
            'date': datetime.now().strftime("%Y-%m-%d %H:%M")
        })
        await callback.message.edit_text(f"✅ Video '{author}' nomidan saqlandi!")
    except Exception as e:
        logging.error(f"Error: {e}")
        await callback.message.edit_text(f"❌ Xato: {e}")

async def main():
    app = web.Application()
    app.router.add_get('/', handle)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', int(os.getenv("PORT", 10000)))
    await asyncio.gather(site.start(), dp.start_polling(bot))

if __name__ == "__main__":
    asyncio.run(main())
