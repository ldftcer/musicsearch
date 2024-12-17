import os
import telebot
from telebot import types
import yt_dlp
import re
from concurrent.futures import ThreadPoolExecutor

# Токен бота
TOKEN = '8022014605:AAF-XMHK40SfJuDYxaq-EnnJhMPIvhiw-Ag'
bot = telebot.TeleBot(TOKEN)

# Папка для хранения файлов
DOWNLOAD_FOLDER = 'downloads'
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)

# Поиск песен на YouTube
def search_youtube(query):
    ydl_opts = {'quiet': True, 'noplaylist': True, 'extract_flat': True}
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            result = ydl.extract_info(f"ytsearch5:{query}", download=False)
            if result and 'entries' in result:
                return result['entries']
        except Exception as e:
            print(f"Ошибка при поиске: {e}")
    return []

# Скачивание аудио из YouTube
def download_audio(url):
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': f'{DOWNLOAD_FOLDER}/%(title)s.%(ext)s',
        'quiet': True,
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info_dict).replace('.webm', '.mp3').replace('.m4a', '.mp3')
            return filename
    except Exception as e:
        print(f"Ошибка при скачивании: {e}")
    return None

# Команда /start
@bot.message_handler(commands=['start'])
def send_welcome(message):
    welcome_text = (
        "👋 **Բարի գալուստ!**\n\n"
        "🎵 Ես կարող եմ գտնել երգեր YouTube-ում և ուղարկել քեզ MP3 ֆորմատով!\n"
        "🔎 Ուղարկիր ինձ երգի անունը, և ես կսկսեմ որոնումը։\n\n"
        "📌 **Օրինակ:** `Miyagi I Got Love`\n\n"
        "💡 Սեղմիր /help, եթե ունես հարցեր։"
    )
    bot.send_message(message.chat.id, welcome_text, parse_mode="Markdown")

# Обработка текстовых сообщений
@bot.message_handler(func=lambda message: True)
def handle_query(message):
    query = message.text
    bot.send_message(
        message.chat.id,
        f"🔍 **Որոնում:** `{query}`\n\n⏳ Խնդրում եմ սպասել մի փոքր...",
        parse_mode="Markdown"
    )
    results = search_youtube(query)
    
    if not results:
        bot.send_message(message.chat.id, "😔 Երգը չգտնվեց։ Փորձիր այլ անվանում։")
        return

    # Создаём кнопки с результатами
    markup = types.InlineKeyboardMarkup()
    for result in results:
        if 'url' in result or 'id' in result:  # Проверка на наличие ссылки или ID
            title = re.sub(r'\[.*?\]', '', result.get('title', 'No Title'))  # Удаляем лишние символы из названия
            video_url = f"https://www.youtube.com/watch?v={result['id']}" if 'id' in result else result['url']
            # Добавляем эмодзи к заголовкам
            button_text = f"🎧 {title}"
            button = types.InlineKeyboardButton(text=button_text, callback_data=video_url)
            markup.add(button)

    bot.send_message(message.chat.id, "💡 Ընտրեք երգը ստորև👇", reply_markup=markup)

# Обработка нажатий на кнопки
@bot.callback_query_handler(func=lambda call: True)
def handle_callback(call):
    bot.answer_callback_query(call.id, "⏳ Ներբեռնում եմ... խնդրում եմ սպասիր...")

    def download_and_send():
        audio_file = download_audio(call.data)
        if audio_file:
            bot.send_message(call.message.chat.id, "✅ **Երգը պատրաստ է! Ուղարկում եմ...**", parse_mode="Markdown")
            try:
                with open(audio_file, 'rb') as audio:
                    caption = "🎵 Ներբեռնվել է @ergeripntrtuknerov_bot\n🔗 @ishkachka | @ldftcer"
                    bot.send_audio(
                        call.message.chat.id, 
                        audio, 
                        title=os.path.basename(audio_file), 
                        caption=caption
                    )
            except Exception as e:
                bot.send_message(call.message.chat.id, "❌ Չհաջողվեց ուղարկել երգը։")
                print(f"Ошибка при отправке файла: {e}")
            finally:
                os.remove(audio_file)  # Удаляем файл после отправки
        else:
            bot.send_message(call.message.chat.id, "❌ Չհաջողվեց ներբեռնել երգը։")

    with ThreadPoolExecutor(max_workers=5) as executor:  # Количество потоков для загрузки/отправки
        executor.submit(download_and_send)

# Запуск бота
print("\n" + "="*40)
print("🎶 Բոտ հաջողությամբ գործարկված է! Հիմա սպասում եմ հաղորդագրություններին...")
print("🔗 Разработано: @ergeripntrtuknerov_bot | @ishkachka | @ldftcer")
print("="*40 + "\n")

bot.polling(none_stop=True)
