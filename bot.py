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
    
    if len(args) > 1:
        video_id = args[1]
        web_url += f"?start={video_id}"

    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="🎬 UzReels-ni ochish", web_app=WebAppInfo(url=web_url)))
    await message.answer(f"Salom {message.from_user.full_name}!\nUzReels-da eng qaynoq videolarni tomosha qiling.", reply_markup=builder.as_markup())

# --- VIDEO QABUL QILISH VA RUKN SO'RASH ---
@dp.message(F.video)
async def ask_category(message: types.Message):
    builder = InlineKeyboardBuilder()
    categories = ["Futbol", "Qiziqarli", "Texno", "Boshqa"]
    for cat in categories:
        builder.button(text=cat, callback_data=f"c_{cat}")
    builder.adjust(2)
    await message.reply("Ushbu video qaysi ruknga tegishli?", reply_markup=builder.as_markup())

# --- KANAL NOMIDAN YOKI PROFIL NOMIDAN SAQLASH ---
@dp.callback_query(F.data.startswith("c_"))
async def save_video_final(callback: types.CallbackQuery):
    cat = callback.data.split("_")[1]
    msg = callback.message.reply_to_message
    
    try:
        file = await bot.get_file(msg.video.file_id)
        download_url = f"https://api.telegram.org/file/bot{TOKEN}/{file.file_path}"
        
        caption = msg.caption or ""
        # Agar tavsifda @kanal bo'lsa, o'shani muallif qilamiz, aks holda user ismini
        author = msg.from_user.full_name
        words = caption.split()
        for word in words:
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
            'date': msg.date.strftime("%Y-%m-%d %H:%M")
        })
        await callback.message.edit_text(f"✅ Video '{author}' nomidan '{cat}' rukniga qo'shildi!")
    except Exception as e:
        await callback.message.edit_text(f"❌ Xato yuz berdi: {e}")

async def main():
    app = web.Application()
    app.router.add_get('/', handle)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', int(os.getenv("PORT", 10000)))
    await asyncio.gather(site.start(), dp.start_polling(bot))

if __name__ == "__main__":
    asyncio.run(main())
