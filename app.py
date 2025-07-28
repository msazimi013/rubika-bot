from flask import Flask
from rubka import Robot
from rubka.keypad import ChatKeypadBuilder  # 1. وارد کردن کتابخانه کیبورد
import google.generativeai as genai
import os
import sys
import threading

# --- تنظیمات اولیه ---
app = Flask(__name__)
AUTH_KEY = os.environ.get("RUBIKA_AUTH_KEY")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

conversation_history = {}

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

# 2. ساخت کیبورد "شروع مجدد"
clear_keypad = (
    ChatKeypadBuilder()
    .row(ChatKeypadBuilder().button("clear_btn", "شروع مجدد 🔄"))
    .build()
)

# --- منطق اصلی ربات ---
@bot.on_message()
def process_messages(bot: Robot, msg):
    try:
        user_text = msg.text
        chat_id = msg.chat_id
        if not user_text or not model:
            return

        print(f"Received: '{user_text}' from {chat_id}", file=sys.stderr)

        # 3. بررسی دستور پاک کردن تاریخچه از طریق متن یا دکمه
        if user_text == "/clear" or user_text == "شروع مجدد 🔄":
            conversation_history[chat_id] = []
            # ارسال پاسخ همراه با کیبورد
            msg.reply("تاریخچه مکالمه شما پاک شد. می‌توانید گفتگو را از نو شروع کنید.", keypad=clear_keypad)
            return

        if chat_id not in conversation_history:
            conversation_history[chat_id] = []
        
        chat_session = model.start_chat(history=conversation_history[chat_id])
        
        response = chat_session.send_message(user_text)
        ai_response = response.text

        conversation_history[chat_id] = chat_session.history

        # ارسال پاسخ هوش مصنوعی همراه با کیبورد
        msg.reply(ai_response, keypad=clear_keypad)
        
    except Exception as e:
        print(f"An error occurred: {e}", file=sys.stderr)
        try:
            # ارسال پیام خطا همراه با کیبورد
            msg.reply("متاسفانه در حال حاضر مشکلی در ارتباط با هوش مصنوعی وجود دارد.", keypad=clear_keypad)
        except Exception as e2:
            print(f"Could not send error reply: {e2}", file=sys.stderr)

# --- صفحه‌ای برای بیدار نگه داشتن سرور ---
@app.route('/')
def index():
    return "Gemini Rubika Bot with history and keypad is active."

# --- اجرای ربات در پشت صحنه ---
def run_bot():
    print("Starting the Rubika bot's main loop (Gemini with History & Keypad)...", file=sys.stderr)
    bot.run()

bot_thread = threading.Thread(target=run_bot)
bot_thread.daemon = True
bot_thread.start()
