import os
import asyncio
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes
# توابع ارسال پیام مستقیما وارد می شوند
from rubpy.client import send_message, send_photo, send_video, send_file
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

# راه‌اندازی وب‌سرور Flask برای بیدار نگه داشتن سرویس
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is running..."

def run_flask():
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)

# این تابع بازنویسی شده است تا از توابع مستقیم استفاده کند
async def forward_to_rubika(file_path=None, caption=None):
    try:
        # دیگر آبجکت bot وجود ندارد، در هر فراخوانی auth key را ارسال می کنیم
        if file_path:
            if file_path.lower().endswith(('.jpg', '.jpeg', '.png')):
                print(f"Sending photo: {file_path} with caption: {caption}")
                await send_photo(RUBIKA_AUTH_KEY, DESTINATION_RUBIKA_GUID, file_path, caption)
            elif file_path.lower().endswith(('.mp4', '.avi', '.mov')):
                print(f"Sending video: {file_path} with caption: {caption}")
                await send_video(RUBIKA_AUTH_KEY, DESTINATION_RUBIKA_GUID, file_path, caption)
            else:
                 print(f"Sending file: {file_path} with caption: {caption}")
                 await send_file(RUBIKA_AUTH_KEY, DESTINATION_RUBIKA_GUID, file_path, caption)
        elif caption:
            print(f"Sending text: {caption}")
            await send_message(RUBIKA_AUTH_KEY, DESTINATION_RUBIKA_GUID, caption)
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
