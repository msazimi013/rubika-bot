import os
import asyncio
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes
# ### <<<< مرحله ۱: وارد کردن کلاس اصلی Client >>>> ###
from rubpy.client import Client
import threading
from flask import Flask

# --- بخش تنظیمات ---
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
RUBIKA_AUTH_KEY = os.getenv('RUBIKA_AUTH_KEY')
SOURCE_TELEGRAM_CHANNEL_ID = int(os.getenv('SOURCE_TELEGRAM_CHANNEL_ID', '0'))
DESTINATION_RUBIKA_GUID = os.getenv('DESTINATION_RUBIKA_GUID')
# --------------------

# ایجاد یک پوشه موقت برای دانلود فایل‌ها
if not os.path.exists('temp_downloads'):
    os.makedirs('temp_downloads')

# ### <<<< مرحله ۲: ساخت یک نمونه (instance) از کلاس Client >>>> ###
rubika_client = Client(RUBIKA_AUTH_KEY)

# راه‌اندازی وب‌سرور Flask
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is running..."

def run_flask():
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)

# ### <<<< مرحله ۳: فراخوانی متدها روی آبجکت ساخته شده >>>> ###
async def forward_to_rubika(file_path=None, caption=None):
    try:
        if file_path:
            # بر اساس مستندات، نام متدها به این شکل است
            if file_path.lower().endswith(('.jpg', '.jpeg', '.png')):
                print(f"Sending photo: {file_path} with caption: {caption}")
                await rubika_client.send_photo(DESTINATION_RUBIKA_GUID, file_path, caption) #
            elif file_path.lower().endswith(('.mp4', '.avi', '.mov')):
                print(f"Sending video: {file_path} with caption: {caption}")
                await rubika_client.send_video(DESTINATION_RUBIKA_GUID, file_path, caption) #
            else:
                 print(f"Sending document: {file_path} with caption: {caption}")
                 await rubika_client.send_document(DESTINATION_RUBIKA_GUID, file_path, caption) #
        elif caption:
            print(f"Sending text: {caption}")
            await rubika_client.send_message(DESTINATION_RUBIKA_GUID, text=caption) #
        print("Message forwarded to Rubika successfully.")
        return True
    except Exception as e:
        print(f"Error sending to Rubika: {e}")
        return False

async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    message = update.channel_post
    if not message or message.chat_id != SOURCE_TELEGRAM_CHANNEL_ID:
        return

    print(f"New message received from Telegram channel {message.chat_id}")

    caption = message.caption or message.text
    file_path = None
    file_to_download = None

    try:
        if message.photo:
            file_to_download = await message.photo[-1].get_file()
            file_path = os.path.join('temp_downloads', os.path.basename(file_to_download.file_path))
        elif message.video:
            file_to_download = await message.video.get_file()
            file_path = os.path.join('temp_downloads', os.path.basename(file_to_download.file_path))
        elif message.document:
            file_to_download = await message.document.get_file()
            file_path = os.path.join('temp_downloads', message.document.file_name)

        if file_to_download:
            print(f"Downloading file to: {file_path}")
            await file_to_download.download_to_drive(file_path)

        await forward_to_rubika(file_path, caption)

    except Exception as e:
        print(f"An error occurred in message_handler: {e}")
    finally:
        if file_path and os.path.exists(file_path):
            os.remove(file_path)
            print(f"Temporary file {file_path} deleted.")

def main() -> None:
    flask_thread = threading.Thread(target=run_flask)
    flask_thread.daemon = True
    flask_thread.start()

    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    application.add_handler(MessageHandler(filters.ChatType.CHANNEL, message_handler))

    print("Telegram bot is polling...")
    application.run_polling()

if __name__ == "__main__":
    main()
