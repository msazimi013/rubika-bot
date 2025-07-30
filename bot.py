import os
import asyncio
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes
from rubika.bot import Bot # <--- این خط تغییر کرده است
import threading
from flask import Flask

# --- بخش تنظیمات ---
# این مقادیر را با اطلاعات خود جایگزین نکنید!
# در مرحله استقرار، این‌ها را به عنوان متغیرهای محیطی (Environment Variables) تنظیم می‌کنیم.
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
RUBIKA_AUTH_KEY = os.getenv('RUBIKA_AUTH_KEY')
SOURCE_TELEGRAM_CHANNEL_ID = int(os.getenv('SOURCE_TELEGRAM_CHANNEL_ID', '0'))
DESTINATION_RUBIKA_GUID = os.getenv('DESTINATION_RUBIKA_GUID')
# --------------------

# ایجاد یک پوشه موقت برای دانلود فایل‌ها
if not os.path.exists('temp_downloads'):
    os.makedirs('temp_downloads')

# راه‌اندازی ربات روبیکا
rubika_bot = Bot(RUBIKA_AUTH_KEY)

# راه‌اندازی وب‌سرور Flask برای بیدار نگه داشتن سرویس
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is running..."

def run_flask():
    # پورت را روی مقداری که Render تعیین می‌کند تنظیم می‌کنیم
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)

async def forward_to_rubika(file_path=None, caption=None):
    """
    تابعی برای ارسال پیام متنی، عکس یا ویدیو به روبیکا
    """
    try:
        if file_path:
            # تشخیص نوع فایل بر اساس پسوند
            if file_path.lower().endswith(('.jpg', '.jpeg', '.png')):
                print(f"Sending photo: {file_path} with caption: {caption}")
                await rubika_bot.send_photo(DESTINATION_RUBIKA_GUID, file_path, caption)
            elif file_path.lower().endswith(('.mp4', '.avi', '.mov')):
                print(f"Sending video: {file_path} with caption: {caption}")
                await rubika_bot.send_video(DESTINATION_RUBIKA_GUID, file_path, caption)
            else:
                 print(f"Sending file: {file_path} with caption: {caption}")
                 await rubika_bot.send_file(DESTINATION_RUBIKA_GUID, file_path, caption)
        elif caption: # اگر فقط متن باشد
            print(f"Sending text: {caption}")
            await rubika_bot.send_message(DESTINATION_RUBIKA_GUID, caption)
        print("Message forwarded to Rubika successfully.")
        return True
    except Exception as e:
        print(f"Error sending to Rubika: {e}")
        return False

async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    این تابع هر پیامی را در کانال تلگرام پردازش می‌کند.
    """
    message = update.channel_post
    if not message or message.chat_id != SOURCE_TELEGRAM_CHANNEL_ID:
        return

    print(f"New message received from Telegram channel {message.chat_id}")

    caption = message.caption or message.text
    file_path = None
    file_to_download = None

    try:
        # تشخیص نوع پیام (عکس، ویدیو یا فایل)
        if message.photo:
            file_to_download = await message.photo[-1].get_file()
            file_path = os.path.join('temp_downloads', os.path.basename(file_to_download.file_path))
        elif message.video:
            file_to_download = await message.video.get_file()
            file_path = os.path.join('temp_downloads', os.path.basename(file_to_download.file_path))
        elif message.document:
            file_to_download = await message.document.get_file()
            file_path = os.path.join('temp_downloads', message.document.file_name)

        # دانلود فایل در صورت وجود
        if file_to_download:
            print(f"Downloading file to: {file_path}")
            await file_to_download.download_to_drive(file_path)

        # ارسال به روبیکا
        await forward_to_rubika(file_path, caption)

    except Exception as e:
        print(f"An error occurred in message_handler: {e}")
    finally:
        # پاک کردن فایل موقت پس از ارسال
        if file_path and os.path.exists(file_path):
            os.remove(file_path)
            print(f"Temporary file {file_path} deleted.")

def main() -> None:
    """شروع به کار ربات."""
    # اجرای وب سرور در یک ترد جداگانه
    flask_thread = threading.Thread(target=run_flask)
    flask_thread.daemon = True
    flask_thread.start()

    # ساخت اپلیکیشن تلگرام
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    # افزودن پردازشگر پیام‌های کانال
    application.add_handler(MessageHandler(filters.ChatType.CHANNEL, message_handler))

    # شروع به کار ربات تلگرام
    print("Telegram bot is polling...")
    application.run_polling()

if __name__ == "__main__":
    main()
