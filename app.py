from flask import Flask
from rubka import Robot
import telegram
import asyncio
import os
import sys
import threading
import time
import random

# --- Setup ---
app = Flask(__name__)
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
RUBIKA_AUTH_KEY = os.environ.get("RUBIKA_AUTH_KEY")

# --- Data Storage (In-Memory) ---
# NOTE: This data will be lost on server restart. A database is needed for a permanent solution.
pending_registrations = {} # Stores { "unique_code": "rubika_chat_id" }
user_mappings = {} # Stores { "telegram_chat_id": "rubika_chat_id" }

# --- Bot Initialization ---
rubika_bot = Robot(RUBIKA_AUTH_KEY)
telegram_bot = telegram.Bot(token=TELEGRAM_BOT_TOKEN)

# --- Main Bridge Logic (runs in background) ---
async def bridge_logic():
    print("Starting the auto-register bridge thread...", file=sys.stderr)
    update_offset = 0
    while True:
        try:
            # Check for new messages on Telegram
            updates = await telegram_bot.get_updates(offset=update_offset, timeout=30)
            for update in updates:
                if update.message and update.message.text:
                    telegram_chat_id = str(update.message.from_user.id)
                    user_message = update.message.text

                    # Check if the message is a registration code
                    if user_message in pending_registrations:
                        rubika_chat_id = pending_registrations[user_message]
                        user_mappings[telegram_chat_id] = rubika_chat_id
                        
                        # Clean up the pending code
                        del pending_registrations[user_message]
                        
                        # Send confirmation messages
                        await telegram_bot.send_message(chat_id=telegram_chat_id, text="✅ Accounts successfully linked!")
                        rubika_bot.send_message(rubika_chat_id, "✅ Accounts successfully linked!")
                        print(f"New link created: Telegram ID {telegram_chat_id} -> Rubika ID {rubika_chat_id}", file=sys.stderr)

                    # If it's a regular message, check if the user is registered
                    elif telegram_chat_id in user_mappings:
                        target_rubika_id = user_mappings[telegram_chat_id]
                        sender_name = update.message.from_user.first_name
                        forwarded_message = f"Message from {sender_name} (Telegram):\n\n{user_message}"
                        
                        rubika_bot.send_message(target_rubika_id, forwarded_message)
                        print(f"Forwarded message from {telegram_chat_id} to {target_rubika_id}", file=sys.stderr)

                update_offset = update.update_id + 1
        except Exception as e:
            print(f"An error in bridge_logic: {e}", file=sys.stderr)
            time.sleep(10)

def run_async_loop():
    asyncio.run(bridge_logic())

# This separate thread handles messages coming FROM Rubika
def rubika_listener():
    for msg in rubika_bot.on_message():
        try:
            if msg.text == "/register":
                # Generate a unique 6-digit code
                reg_code = str(random.randint(100000, 999999))
                pending_registrations[reg_code] = msg.chat_id
                
                reply_text = (
                    "To link your accounts, please send this code to your Telegram bot:\n\n"
                    f"`{reg_code}`\n\n"
                    "(This code is valid for 5 minutes)"
                )
                msg.reply(reply_text)
                print(f"Generated registration code {reg_code} for Rubika ID {msg.chat_id}", file=sys.stderr)
        except Exception as e:
            print(f"Error in rubika_listener: {e}", file=sys.stderr)

# --- Web Server to Keep Bot Alive ---
@app.route('/')
def index():
    return "Auto-Register Telegram-Rubika Bridge is active."

# --- Start the Bot Threads ---
telegram_thread = threading.Thread(target=run_async_loop)
telegram_thread.daemon = True
telegram_thread.start()

rubika_thread = threading.Thread(target=rubika_listener)
rubika_thread.daemon = True
rubika_thread.start()
