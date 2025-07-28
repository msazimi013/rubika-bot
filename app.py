from flask import Flask
from rubka import Robot
import google.generativeai as genai
import os
import sys
import threading

# --- تنظیمات اولیه ---
app = Flask(__name__)
AUTH_KEY = os.environ.get("RUBIKA_AUTH_KEY")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

# دیکشنری برای ذخیره تاریخچه مکالمات هر کاربر
conversation_history = {}

# بررسی و تنظیم کلید Gemini
model = None
if GEMINI_API_KEY:
    try:
        genai.configure(api_key=GEMINI_API_KEY)
        model = genai.GenerativeModel('gemini-1.5-flash-latest')
    except Exception as e:
        print(f"خطا در تنظیم Gemini: {e}", file=sys.stderr)
else:
    print("کلید API برای Gemini تنظیم نشده است!", file=sys.stderr)

bot = Robot(AUTH_KEY)

# --- منطق اصلی ربات ---
@bot.on_message()
def process_messages(bot: Robot, msg):
    try:
        user_text = msg.text
        chat_id = msg.chat_id
        if not user_text or not model:
            return

        print(f"Received: '{user_text}' from {chat_id}", file=sys.stderr)

        # دستور برای پاک کردن تاریخچه
        if user_text == "/clear":
            conversation_history[chat_id] = []
            msg.reply("تاریخچه مکالمه شما پاک شد.")
            return

        # دریافت تاریخچه مکالمه قبلی کاربر
        if chat_id not in conversation_history:
            conversation_history[chat_id] = []

        # شروع یک جلسه چت جدید با تاریخچه قبلی
        chat_session = model.start_chat(history=conversation_history[chat_id])

        # ارسال پیام جدید به Gemini
        response = chat_session.send_message(user_text)
        ai_response = response.text

        # به‌روزرسانی تاریخچه با پیام جدید کاربر و پاسخ مدل
        conversation_history[chat_id] = chat_session.history

        # ارسال پاسخ به کاربر
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
    return "Gemini Rubika Bot with history is active."

# --- اجرای ربات در پشت صحنه ---
def run_bot():
    print("Starting the Rubika bot's main loop (Gemini with History)...", file=sys.stderr)
    bot.run()

bot_thread = threading.Thread(target=run_bot)
bot_thread.daemon = True
bot_thread.start()
