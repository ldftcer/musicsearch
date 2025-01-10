from pyrogram import Client, filters
import yt_dlp
import os
import subprocess
import requests
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
import re
import logging

# Логирование
logging.basicConfig(level=logging.INFO)

# Переменные Railway
TOKEN = '7246695508:AAFynFXANrHO-JoQw1Sxdou_ln9M7-NWQIY'
API_ID = '23124608'
API_HASH = '0a612aa8f1c8f5eaf60eaadb73ab8e27'

# Директории
DOWNLOADS_DIR = "downloads"
SAVED_DIR = "saved"
COOKIES_FILE = "cookies.txt"

os.makedirs(DOWNLOADS_DIR, exist_ok=True)
os.makedirs(SAVED_DIR, exist_ok=True)

# Инициализация бота
app = Client("my_bot", api_id=API_ID, api_hash=API_HASH, bot_token=TOKEN)

# Пользовательские данные
user_data = {}


def clean_filename(filename):
    return re.sub(r'[\\/*?:"<>|]', '_', filename)


# Команда /start
@app.on_message(filters.command("start"))
async def start(client, message):
    await message.reply_animation(
        animation="https://media.giphy.com/media/3o6Zt481isNVuQI1l6/giphy.gif",
        caption="🎉 Добро пожаловать в наш YouTube бот! 📽️\nОтправьте ссылку, чтобы начать."
    )


# Обработка ссылок YouTube
@app.on_message(filters.text & ~filters.command("start"))
async def ask_video_or_audio(client, message):
    url = message.text.strip()
    if not re.match(r'(https?://)?(www\.)?(youtube|youtu\.be)(\.com)?/.+', url):
        await message.reply_text('🚫 Отправьте действительную ссылку на YouTube.')
        return

    user_data[message.chat.id] = {'url': url}

    try:
        ydl_opts = {
            'format': 'best',
            'noplaylist': True,
            'cookiefile': COOKIES_FILE,  # Используем cookies
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            thumbnail = info.get('thumbnail', None)
            title = info.get('title', 'Видео')

            if thumbnail:
                response = requests.get(thumbnail, stream=True)
                if response.status_code == 200:
                    thumb_path = os.path.join(DOWNLOADS_DIR, "thumbnail.jpg")
                    with open(thumb_path, 'wb') as f:
                        for chunk in response.iter_content(1024):
                            f.write(chunk)

                    await client.send_photo(
                        message.chat.id,
                        photo=thumb_path,
                        caption=f"🎬 Что хотите скачать: аудио или видео? `{title}`",
                        reply_markup=video_selection_keyboard()
                    )
                    os.remove(thumb_path)
                else:
                    await message.reply_text("⚠️ Не удалось загрузить миниатюру.")
            else:
                await message.reply_text("⚠️ Миниатюра недоступна.")

    except Exception as e:
        await message.reply_text(f'⚠️ Ошибка: {e}')


# Кнопки выбора
def video_selection_keyboard():
    keyboard = [
        [InlineKeyboardButton("🎥 Видео", callback_data='video')],
        [InlineKeyboardButton("🎵 Аудио", callback_data='audio')]
    ]
    return InlineKeyboardMarkup(keyboard)


# Кнопки качества
def quality_keyboard():
    keyboard = [
        [InlineKeyboardButton("144p", callback_data='144')],
        [InlineKeyboardButton("240p", callback_data='240')],
        [InlineKeyboardButton("360p", callback_data='360')],
        [InlineKeyboardButton("480p", callback_data='480')],
        [InlineKeyboardButton("720p", callback_data='720')],
        [InlineKeyboardButton("1080p", callback_data='1080')],
        [InlineKeyboardButton("🔙 Назад", callback_data='back')]
    ]
    return InlineKeyboardMarkup(keyboard)


# Обработка callback
@app.on_callback_query()
async def button_click(client, callback_query):
    await callback_query.answer()
    chat_id = callback_query.message.chat.id
    choice = callback_query.data

    if choice == 'video':
        user_data[chat_id]['choice'] = 'video'
        await callback_query.edit_message_text('📺 Выберите качество:', reply_markup=quality_keyboard())

    elif choice == 'audio':
        user_data[chat_id]['choice'] = 'audio'
        await download_audio(chat_id, callback_query)

    elif choice in ['144', '240', '360', '480', '720', '1080']:
        user_data[chat_id]['quality'] = choice
        await download_video(chat_id, callback_query)


# Скачивание аудио
async def download_audio(chat_id, callback_query):
    url = user_data[chat_id]['url']
    try:
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': f'{DOWNLOADS_DIR}/%(title)s.%(ext)s',
            'cookiefile': COOKIES_FILE,
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            title = clean_filename(info.get('title', 'Без названия'))
            file_path = os.path.join(DOWNLOADS_DIR, f"{title}.mp3")

            await callback_query.message.reply_audio(
                audio=open(file_path, 'rb'),
                title=title,
                caption="📥 Ваше аудио готово!"
            )
            os.remove(file_path)

    except Exception as e:
        await callback_query.message.reply_text(f'⚠️ Ошибка: {e}')


# Запуск бота
if __name__ == "__main__":
    app.run()
