import os
import asyncio
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes
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

# ساخت نمونه‌ها در سطح ماژول
rubika_client = Client(RUBIKA_AUTH_KEY)
app = Flask(__name__)
application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

@app.route('/')
def home():
    return "Bot is running..."

def run_flask():
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)

async def forward_to_rubika(file_path=None, caption=None):
    try:
        if file_path:
            if file_path.lower().endswith(('.jpg', '.jpeg', '.png')):
                await rubika_client.send_photo(DESTINATION_RUBIKA_GUID, file_path, caption)
            elif file_path.lower().endswith(('.mp4', '.avi', '.mov')):
                await rubika_client.send_video(DESTINATION_RUBIKA_GUID, file_path, caption)
            else:
                 await rubika_client.send_document(DESTINATION_RUBIKA_GUID, file_path, caption)
        elif caption:
            await rubika_client.send_message(DESTINATION_RUBIKA_GUID, text=caption)
        print("Message forwarded to Rubika successfully.")
    except Exception as e:
        print(f"Error sending to Rubika: {e}")

async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    message = update.channel_post
    if not message or message.chat_id != SOURCE_TELEGRAM_CHANNEL_ID:
        return

    print(f"New message received from Telegram channel {message.chat_id}")
    caption = message.caption or message.text
    file_path = None
    # ### <<<< مشکل اول در این خط حل شد >>>> ###
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
    finally:
        if file_path and os.path.exists(file_path):
            os.remove(file_path)
            print(f"Temporary file {file_path} deleted.")

# ### <<<< مشکل دوم با این ساختار جدید حل شد >>>> ###
async def main() -> None:
    # اجرای وب سرور در یک ترد جداگانه
    flask_thread = threading.Thread(target=run_flask)
    flask_thread.daemon = True
    flask_thread.start()

    # افزودن پردازشگر به اپلیکیشن تلگرام
    application.add_handler(MessageHandler(filters.ChatType.CHANNEL, message_handler))

    # استفاده از یک بلوک with برای مدیریت صحیح راه‌اندازی و خاموش شدن
    async with application:
        # ۱. اتصال به روبیکا
        print("Connecting to Rubika...")
        await rubika_client.connect()
        print("Connected to Rubika successfully.")
        
        # ۲. شروع ربات تلگرام با پاک کردن آپدیت‌های در صف
        print("Starting Telegram bot polling...")
        await application.start()
        await application.updater.start_polling(drop_pending_updates=True)
        
        # ۳. ربات را برای همیشه در حال اجرا نگه می‌داریم
        while True:
            await asyncio.sleep(3600)

if __name__ == "__main__":
    # اجرای تابع async اصلی
    asyncio.run(main())
