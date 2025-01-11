
import os
import telebot
from telebot import types
import yt_dlp
import re
from concurrent.futures import ThreadPoolExecutor

TOKEN ='7939631781:AAGBR38TykN2YyIh8dh2qQSRM11FtXGqTVY'  # Замените на ваш токен
OWNER_ID = 123456789  # Замените на ваш Telegram ID
BANNED_USERS_FILE = 'banned_users.txt'

bot = telebot.TeleBot(TOKEN)

DOWNLOAD_FOLDER = 'downloads'
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)

# Функции для работы с файлом заблокированных пользователей
def get_banned_users():
    if not os.path.exists(BANNED_USERS_FILE):
        return set()
    with open(BANNED_USERS_FILE, 'r') as file:
        return set(line.strip() for line in file)

def add_banned_user(user_id):
    with open(BANNED_USERS_FILE, 'a') as file:
        file.write(f"{user_id}\n")

# Проверка на блокировку
def is_user_banned(user_id):
    return str(user_id) in get_banned_users()

# Функция для поиска YouTube
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

# Функция для загрузки аудио
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

# Обработчик команды /start
@bot.message_handler(commands=['start'])
def send_welcome(message):
    if is_user_banned(message.from_user.id):
        bot.reply_to(message, "❌ Вы заблокированы в этом боте.")
        return
    welcome_text = (
        "👋 **Բարի գալուստ!**\n\n"
        "🎵 Ես կարող եմ գտնել երգեր YouTube-ում և ուղարկել քեզ MP3 ֆորմատով!\n"
        "🔎 Ուղարկիր ինձ երգի անունը, և ես կսկսեմ որոնումը։\n\n"
        "📌 **Օրինակ:** `Miyagi I Got Love`\n\n"
        "💡 Սեղմիր /help, եթե ունես հարցեր։"
    )
    bot.send_message(message.chat.id, welcome_text, parse_mode="Markdown")

# Обработчик команды /help
@bot.message_handler(commands=['help'])
def send_help(message):
    if is_user_banned(message.from_user.id):
        bot.reply_to(message, "❌ Вы заблокированы в этом боте.")
        return
    help_text = (
        "📖 **Как пользоваться ботом:**\n\n"
        "1. Отправьте мне название песни или имя артиста.\n"
        "2. Я покажу 5 лучших результатов с YouTube.\n"
        "3. Выберите песню из списка.\n"
        "4. Песня будет преобразована в MP3 и отправлена вам.\n\n"
        "❗ **Примечание:**\n"
        "- Весь процесс может занять несколько минут в зависимости от скорости интернета.\n"
        "- Если что-то не работает, попробуйте снова.\n\n"
        "📩 **Вопросы:** @ldftcer"
    )
    bot.send_message(message.chat.id, help_text, parse_mode="Markdown")

# Обработчик команды /ban
@bot.message_handler(commands=['ban'])
def ban_user(message):
    if message.from_user.id != 5743254515:
        bot.reply_to(message, "❌ У вас нет прав для выполнения этой команды.")
        return

    args = message.text.split()
    if len(args) != 2:
        bot.reply_to(message, "⚠️ Использование: /ban {user_id}")
        return

    user_id = args[1]
    if not user_id.isdigit():
        bot.reply_to(message, "❌ Неверный ID пользователя.")
        return

    add_banned_user(user_id)
    bot.reply_to(message, f"✅ Пользователь с ID {user_id} заблокирован.")
    try:
        bot.send_message(int(user_id), "❌ Вы были заблокированы в боте.")
    except Exception as e:
        print(f"Ошибка при отправке сообщения пользователю {user_id}: {e}")

# Обработчик запросов
@bot.message_handler(func=lambda message: True)
def handle_query(message):
    if is_user_banned(message.from_user.id):
        bot.reply_to(message, "❌ Вы заблокированы в этом боте.")
        return

    query = message.text
    bot.send_message(
        message.chat.id,
        f"🔍 **Поиск:** `{query}`\n\n⏳ Пожалуйста, подождите немного...",
        parse_mode="Markdown"
    )
    results = search_youtube(query)

    if not results:
        bot.send_message(message.chat.id, "😔 Песня не найдена. Попробуйте другое название.")
        return

    markup = types.InlineKeyboardMarkup()
    for result in results:
        if 'url' in result or 'id' in result:
            title = re.sub(r'\[.*?\]', '', result.get('title', 'No Title'))
            video_url = f"https://www.youtube.com/watch?v={result['id']}" if 'id' in result else result['url']
            button_text = f"🎧 {title}"
            button = types.InlineKeyboardButton(text=button_text, callback_data=video_url)
            markup.add(button)

    bot.send_message(message.chat.id, "💡 Выберите песню ниже👇", reply_markup=markup)

# Обработчик нажатий на кнопки
@bot.callback_query_handler(func=lambda call: True)
def handle_callback(call):
    bot.answer_callback_query(call.id, "⏳ Загружаю... Пожалуйста, подождите...")

    def download_and_send():
        audio_file = download_audio(call.data)
        if audio_file:
            bot.send_message(call.message.chat.id, "✅ **Песня готова! Отправляю...**", parse_mode="Markdown")
            try:
                with open(audio_file, 'rb') as audio:
                    caption = "🎵 Загружено @melodyi_bot \n🔗 @ishkachka | @ldftcer"
                    bot.send_audio(
                        call.message.chat.id,
                        audio,
                        title=os.path.basename(audio_file),
                        caption=caption
                    )
            except Exception as e:
                bot.send_message(call.message.chat.id, "❌ Не удалось отправить песню.")
                print(f"Ошибка при отправке файла: {e}")
            finally:
                os.remove(audio_file)
        else:
            bot.send_message(call.message.chat.id, "❌ Не удалось загрузить песню.")

    with ThreadPoolExecutor(max_workers=5) as executor:
        executor.submit(download_and_send)

print("\n" + "=" * 40)
print("🎶 Бот успешно запущен!")
print("=" * 40 + "\n")

bot.polling(none_stop=True)
