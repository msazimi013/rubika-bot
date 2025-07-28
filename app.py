from flask import Flask
from rubka import Robot
import openai
import os
import sys
import threading

# --- تنظیمات اولیه ---
app = Flask(__name__)
AUTH_KEY = os.environ.get("RUBIKA_AUTH_KEY")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")

# بررسی و تنظیم کلید OpenAI
if not OPENAI_API_KEY:
    print("کلید API برای OpenAI تنظیم نشده است!", file=sys.stderr)
else:
    openai.api_key = OPENAI_API_KEY

# ساخت ربات با کتابخانه rubka
# فقط در صورتی که کلید احراز هویت وجود داشته باشد
bot = None
if AUTH_KEY:
    bot = Robot(AUTH_KEY)
else:
    print("کلید احراز هویت روبیکا (AUTH_KEY) تنظیم نشده است!", file=sys.stderr)

# --- منطق اصلی ربات (که در پشت صحنه اجرا می‌شود) ---
def process_messages():
    if not bot:
        print("ربات به دلیل عدم وجود کلید احراز هویت، اجرا نشد.", file=sys.stderr)
        return

    print("Starting Rubika bot polling thread...", file=sys.stderr)
    for msg in bot.on_message():
        try:
            user_text = msg.text
            if not user_text:
                continue

            print(f"Received: '{user_text}' from {msg.chat_id}", file=sys.stderr)

            # نمایش حالت "در حال نوشتن..." به کاربر
            bot.send_action(msg.chat_id, "Typing")

            # فراخوانی ChatGPT
            response = openai.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": user_text}]
            )
            ai_response = response.choices[0].message.content

            # ارسال پاسخ هوش مصنوعی به کاربر
            msg.reply(ai_response)

        except Exception as e:
            print(f"An error occurred: {e}", file=sys.stderr)
            try:
                msg.reply("متاسفانه در حال حاضر مشکلی در ارتباط با هوش مصنوعی وجود دارد.")
            except Exception as e2:
                print(f"Could not send error reply: {e2}", file=sys.stderr)

# --- صفحه‌ای برای بیدار نگه داشتن سرور ---
@app.route('/')
def index():
    return "ChatGPT Rubika Bot is active and running."

# --- اجرای ربات در پشت صحنه ---
# فقط در صورتی که ربات با موفقیت ساخته شده باشد، آن را اجرا کن
if bot:
    polling_thread = threading.Thread(target=process_messages)
    polling_thread.daemon = True
    polling_thread.start()
