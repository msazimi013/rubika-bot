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
RUBIKA_BOT_TOKEN = os.environ.get("RUBIKA_BOT_TOKEN") # Using the correct name
RUBIKA_TARGET_CHAT_ID = os.environ.get("RUBIKA_TARGET_CHAT_ID")

rubika_bot = Robot(RUBIKA_BOT_TOKEN)
telegram_bot = telegram.Bot(token=TELEGRAM_BOT_TOKEN)

# --- Main Bridge Logic (runs in background) ---
async def bridge_logic():
    print("Starting the Telegram-Rubika bridge thread...", file=sys.stderr)
    update_offset = 0
    while True:
        try:
            updates = await telegram_bot.get_updates(offset=update_offset, timeout=30)
            for update in updates:
                if update.message and update.message.text:
                    user_message = update.message.text
                    sender_name = update.message.from_user.first_name
                    forwarded_message = f"Message from {sender_name} (Telegram):\n\n{user_message}"
                    
                    rubika_bot.send_message(RUBIKA_TARGET_CHAT_ID, forwarded_message)
                    print(f"Forwarded message from {sender_name}", file=sys.stderr)
                
                update_offset = update.update_id + 1
        except Exception as e:
            print(f"An error in bridge_logic: {e}", file=sys.stderr)
            time.sleep(10)

def run_async_loop():
    asyncio.run(bridge_logic())

# --- Web Server to Keep Bot Alive ---
@app.route('/')
def index():
    return "Telegram-Rubika Bridge is active."

# --- Start the Bot ---
bot_thread = threading.Thread(target=run_async_loop)
bot_thread.daemon = True
bot_thread.start()
