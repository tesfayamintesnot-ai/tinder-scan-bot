import os
import json
import threading
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import telebot
from telebot.types import InlineKeyboardButton, InlineKeyboardMarkup
import urllib.parse
from flask import Flask

# Flask App for Render Port Binding
app = Flask(__name__)

@app.route('/')
def home():
    return "Tinder Scan Bot is Live 24/7!"

# Your Telegram Bot Token
TOKEN = '8773284530:AAGBvJh23K7oITP0xlaNyyXDo0wmLEdpR8w'
bot = telebot.TeleBot(TOKEN)

# Your Personal Telegram Username
YOUR_TELEGRAM_USERNAME = 'MinteHub'

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept-Language': 'en-US,en;q=0.9',
}

def calculate_account_age(created_dt):
    """Calculates age relative to current date."""
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
        gender = "Unknown ❓"
        birth_date = "N/A"
        user_age = "Unknown"
        photos_count = 0
        created_time_str = "N/A"
        account_age_str = "N/A"
        user_id = "Hidden"
        is_verified = False
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
                is_verified = user_data.get('is_verified', False)

                gender_code = user_data.get('gender', -1)
                if gender_code == 0:
                    gender = "Male 👦"
                elif gender_code == 1:
                    gender = "Female 👧"

                raw_photos = user_data.get('photos', [])
                photos_count = len(raw_photos)
                photos = [p.get('url') for p in raw_photos if 'url' in p]

                birth_date_raw = user_data.get('birth_date', '')
                if birth_date_raw:
                    b_dt = datetime.strptime(birth_date_raw.split('T')[0], '%Y-%m-%d')
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

        # Meta Fallback Parsing if NEXT_DATA is empty
        if user_age == "Unknown" or display_name == "Unknown":
            og_title = soup.find('meta', property='og:title')
            if og_title and og_title.get('content'):
                title_text = og_title['content']
                display_name = title_text.split(',')[0].strip()
                # Parse age from OG Title format: "Name, 24"
                if ',' in title_text:
                    possible_age = title_text.split(',')[1].strip().split(' ')[0]
                    if possible_age.isdigit():
                        user_age = f"{possible_age} years"

            og_images = soup.find_all('meta', property='og:image')
            photos = [img['content'] for img in og_images if img.get('content')]
            photos_count = len(photos)

        verification_text = "Verified" if is_verified else "Not Verified"

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

        trade_text = (
            f"Account Details:\n"
            f"👤 Gender: {gender}\n"
            f"⏱ User Age: {user_age}\n"
            f"🌐 Type: {verification_text}\n"
            f"📅 Created Time: {created_time_str}\n\n"
            f"Tell me the price 💰"
        )

        encoded_trade_text = urllib.parse.quote(trade_text)
        direct_inbox_url = f"https://t.me/{YOUR_TELEGRAM_USERNAME}?text={encoded_trade_text}"

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

def run_bot():
    bot.infinity_polling()

if __name__ == '__main__':
    # Start bot in background thread
    threading.Thread(target=run_bot, daemon=True).start()
    
    # Run Flask server for Render on bound PORT
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

        
