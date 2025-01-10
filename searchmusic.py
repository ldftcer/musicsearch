from pyrogram import Client, filters
import yt_dlp
import os
import subprocess
import requests
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
import re
import logging
import shutil

# Logging configuration
logging.basicConfig(level=logging.INFO)

# Bot credentials
TOKEN = '7246695508:AAFynFXANrHO-JoQw1Sxdou_ln9M7-NWQIY'
API_ID = '23124608'
API_HASH = '0a612aa8f1c8f5eaf60eaadb73ab8e27'

# Initialize bot
app = Client("my_bot", api_id=API_ID, api_hash=API_HASH, bot_token=TOKEN)

# Store user data during sessions
user_data = {}

# Directory paths
DOWNLOADS_DIR = "downloads"
SAVED_DIR = "saved"

os.makedirs(DOWNLOADS_DIR, exist_ok=True)
os.makedirs(SAVED_DIR, exist_ok=True)


# Utility: Sanitize filenames
def clean_filename(filename):
    return re.sub(r'[\\/*?:"<>|]', '_', filename)


# Start command handler
@app.on_message(filters.command("start"))
async def start(client, message):
    await message.reply_animation(
        animation="https://media.giphy.com/media/3o6Zt481isNVuQI1l6/giphy.gif",
        caption="🎉 Բարի գալուստ մեր մեգա-կрутому боту! 📽️\nՈւղղարկեք Յութուբի լինկը, чтобы начать."
    )


# Handle YouTube links
@app.on_message(filters.text & ~filters.command("start"))
async def ask_video_or_audio(client, message):
    url = message.text.strip()
    if not re.match(r'(https?://)?(www\.)?(youtube|youtu\.be)(\.com)?/.+', url):
        await message.reply_text('🚫 Տվեք YouTube-ի հղումը:')
        return

    user_data[message.chat.id] = {'url': url}

    try:
        ydl_opts = {'format': 'best', 'noplaylist': True}
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            thumbnail = info.get('thumbnail', None)
            title = info.get('title', 'Վիդեո')

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
                        caption=f"🎬 Ինչ եք ցանկանում  ներբեռնել՝ աուդիո կամ վիդեո: `{title}`",
                        reply_markup=video_selection_keyboard()
                    )
                    os.remove(thumb_path)
                else:
                    await message.reply_text("⚠️ Հնարավոր չէ ստանալ տեսանյութի նկար.")
            else:
                await message.reply_text("⚠️ Հնարավոր չէ ստանալ տեսանյութի նկար.")

    except Exception as e:
        await message.reply_text(f'⚠️ Նկարահանման ժամանակ առաջացավ սխալ: {e}')


# Inline keyboard for video or audio selection
def video_selection_keyboard():
    keyboard = [
        [InlineKeyboardButton("🎥 Վիդեո", callback_data='video')],
        [InlineKeyboardButton("🎵 Աուդիո", callback_data='audio')]
    ]
    return InlineKeyboardMarkup(keyboard)


# Inline keyboard for video quality selection
def quality_keyboard():
    keyboard = [
        [InlineKeyboardButton("144p", callback_data='144')],
        [InlineKeyboardButton("240p", callback_data='240')],
        [InlineKeyboardButton("360p", callback_data='360')],
        [InlineKeyboardButton("480p", callback_data='480')],
        [InlineKeyboardButton("720p", callback_data='720')],
        [InlineKeyboardButton("1080p", callback_data='1080')],
        [InlineKeyboardButton("🔙 Վերադառնալ", callback_data='back')]
    ]
    return InlineKeyboardMarkup(keyboard)


# Handle callback queries
@app.on_callback_query()
async def button_click(client, callback_query):
    await callback_query.answer()
    chat_id = callback_query.message.chat.id
    choice = callback_query.data

    if choice == 'video':
        user_data[chat_id]['choice'] = 'video'
        await callback_query.edit_message_text('📺  Ընտրեք որակը:', reply_markup=quality_keyboard())

    elif choice in ['144', '240', '360', '480', '720', '1080']:
        user_data[chat_id]['quality'] = choice
        await download_video(chat_id, callback_query)

    elif choice == 'audio':
        user_data[chat_id]['choice'] = 'audio'
        await download_audio(chat_id, callback_query)

    elif choice == 'back':
        await callback_query.edit_message_text('🎬 Ընտրեք ձևաչափ՝ աուդիո կամ վիդեո:', reply_markup=video_selection_keyboard())


# Download audio
async def download_audio(chat_id, callback_query):
    url = user_data[chat_id]['url']
    try:
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': f'{DOWNLOADS_DIR}/%(title)s.%(ext)s',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            'noplaylist': True,
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            title = clean_filename(info.get('title', 'Без названия'))
            file_path = os.path.join(DOWNLOADS_DIR, f"{title}.mp3")
            saved_path = os.path.join(SAVED_DIR, f"{title}.mp3")
            shutil.move(file_path, saved_path)

            await callback_query.message.reply_audio(
                audio=open(saved_path, 'rb'),
                title=title,
                performer='@Ldftcer',
                caption="📥 @armYouTube_bot | Բոտ от @Ldftcer"
            )

    except Exception as e:
        await callback_query.message.reply_text(f'⚠️ Սխալ՝ {e}')


# Download video
async def download_video(chat_id, callback_query):
    url = user_data[chat_id]['url']
    quality = user_data[chat_id]['quality']

    try:
        ydl_opts = {
            'format': f'bestvideo[height<={quality}]+bestaudio/best',
            'outtmpl': f'{DOWNLOADS_DIR}/%(title)s.%(ext)s',
            'noplaylist': True,
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            title = clean_filename(info.get('title', 'Без названия'))
            file_path = os.path.join(DOWNLOADS_DIR, f"{title}.mp4")
            saved_path = os.path.join(SAVED_DIR, f"{title}.mp4")

            # Compress the video for Telegram
            compressed_file = os.path.join(DOWNLOADS_DIR, f"{title}_compressed.mp4")
            command = [
                'ffmpeg', '-i', file_path, '-vf', 'scale=1280:720', '-c:v', 'libx264',
                '-preset', 'slow', '-crf', '28', '-c:a', 'aac', compressed_file
            ]
            subprocess.run(command, check=True)

            shutil.move(compressed_file, saved_path)

            await callback_query.message.reply_video(
                video=open(saved_path, 'rb'),
                caption=f"📥 {title}\nBy @Ldftcer"
            )

    except Exception as e:
        await callback_query.message.reply_text(f'⚠️ Սխալ: {e}')


# Run the bot
if __name__ == "__main__":
    app.run()
