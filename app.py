from flask import Flask
from rubka import Robot
import telegram
import asyncio
import os
import sys
import threading
import time

# --- Setup ---
app = Flask(__name__)
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
RUBIKA_AUTH_KEY = os.environ.get("RUBIKA_AUTH_KEY")
RUBIKA_TARGET_CHAT_ID = os.environ.get("RUBIKA_TARGET_CHAT_ID")

# A simple lock to ensure the bot logic only runs once
bot_started = False

# --- Bot Initialization ---
try:
    rubika_bot = Robot(RUBIKA_AUTH_KEY)
    telegram_bot = telegram.Bot(token=TELEGRAM_BOT_TOKEN)
except Exception as e:
    print(f"Failed to initialize bots: {e}", file=sys.stderr)
    rubika_bot = None
    telegram_bot = None

# --- Main Bridge Logic (runs in background) ---
async def bridge_logic():
    global bot_started
    if bot_started:
        # If another thread already started the bot, do nothing.
        return
    bot_started = True

    print("Starting the Telegram-Rubika bridge thread...", file=sys.stderr)
    update_offset = 0
    while True:
        try:
            if not telegram_bot:
                print("Telegram bot not initialized. Waiting...", file=sys.stderr)
                time.sleep(30)
                continue

            updates = await telegram_bot.get_updates(offset=update_offset, timeout=30)
            for update in updates:
                if update.message:
                    sender_name = update.message.from_user.first_name

                    # Handle Text Messages
                    if update.message.text:
                        user_message = update.message.text
                        forwarded_message = f"Message from {sender_name} (Telegram):\n\n{user_message}"

                        rubika_bot.send_message(RUBIKA_TARGET_CHAT_ID, forwarded_message)
                        print(f"Forwarded text from {sender_name}", file=sys.stderr)

                    # Handle Photo Messages
                    elif update.message.photo:
                        caption = update.message.caption or ""
                        forwarded_caption = f"Photo from {sender_name} (Telegram):\n\n{caption}"

                        photo_file_id = update.message.photo[-1].file_id
                        file = await telegram_bot.get_file(photo_file_id)
                        temp_photo_path = f"{photo_file_id}.jpg"
                        await file.download_to_drive(custom_path=temp_photo_path)

                        rubika_bot.send_photo(RUBIKA_TARGET_CHAT_ID, photo=temp_photo_path, caption=forwarded_caption)
                        print(f"Forwarded photo from {sender_name}", file=sys.stderr)

                        os.remove(temp_photo_path)

                update_offset = update.update_id + 1
        except Exception as e:
            print(f"An error in bridge_logic: {e}", file=sys.stderr)
            # If error is due to conflict, wait longer before retrying
            if 'Conflict' in str(e):
                time.sleep(60)
            else:
                time.sleep(10)

def run_async_loop():
    asyncio.run(bridge_logic())

# --- Web Server to Keep Bot Alive ---
@app.route('/')
def index():
    return "Telegram-Rubika Bridge is active."

# --- Start the Bot ---
if rubika_bot and telegram_bot:
    bot_thread = threading.Thread(target=run_async_loop)
    bot_thread.daemon = True
    bot_thread.start()
