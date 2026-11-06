import os
import asyncio
import logging
import html
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart, Command
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.types import FSInputFile, CallbackQuery

import config
import music_service
import keyboards

# Loglarni sozlash
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

bot = Bot(
    token=config.BOT_TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML)
)
dp = Dispatcher()

@dp.message(CommandStart())
async def cmd_start(message: types.Message):
    user_name = html.escape(message.from_user.first_name or "Do'stim")
    text = (
        f"Salom, <b>{user_name}</b>! 🎧\n\n"
        f"Men musiqa qidirish va yuklab berish botiman. "
        f"Mening bazamda <b>millionlab qo'shiqlar</b> mavjud!\n\n"
        f"🎵 <b>Qo'shiq topish uchun:</b>\n"
        f"Shunchaki qo'shiq nomi, ijrochi yoki YouTube havolasini yozib yuboring.\n\n"
        f"<i>Masalan:</i>\n"
        f"• <code>Konsta</code>\n"
        f"• <code>Xamdam Sobirov</code>\n"
        f"• <code>Imagine Dragons Believer</code>\n\n"
        f"Qani, xohlagan qo'shiq nomini yozing! 👇"
    )
    await message.answer(text)

@dp.message(Command("help"))
async def cmd_help(message: types.Message):
    text = (
        "💡 <b>Botdan qanday foydalaniladi?</b>\n\n"
        "1. Menga istalgan qo'shiq yoki san'atkor nomini yuboring.\n"
        "2. Bot sizga eng mos 5 ta variantni chiqarib beradi.\n"
        "3. Raqamli tugmalardan (1️⃣, 2️⃣, 3️⃣...) birini bosing.\n"
        "4. Bot musiqani MP3 holatida tayyorlab, sizga yuboradi!\n\n"
        "Shuningdek, YouTube havolasini yuborsangiz ham to'g'ridan-to'g'ri MP3 yuklab beradi."
    )
    await message.answer(text)

@dp.message(F.text)
async def handle_music_query(message: types.Message):
    query = message.text.strip()
    if not query:
        return

    # 1. Agar YouTube link bo'lsa
    yt_id = music_service.extract_youtube_id(query)
    if yt_id:
        status_msg = await message.answer("⏳ <b>Musiqa yuklab olinmoqda...</b> Iltimos, kuting.")
        try:
            track = await music_service.async_download_audio(yt_id)
            audio_file = FSInputFile(track['file_path'])
            await message.answer_audio(
                audio=audio_file,
                title=track['title'],
                performer=track['uploader'],
                duration=track['duration'],
                caption="🎶 <b>@cheater_000bot</b> orqali yuklab olindi"
            )
            await status_msg.delete()
            # Diskni toza saqlash uchun yuklangan faylni o'chiramiz
            if os.path.exists(track['file_path']):
                try:
                    os.remove(track['file_path'])
                except Exception:
                    pass
        except Exception as e:
            logger.error(f"Yuklashda xatolik: {e}")
            await status_msg.edit_text("❌ Musiqani yuklab olishda xatolik yuz berdi. Boshqa havola yuborib ko'ring.")
        return

    # 2. Qo'shiq nomi bo'yicha qidiruv
    status_msg = await message.answer(f"🔍 <i>\"{html.escape(query)}\"</i> bo'yicha qidirilmoqda...")
    try:
        results = await music_service.async_search_music(query, limit=5)
        if not results:
            await status_msg.edit_text("❌ Hech qanday musiqa topilmadi. Iltimos, boshqacha nom bilan qidirib ko'ring.")
            return

        text = f"🎵 <b>\"{html.escape(query)}\" bo'yicha topilgan taronalar:</b>\n\n"
        emojis = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣"]
        for i, item in enumerate(results):
            emo = emojis[i] if i < len(emojis) else f"{i+1}."
            text += f"{emo} <b>{item['escaped_title']}</b> [{item['duration_str']}]\n"

        text += "\n👇 <i>Yuklab olish uchun pastdagi mos raqamni bosing:</i>"
        kb = keyboards.get_search_results_keyboard(results)
        await status_msg.edit_text(text, reply_markup=kb)

    except Exception as e:
        logger.error(f"Qidiruvda xatolik: {e}")
        await status_msg.edit_text("❌ Qidiruvda xatolik yuz berdi. Qayta urinib ko'ring.")

@dp.callback_query(F.data.startswith("dl:"))
async def handle_download_callback(callback: CallbackQuery):
    video_id = callback.data.split(":")[1]
    await callback.answer("⏳ Qo'shiq yuklanmoqda...")
    
    status_msg = await callback.message.reply("⏳ <b>Musiqa tayyorlanmoqda va yuklanmoqda...</b>")
    try:
        track = await music_service.async_download_audio(video_id)
        audio_file = FSInputFile(track['file_path'])
        
        await callback.message.answer_audio(
            audio=audio_file,
            title=track['title'],
            performer=track['uploader'],
            duration=track['duration'],
            caption="🎶 <b>@cheater_000bot</b> orqali yuklab olindi"
        )
        await status_msg.delete()

        # Faylni diskdan tozalash
        if os.path.exists(track['file_path']):
            try:
                os.remove(track['file_path'])
            except Exception:
                pass
    except Exception as e:
        logger.error(f"Callback yuklashda xatolik: {e}")
        await status_msg.edit_text("❌ Musiqani yuklab olishda xatolik yuz berdi. Iltimos, boshqa qatorni tanlab ko'ring.")

async def start_web_server():
    """Render bepul tarifida Port ochish va sog'lomlik tekshiruvi (Health Check) uchun"""
    from aiohttp import web
    
    async def handle_ping(request):
        return web.Response(text="Bot is running! 200 OK")

    port = int(os.environ.get("PORT", 8080))
    app = web.Application()
    app.router.add_get("/", handle_ping)
    app.router.add_get("/health", handle_ping)
    
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    logger.info(f"Render uchun Web server {port}-portda ishga tushdi.")

async def main():
    logger.info("Bot ishga tushmoqda...")
    
    # Agar Render yoki boshqa bulutli serverda PORT o'zgaruvchisi berilgan bo'lsa
    if os.environ.get("PORT"):
        await start_web_server()

    # Eski update'larni tozalaymiz
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Bot to'xtatildi.")
