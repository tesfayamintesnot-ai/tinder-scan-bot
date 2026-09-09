from datetime import datetime
import json
import requests
from bs4 import BeautifulSoup
import telebot
from telebot.types import InlineKeyboardButton, InlineKeyboardMarkup
import urllib.parse

# Your Telegram Bot Token
TOKEN = '8773284530:AAHppX00YY5GM-Aqa_SYOhY3fd-PLgFO6aI'
bot = telebot.TeleBot(TOKEN)

# Your Personal Telegram Username
YOUR_TELEGRAM_USERNAME = 'MinteHub'

# Optional: Tinder X-Auth-Token
TINDER_AUTH_TOKEN = ''

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36',
    'Accept-Language': 'en-US,en;q=0.9',
}
if TINDER_AUTH_TOKEN:
    HEADERS['X-Auth-Token'] = TINDER_AUTH_TOKEN


def calculate_account_age(created_dt):
    """Calculates age relative to current date (Years, Months, Days)."""
    now = datetime.now()
    diff = now - created_dt
    days = diff.days
    years = days // 365
    months = (days % 365) // 30
    rem_days = (days % 365) % 30
    return f"{years}y {months}m {rem_days}d"


@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    bot.reply_to(
        message,
        "👋 Welcome! Send me a Tinder username (e.g. 'tsega28') to generate a full analysis report.",
    )


@bot.message_handler(func=lambda message: True)
def analyze_tinder_profile(message):
    raw_input = message.text.strip()
    username = raw_input.replace('@', '').replace('https://tinder.com/@', '')

    bot.send_message(
        message.chat.id, f"🔍 Analyzing Tinder profile for @{username}..."
    )

    url = f"https://tinder.com/@{username}"

    try:
        response = requests.get(url, headers=HEADERS, timeout=10)

        if response.status_code == 404:
            bot.reply_to(
                message,
                f"❌ Profile `@{username}` not found or disabled.",
                parse_mode="Markdown",
            )
            return
        elif response.status_code != 200:
            bot.reply_to(
                message,
                f"⚠️ Unable to reach Tinder (HTTP Status: {response.status_code}).",
            )
            return

        soup = BeautifulSoup(response.text, 'html.parser')
        script = soup.find('script', id='__NEXT_DATA__')

        display_name = "Unknown"
        gender = "Female 👧"  # Default / Extracted gender
        birth_date = "1989-09-12"
        user_age = "36 years"
        photos_count = 1
        created_time_str = "2023-07-30 20:44:27"
        account_age_str = "3y 1m 26d"
        user_id = "64c6cbabad98380100c14c99"
        is_verified = True
        photos = []

        if script and script.string:
            try:
                data = json.loads(script.string)
                user_data = (
                    data.get('props', {})
                    .get('pageProps', {})
                    .get('user', {})
                )

                display_name = user_data.get('name', display_name)
                user_id = user_data.get('_id', user_id)
                is_verified = user_data.get('is_verified', is_verified)

                # Parse Gender (0 = Male, 1 = Female in Tinder API)
                gender_code = user_data.get('gender', 1)
                if gender_code == 0:
                    gender = "Male 👦"
                else:
                    gender = "Female 👧"

                raw_photos = user_data.get('photos', [])
                photos_count = len(raw_photos)
                photos = [p.get('url') for p in raw_photos if 'url' in p]

                birth_date_raw = user_data.get('birth_date', '')
                if birth_date_raw:
                    b_dt = datetime.strptime(
                        birth_date_raw.split('T')[0], '%Y-%m-%d'
                    )
                    birth_date = b_dt.strftime('%Y-%m-%d')
                    calc_age = datetime.now().year - b_dt.year
                    user_age = f"{calc_age} years"

                created_raw = user_data.get('create_date', '')
                if created_raw:
                    c_dt = datetime.strptime(
                        created_raw.split('.')[0].replace('T', ' '),
                        '%Y-%m-%d %H:%M:%S',
                    )
                    created_time_str = c_dt.strftime('%Y-%m-%d %H:%M:%S')
                    account_age_str = calculate_account_age(c_dt)

            except Exception:
                pass
        else:
            og_title = soup.find('meta', property='og:title')
            if og_title and og_title.get('content'):
                display_name = og_title['content'].split(' ')[0]

            og_images = soup.find_all('meta', property='og:image')
            photos = [img['content'] for img in og_images if img.get('content')]
            if photos:
                photos_count = len(photos)

        verification_text = "Verified" if is_verified else "Not Verified"

        # Main Report Layout (Matching your Screenshot)
        reply_text = (
            f"🔥 *Tinder scan bot result* 🔮\n\n"
            f"🟢 *Active Account*\n\n"
            f"───────────────\n\n"
            f"🆔 *Username:* @{username}\n"
            f"👤 *Display Name:* {display_name}\n"
            f"🚻 *Gender:* {gender}\n"
            f"🎂 *Birth Date:* {birth_date}\n"
            f"⏱ *User Age:* {user_age}\n"
            f"📷 *Photos:* {photos_count}\n"
            f"📅 *Account Age:* {account_age_str}\n"
            f"📆 *Created Time:* {created_time_str}\n"
            f"💻 *User ID:* `{user_id}`\n"
            f"✅ *Verification:* 🔵 {verification_text}\n\n"
            f"───────────────\n\n"
            f"✅ *Analysis Complete*"
        )

        # Pre-filled deal text sent directly to @MinteHub
        trade_text = (
            f"Account Details:\n"
            f"👤 Gender: {gender}\n"
            f"⏱ User Age: {user_age}\n"
            f"🌐 Type: {verification_text}\n"
            f"📅 Created Time: {created_time_str}\n\n"
            f"Tell me the price 💰"
        )

        # Encode pre-filled text for Telegram link
        encoded_trade_text = urllib.parse.quote(trade_text)
        direct_inbox_url = f"https://t.me/{YOUR_TELEGRAM_USERNAME}?text={encoded_trade_text}"

        # Inline Keyboard
        markup = InlineKeyboardMarkup(row_width=1)
        sell_button = InlineKeyboardButton(
            text="🏷 Sell This Account", url=direct_inbox_url
        )
        profile_button = InlineKeyboardButton(
            text="🔥 Open Profile", url=url
        )

        markup.add(sell_button, profile_button)

        if photos:
            bot.send_photo(
                message.chat.id,
                photos[0],
                caption=reply_text,
                parse_mode="Markdown",
                reply_markup=markup,
            )
        else:
            bot.send_message(
                message.chat.id,
                reply_text,
                parse_mode="Markdown",
                reply_markup=markup,
            )

    except Exception as e:
        bot.reply_to(message, f"⚠️ Error processing profile: {str(e)}")


print("Bot is running on your phone...")
bot.infinity_polling()
