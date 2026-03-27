import os
import asyncio
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder
from yt_dlp import YoutubeDL

# --- НАСТРОЙКИ ---
TOKEN = '8797737257:AAFB5JwyKdNZLnUUXUbZFQXQ4JOJf8bGXl8'
bot = Bot(token=TOKEN)
dp = Dispatcher()

# Укажи здесь точный путь к папке bin (БЕЗ кавычек внутри строки)
FFMPEG_PATH = r'C:\Users\hakku\OneDrive\Desktop\ffmpeg\ffmpeg-8.0.1-essentials_build\bin'

YDL_OPTIONS = {
    'format': 'bestaudio/best',
    'noplaylist': True,
    'quiet': True,
    'default_search': 'ytsearch5',
}

@dp.message(Command("start"))
async def start(message: types.Message):
    await message.answer("Привет! Введи название трека, который хочешь скачать.")

@dp.message(F.text)
async def search_music(message: types.Message):
    msg = await message.answer("Ищу варианты...")
    
    with YoutubeDL(YDL_OPTIONS) as ydl:
        try:
            info = ydl.extract_info(message.text, download=False)
            entries = info.get('entries', [])

            if not entries:
                await msg.edit_text("Ничего не найдено.")
                return

            builder = InlineKeyboardBuilder()
            for entry in entries:
                title = entry.get('title')[:40]
                callback_data = f"dl|{entry.get('id')}"
                builder.row(types.InlineKeyboardButton(text=title, callback_data=callback_data))

            await msg.edit_text("Выбери нужный трек:", reply_markup=builder.as_markup())
            
        except Exception as e:
            print(f"Ошибка поиска: {e}")
            await msg.edit_text("Произошла ошибка при поиске.")

@dp.callback_query(F.data.startswith("dl|"))
async def download_music(callback: types.CallbackQuery):
    video_id = callback.data.split("|")[1]
    url = f"https://www.youtube.com/watch?v={video_id}"
    
    await callback.answer("Начинаю загрузку... ")
    status_msg = await callback.message.answer("Загружаю и обрабатываю MP3...")
    
    file_path = f"{video_id}"
    
    download_opts = {
        'format': 'bestaudio/best',
        'outtmpl': f"{file_path}.%(ext)s",
        'ffmpeg_location': FFMPEG_PATH,
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
    }

    try:
        with YoutubeDL(download_opts) as ydl:
            ydl.download([url])
        
        final_file = f"{file_path}.mp3"
        
        if os.path.exists(final_file):
            await asyncio.sleep(1) 
            
            audio = types.FSInputFile(final_file)
            await bot.send_audio(chat_id=callback.message.chat.id, audio=audio)
            await status_msg.delete()
            
            os.remove(final_file)
        else:
            await status_msg.edit_text("Ошибка: файл не был создан.")
            
    except Exception as e:
        print(f"Ошибка загрузки: {e}")
        await status_msg.edit_text("Не удалось скачать файл. Попробуй другой вариант.")
        if os.path.exists(f"{file_path}.mp3"): os.remove(f"{file_path}.mp3")

async def main():
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
