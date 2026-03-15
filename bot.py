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

# Firebase sozlamalari
cred_path = "/opt/render/project/src/firebase-key.json"
firebase_url = "https://uzreels-bot-default-rtdb.europe-west1.firebasedatabase.app/"

if not firebase_admin._apps:
    cred = credentials.Certificate(cred_path)
    firebase_admin.initialize_app(cred, {'databaseURL': firebase_url})

TOKEN = os.getenv("BOT_TOKEN")
bot = Bot(token=TOKEN)
dp = Dispatcher()

# YouTube va Instagram linklarini ajratish uchun oddiy tekshiruv
def get_embed_url(original_url):
    if "youtube.com" in original_url or "youtu.be" in original_url:
        # Shorts linkini Embed ko'rinishiga keltirish
        if "shorts/" in original_url:
            video_id = original_url.split("shorts/")[1].split("?")[0]
            return f"https://www.youtube.com/embed/{video_id}?autoplay=1&loop=1&playlist={video_id}"
    elif "instagram.com" in original_url:
        # Instagram Reels uchun (Eslatma: Instagram embed qilishni cheklashi mumkin)
        if "/reels/" in original_url or "/reel/" in original_url:
            clean_url = original_url.split("?")[0]
            return f"{clean_url}embed/"
    return original_url

@dp.message(F.text.contains("http"))
async def process_link(message: types.Message):
    url = get_embed_url(message.text)
    builder = InlineKeyboardBuilder()
    for cat in ["Futbol", "Qiziqarli", "Texno", "Boshqa"]:
        builder.button(text=cat, callback_data=f"save_{cat}")
    builder.adjust(2)
    # Vaqtinchalik linkni foydalanuvchi ma'lumotlarida saqlab turamiz
    await message.reply(f"Link qabul qilindi. Ruknni tanlang:", reply_markup=builder.as_markup())

@dp.callback_query(F.data.startswith("save_"))
async def save_link(callback: types.CallbackQuery):
    cat = callback.data.split("_")[1]
    msg = callback.message.reply_to_message # Bu foydalanuvchi yuborgan link
    
    final_url = get_embed_url(msg.text)
    
    db.reference('videos').push({
        'url': final_url,
        'type': 'youtube' if 'youtube' in final_url else 'instagram',
        'user': callback.from_user.full_name,
        'category': cat,
        'date': datetime.now().strftime("%Y-%m-%d %H:%M")
    })
    await callback.message.edit_text(f"✅ Link '{cat}' rukniga saqlandi!")

async def main():
    app = web.Application()
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', int(os.getenv("PORT", 10000)))
    await asyncio.gather(site.start(), dp.start_polling(bot))

if __name__ == "__main__":
    asyncio.run(main())
