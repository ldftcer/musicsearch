import os
import telebot
from telebot import types
import yt_dlp
import re
from concurrent.futures import ThreadPoolExecutor

TOKEN = '7939631781:AAGBR38TykN2YyIh8dh2qQSRM11FtXGqTVY'  # Замените на ваш токен
bot = telebot.TeleBot(TOKEN)

DOWNLOAD_FOLDER = 'downloads'
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)

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

@bot.message_handler(commands=['help'])
def send_help(message):
    help_text = (
        "📖 **Ինչպես օգտվել բոտից:**\n\n"
        "1. Ուղարկեք ինձ երգի կամ արտիստի անունը։\n"
        "2. Ես ցույց կտամ YouTube-ի 5 լավագույն արդյունքները։\n"
        "3. Ընտրեք երգը ցանկից։\n"
        "4. Երգը կվերափոխվի MP3 ձևաչափի և կուղարկվի ձեզ։\n\n"
        "❗ **Նշում:**\n"
        "- Ամբողջ պրոցեսը կարող է տևել մի քանի րոպե, կախված ինտերնետի արագությունից։\n"
        "- Եթե ինչ-որ բան չի աշխատում, փորձեք կրկին։\n\n"
        "📩 **Հարցերի դեպքում դիմեք:** @ldftcer"
    )
    bot.send_message(message.chat.id, help_text, parse_mode="Markdown")

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

    markup = types.InlineKeyboardMarkup()
    for result in results:
        if 'url' in result or 'id' in result:  
            title = re.sub(r'\[.*?\]', '', result.get('title', 'No Title'))  
            video_url = f"https://www.youtube.com/watch?v={result['id']}" if 'id' in result else result['url']
            button_text = f"🎧 {title}"
            button = types.InlineKeyboardButton(text=button_text, callback_data=video_url)
            markup.add(button)

    bot.send_message(message.chat.id, "💡 Ընտրեք երգը ստորև👇", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: True)
def handle_callback(call):
    bot.answer_callback_query(call.id, "⏳ Ներբեռնում եմ... խնդրում եմ սպասիր...")

    def download_and_send():
        audio_file = download_audio(call.data)
        if audio_file:
            bot.send_message(call.message.chat.id, "✅ **Երգը պատրաստ է! Ուղարկում եմ...**", parse_mode="Markdown")
            try:
                with open(audio_file, 'rb') as audio:
                    caption = "🎵 Ներբեռնվել է  @melodyi_bot \n🔗 @ishkachka | @ldftcer"
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
                os.remove(audio_file)  
        else:
            bot.send_message(call.message.chat.id, "❌ Չհաջողվեց ներբեռնել երգը։")

    with ThreadPoolExecutor(max_workers=5) as executor: 
        executor.submit(download_and_send)

print("\n" + "="*40)
print("🎶 Բոտ հաջողությամբ գործարկված է! Հիմա սպասում եմ հաղորդագրություններին...")
print("🔗 Разработано: @ergeripntrtuknerov_bot | @ishkachka | @ldftcer")
print("="*40 + "\n")

bot.polling(none_stop=True)
