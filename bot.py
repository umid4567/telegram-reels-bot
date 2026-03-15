import os
import logging
import asyncio
import firebase_admin
from firebase_admin import credentials, db
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart
from aiogram.types import WebAppInfo, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiohttp import web

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
    return web.Response(text="Bot ishlamoqda!")

# --- DEEP LINKING BILAN START ---
@dp.message(CommandStart())
async def start(message: types.Message):
    args = message.text.split()
    web_url = "https://umid4567.github.io/telegram-reels-bot/"
    
    # Agar do'sti yuborgan link orqali kirsa (/start videoID)
    if len(args) > 1:
        video_id = args[1]
        web_url += f"?start={video_id}" # Web App-ga ID-ni uzatish

    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(
        text="🎬 Videoni ko'rish", 
        web_app=WebAppInfo(url=web_url))
    )
    
    await message.answer(
        f"Salom {message.from_user.full_name}!\nUzReels-ga xush kelibsiz. Videoni ko'rish uchun pastdagi tugmani bosing.", 
        reply_markup=builder.as_markup()
    )

@dp.message(F.video)
async def ask_category(message: types.Message):
    builder = InlineKeyboardBuilder()
    categories = ["Futbol", "Qiziqarli", "Texno", "Boshqa"]
    for cat in categories:
        builder.button(text=cat, callback_data=f"c_{cat}")
    builder.adjust(2)
    await message.reply("Ushbu video qaysi ruknga tegishli?", reply_markup=builder.as_markup())

@dp.callback_query(F.data.startswith("c_"))
async def save_video_with_cat(callback: types.CallbackQuery):
    cat = callback.data.split("_")[1]
    msg = callback.message.reply_to_message
    
    try:
        file = await bot.get_file(msg.video.file_id)
        download_url = f"https://api.telegram.org/file/bot{TOKEN}/{file.file_path}"
        
        ref = db.reference('videos')
        ref.push({
            'url': download_url,
            'user': msg.from_user.full_name or "Foydalanuvchi",
            'username': msg.from_user.username or "user",
            'caption': msg.caption or "Video",
            'category': cat,
            'date': msg.date.strftime("%Y-%m-%d %H:%M")
        })
        await callback.message.edit_text(f"✅ Video '{cat}' rukniga qo'shildi!")
    except Exception as e:
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
