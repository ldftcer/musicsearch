import os
import telebot
from telebot import types
import yt_dlp
import re
from concurrent.futures import ThreadPoolExecutor

TOKEN = '7939631781:AAGBR38TykN2YyIh8dh2qQSRM11FtXGqTVY'  # Փոխարինեք ձեր բոտի նշանաբառով
OWNER_ID = 5743254515  # Փոխարինեք ձեր Telegram ID-ով
BANNED_USERS_FILE = 'banned_users.txt'

bot = telebot.TeleBot(TOKEN)

DOWNLOAD_FOLDER = 'downloads'
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)

# Ֆունկցիաներ արգելված օգտատերերի հետ աշխատանքի համար
def get_banned_users():
    if not os.path.exists(BANNED_USERS_FILE):
        return set()
    with open(BANNED_USERS_FILE, 'r') as file:
        return set(line.strip() for line in file)

def add_banned_user(user_id):
    with open(BANNED_USERS_FILE, 'a') as file:
        file.write(f"{user_id}\n")

def remove_banned_user(user_id):
    banned_users = get_banned_users()
    if user_id in banned_users:
        banned_users.remove(user_id)
        with open(BANNED_USERS_FILE, 'w') as file:
            file.writelines(f"{uid}\n" for uid in banned_users)

# Ստուգում, թե օգտատերը արգելված է
def is_user_banned(user_id):
    return str(user_id) in get_banned_users()

# /ban հրամանի մշակման ֆունկցիան
@bot.message_handler(commands=['ban'])
def ban_user(message):
    if message.from_user.id != OWNER_ID:
        bot.reply_to(message, "❌ Դուք չունեք այս հրամանը կատարելու իրավունք։")
        return

    args = message.text.split()
    if len(args) != 2:
        bot.reply_to(message, "⚠️ Օգտագործում: /ban {օգտատիրոջ ID կամ @username}")
        return

    identifier = args[1]

    if identifier.isdigit():  # Եթե ID է
        add_banned_user(identifier)
        bot.reply_to(message, f"✅ Օգտատերը ID {identifier} արգելափակված է։")
        try:
            bot.send_message(int(identifier), "❌ Դուք արգելափակված եք բոտում։")
        except Exception as e:
            print(f"Սխալ օգտատիրոջ {identifier} հաղորդագրության ուղարկման ժամանակ: {e}")
    elif identifier.startswith('@'):  # Եթե username է
        bot.reply_to(message, "⚠️ Username-ով արգելափակումը ժամանակավորապես անհասանելի է։")
    else:
        bot.reply_to(message, "❌ Սխալ ֆորմատ։ Օգտագործեք ID կամ @username։")

# /unban հրամանի մշակման ֆունկցիան
@bot.message_handler(commands=['unban'])
def unban_user(message):
    if message.from_user.id != OWNER_ID:
        bot.reply_to(message, "❌ Դուք չունեք այս հրամանը կատարելու իրավունք։")
        return

    args = message.text.split()
    if len(args) != 2:
        bot.reply_to(message, "⚠️ Օգտագործում: /unban {օգտատիրոջ ID}")
        return

    user_id = args[1]
    if not user_id.isdigit():
        bot.reply_to(message, "❌ Սխալ ID։")
        return

    remove_banned_user(user_id)
    bot.reply_to(message, f"✅ Օգտատերը ID {user_id} ապաբլոկավորված է։")
    try:
        bot.send_message(int(user_id), "✅ Դուք ապաբլոկավորված եք բոտում։")
    except Exception as e:
        print(f"Սխալ օգտատիրոջ {user_id} հաղորդագրության ուղարկման ժամանակ: {e}")

# YouTube որոնման ֆունկցիան
def search_youtube(query):
    ydl_opts = {'quiet': True, 'noplaylist': True, 'extract_flat': True}
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            result = ydl.extract_info(f"ytsearch5:{query}", download=False)
            if result and 'entries' in result:
                return result['entries']
        except Exception as e:
            print(f"Որոնման սխալ: {e}")
    return []

# MP3 ներբեռնման ֆունկցիան 
def download_audio(url):
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': f'{DOWNLOAD_FOLDER}/%(title)s.%(ext)s',
        'quiet': True,
        'cookies': 'cookies.txt',  # Указываем путь к cookies файлу
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
        print(f"Ներբեռնման սխալ: {e}")
    return None


# /start հրամանի մշակման ֆունկցիան
@bot.message_handler(commands=['start'])
def send_welcome(message):
    if is_user_banned(message.from_user.id):
        bot.reply_to(message, "❌ Դուք արգելափակված եք և չեք կարող օգտվել բոտից։")
        return
    welcome_text = (
        "👋 **Բարի գալուստ!**\n\n"
        "🎵 Ես կարող եմ գտնել երգեր YouTube-ում և ուղարկել MP3 ֆորմատով։\n"
        "🔎 Ուղարկիր ինձ երգի անունը, և ես կսկսեմ որոնումը։\n\n"
        "📌 **Օրինակ:** `Miyagi I Got Love`\n\n"
        "💡 Օգնության համար սեղմեք /help։"
    )
    bot.send_message(message.chat.id, welcome_text, parse_mode="Markdown")

# /help հրամանի մշակման ֆունկցիան
@bot.message_handler(commands=['help'])
def send_help(message):
    if is_user_banned(message.from_user.id):
        bot.reply_to(message, "❌ Դուք արգելափակված եք և չեք կարող օգտվել բոտից։")
        return
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

# Տեքստային հարցման մշակման ֆունկցիան
@bot.message_handler(func=lambda message: True)
def handle_query(message):
    if is_user_banned(message.from_user.id):
        bot.reply_to(message, "❌ Դուք արգելափակված եք և չեք կարող օգտվել բոտից։")
        return

    query = message.text
    bot.send_message(
        message.chat.id,
        f"🔍 **Որոնում:** `{query}`\n\n⏳ Խնդրում եմ սպասել մի փոքր...",
        parse_mode="Markdown"
    )
    results = search_youtube(query)
    
    if not results:
        bot.send_message(message.chat.id, "😔 Երգը չգտնվեց։ Փորձեք այլ անուն։")
        return

    markup = types.InlineKeyboardMarkup()
    for result in results:
        if 'url' in result or 'id' in result:
            title = re.sub(r'\[.*?\]', '', result.get('title', 'No Title'))
            video_url = f"https://www.youtube.com/watch?v={result['id']}" if 'id' in result else result['url']
            button_text = f"🎧 {title}"
            button = types.InlineKeyboardButton(text=button_text, callback_data=video_url)
            markup.add(button)

    bot.send_message(message.chat.id, "💡 Ընտրեք երգը ստորև 👇", reply_markup=markup)

# Կոճակի սեղմման մշակման ֆունկցիան
@bot.callback_query_handler(func=lambda call: True)
def handle_callback(call):
    if is_user_banned(call.from_user.id):
        bot.answer_callback_query(call.id, "❌ Դուք արգելափակված եք։")
        return

    bot.answer_callback_query(call.id, "⏳ Ներբեռնում եմ... խնդրում եմ սպասել...")
    
    def download_and_send():
        audio_file = download_audio(call.data)
        if audio_file:
            bot.send_message(call.message.chat.id, "✅ **Երգը պատրաստ է! Ուղարկում եմ...**", parse_mode="Markdown")
            try:
                with open(audio_file, 'rb') as audio:
                    caption = "🎵 Ներբեռնվել է @melodyi_bot "
                    bot.send_audio(call.message.chat.id, audio, title=os.path.basename(audio_file), caption=caption)
            except Exception as e:
                bot.send_message(call.message.chat.id, "❌ Չհաջողվեց ուղարկել երգը։")
                print(f"Սխալ ֆայլի ուղարկման ժամանակ: {e}")
            finally:
                os.remove(audio_file)
        else:
            bot.send_message(call.message.chat.id, "❌ Չհաջողվեց ներբեռնել երգը։")

    with ThreadPoolExecutor(max_workers=5) as executor:
        executor.submit(download_and_send)

print("\n" + "="*40)
print("🎶 Բոտը հաջողությամբ գործարկված է! Սպասում եմ հաղորդագրություններին...")
print("="*40 + "\n")

bot.polling(none_stop=True)
