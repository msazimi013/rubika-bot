from flask import Flask
from rubka import Robot
from rubka.keypad import ChatKeypadBuilder
import google.generativeai as genai
import os
import sys
import threading
from datetime import date # برای کار با تاریخ

# --- تنظیمات اولیه ---
app = Flask(__name__)
AUTH_KEY = os.environ.get("RUBIKA_AUTH_KEY")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

# --- مدیریت کاربران و تاریخچه مکالمات ---
conversation_history = {}
# ساختار داده کاربران:
# { "chat_id": {"usage_count": 0, "last_used_date": "YYYY-MM-DD", "plan": "free"} }
user_data = {}

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

# --- کیبورد اصلی ---
main_keypad = (
    ChatKeypadBuilder()
    .row(ChatKeypadBuilder().button("start_chat", "شروع مکالمه با هوش مصنوعی 💬"))
    .row(ChatKeypadBuilder().button("account_info", "حساب کاربری 👤"))
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

        # --- مدیریت کاربر ---
        today = str(date.today())
        # اگر کاربر جدید بود، اطلاعات پیش‌فرض را برایش بساز
        if chat_id not in user_data:
            user_data[chat_id] = {"usage_count": 0, "last_used_date": today, "plan": "free"}
        
        # اگر تاریخ استفاده کاربر برای دیروز بود، شمارنده را ریست کن
        if user_data[chat_id]["last_used_date"] != today:
            user_data[chat_id]["usage_count"] = 0
            user_data[chat_id]["last_used_date"] = today
            
        # --- بررسی دستورات اصلی ---
        if user_text == "/start":
            msg.reply_keypad("سلام! به ربات هوش مصنوعی جمنای خوش آمدید.", keypad=main_keypad)
            return
            
        if user_text == "حساب کاربری 👤":
            user_info = user_data[chat_id]
            plan = "رایگان" if user_info['plan'] == 'free' else "ویژه (نامحدود)"
            usage_left = 2 - user_info['usage_count']
            if usage_left < 0:
                usage_left = 0
            
            reply_text = f"👤 اطلاعات حساب شما:\n\n- طرح اشتراک: **{plan}**\n"
            if user_info['plan'] == 'free':
                reply_text += f"- پیام‌های باقی‌مانده امروز: **{usage_left}** عدد\n\nبرای استفاده نامحدود، نیاز به خرید اشتراک دارید."

            msg.reply_keypad(reply_text, keypad=main_keypad)
            return

        # دستور مخفی برای مدیر ربات جهت ویژه کردن یک کاربر
        if user_text.startswith("/subscribe"):
            # مثال: /subscribe <chat_id>
            parts = user_text.split()
            if len(parts) == 2:
                target_chat_id = parts[1]
                if target_chat_id in user_data:
                    user_data[target_chat_id]['plan'] = 'premium'
                    msg.reply(f"کاربر {target_chat_id} با موفقیت به طرح ویژه ارتقا یافت.")
                else:
                    msg.reply("کاربر یافت نشد.")
                return

        # --- پردازش پیام هوش مصنوعی ---
        current_plan = user_data[chat_id]['plan']
        usage_count = user_data[chat_id]['usage_count']

        # بررسی محدودیت استفاده برای کاربران رایگان
        if current_plan == 'free' and usage_count >= 2:
            msg.reply_keypad("شما از تمام ۲ پیام رایگان امروز خود استفاده کرده‌اید. برای استفاده نامحدود، لطفاً اشتراک تهیه کنید.", keypad=main_keypad)
            return

        # اگر کاربر مجاز به استفاده بود
        if chat_id not in conversation_history:
            conversation_history[chat_id] = []
        
        chat_session = model.start_chat(history=conversation_history[chat_id])
        response = chat_session.send_message(user_text)
        ai_response = response.text
        conversation_history[chat_id] = chat_session.history

        # افزایش شمارنده استفاده
        if current_plan == 'free':
            user_data[chat_id]['usage_count'] += 1

        msg.reply_keypad(ai_response, keypad=main_keypad)
        
    except Exception as e:
        print(f"An error occurred: {e}", file=sys.stderr)
        msg.reply("متاسفانه خطایی رخ داد. لطفاً دوباره تلاش کنید.")

# --- صفحه‌ای برای بیدار نگه داشتن سرور ---
@app.route('/')
def index():
    return "Gemini Rubika Bot with User Management is active."

# --- اجرای ربات در پشت صحنه ---
def run_bot():
    print("Starting the Rubika bot's main loop (Gemini with User Management)...", file=sys.stderr)
    bot.run()

bot_thread = threading.Thread(target=run_bot)
bot_thread.daemon = True
bot_thread.start()
