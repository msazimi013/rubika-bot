import telegram
from rubka import Robot
import asyncio

# --- CONFIGURATION ---
# 1. Get this from @BotFather on TELEGRAM
TELEGRAM_BOT_TOKEN = "YOUR_TELEGRAM_BOT_TOKEN"

# 2. Get this from @BotFather on RUBIKA (as you have proven works)
RUBIKA_BOT_AUTH = "YOUR_RUBIKA_BOT_TOKEN"

# 3. The destination chat_id in Rubika where messages should be sent
# This can be your own user GUID or a group/channel ID
RUBIKA_TARGET_CHAT_ID = "YOUR_RUBIKA_DESTINATION_CHAT_ID"

# --- INITIALIZATION ---
rubika_bot = Robot(RUBIKA_BOT_AUTH)

async def main():
    """
    Fetches updates from Telegram and forwards them to Rubika.
    """
    print("Bridge bot starting...")
    # Get the Telegram bot info to ensure the token is correct
    telegram_bot = telegram.Bot(token=TELEGRAM_BOT_TOKEN)
    bot_info = await telegram_bot.get_me()
    print(f"Logged in to Telegram as: {bot_info.first_name} (@{bot_info.username})")
    
    # The offset tells Telegram which messages we have already processed
    update_offset = 0

    while True:
        try:
            # Get new messages from Telegram
            updates = await telegram_bot.get_updates(offset=update_offset, timeout=10)

            for update in updates:
                if update.message and update.message.text:
                    user_message = update.message.text
                    print(f"Received from Telegram: {user_message}")
                    
                    # Forward the message to Rubika
                    rubika_bot.send_message(RUBIKA_TARGET_CHAT_ID, user_message)
                    print("Forwarded to Rubika.")
                
                # Update the offset to avoid re-reading the same message
                update_offset = update.update_id + 1

        except Exception as e:
            print(f"An error occurred: {e}")

# --- START THE BOT ---
if __name__ == "__main__":
    # To run this script, you need to install the telegram library:
    # pip install python-telegram-bot
    asyncio.run(main())
