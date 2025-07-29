from flask import Flask
from rubka import Robot
import telegram
import asyncio
import os
import sys
import threading
import time

# --- تنظیمات اولیه ---
app = Flask(__name__)
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
RUBIKA_AUTH_KEY = os.environ.get("RUBIKA_AUTH_KEY")
RUBIKA_TARGET_CHAT_ID = os.environ.get("RUBIKA_TARGET_CHAT_ID")

# ساخت ربات‌ها
rubika_bot = Robot(RUBIKA_AUTH_KEY)
telegram_bot = telegram.Bot(token=TELEGRAM_BOT_TOKEN)

# --- منطق اصلی پل (که در پشت صحنه اجرا می‌شود) ---
async def bridge_logic():
    print("Starting the Telegram-Rubika bridge thread...", file=sys.stderr)
    update_offset = 0
    while True:
        try:
            # دریافت پیام‌های جدید از تلگرام
            updates = await telegram_bot.get_updates(offset=update_offset, timeout=30)
            for update in updates:
                if update.message and update.message.text:
                    user_message = update.message.text
                    # ایجاد یک فرمت بهتر برای پیام ارسالی
                    sender_name = update.message.from_user.first_name
                    forwarded_message = f"پیام جدید از تلگرام (از طرف: {sender_name}):\n\n{user_message}"
                    
                    print(f"Received from Telegram: '{user_message}'", file=sys.stderr)
                    
                    # ارسال پیام به روبیکا
                    rubika_bot.send_message(RUBIKA_TARGET_CHAT_ID, forwarded_message)
                    print("Forwarded to Rubika.", file=sys.stderr)
                
                update_offset = update.update_id + 1
        except Exception as e:
            print(f"An error in bridge_logic: {e}", file=sys.stderr)
            time.sleep(10) # در صورت بروز خطا، ۱۰ ثانیه صبر کن

def run_async_loop():
    # چون کتابخانه تلگرام async است، باید آن را در یک event loop اجرا کنیم
    asyncio.run(bridge_logic())

# --- صفحه‌ای برای بیدار نگه داشتن سرور ---
@app.route('/')
def index():
    return "Telegram-Rubika Bridge is active."

# --- اجرای ربات در پشت صحنه ---
bot_thread = threading.Thread(target=run_async_loop)
bot_thread.daemon = True
bot_thread.start()
