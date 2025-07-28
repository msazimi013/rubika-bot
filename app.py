from flask import Flask
from rubka import Robot, Message
import openai
import os
import sys
import threading
import time

# --- تنظیمات اولیه ---
app = Flask(__name__)
AUTH_KEY = os.environ.get("RUBIKA_AUTH_KEY")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")

# تنظیم کلید OpenAI
if OPENAI_API_KEY:
    openai.api_key = OPENAI_API_KEY
else:
    print("کلید API برای OpenAI تنظیم نشده است!", file=sys.stderr)

bot = Robot(AUTH_KEY)

# --- منطق اصلی ربات ---
def process_messages():
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
                messages=[
                    {"role": "user", "content": user_text}
                ]
            )
            ai_response = response.choices[0].message.content

            # ارسال پاسخ هوش مصنوعی به کاربر
            msg.reply(ai_response)

        except Exception as e:
            print(f"An error occurred: {e}", file=sys.stderr)
            try:
                # در صورت بروز خطا، یک پیام خطا به کاربر ارسال کن
                msg.reply("متاسفانه در حال حاضر مشکلی در ارتباط با هوش مصنوعی وجود دارد. لطفاً بعداً دوباره تلاش کنید.")
            except Exception as e2:
                print(f"Could not send error reply: {e2}", file=sys.stderr)

# --- صفحه‌ای برای بیدار نگه داشتن سرور ---
@app.route('/')
def index():
    return "ChatGPT Rubika Bot is running. Uptime check successful."

# --- اجرای ربات در پشت صحنه ---
polling_thread = threading.Thread(target=process_messages)
polling_thread.daemon = True
polling_thread.start()
