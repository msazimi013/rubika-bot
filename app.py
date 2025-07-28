from flask import Flask
from rubka import Robot
from rubka.keypad import ChatKeypadBuilder
import google.generativeai as genai
import requests # برای ارسال درخواست به سرویس تصویرساز
import os
import sys
import threading
from datetime import date

# --- تنظیمات اولیه ---
app = Flask(__name__)
AUTH_KEY = os.environ.get("RUBIKA_AUTH_KEY")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

# --- مدیریت کاربران و تاریخچه مکالمات ---
conversation_history = {}
# یک کلید "mode" برای مدیریت حالت کاربر اضافه میکنیم
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

# --- کیبورد اصلی با دکمه جدید ---
main_keypad = (
    ChatKeypadBuilder()
    .row(ChatKeypadBuilder().button("start_chat", "شروع مکالمه با هوش مصنوعی 💬"))
    .row(ChatKeypadBuilder().button("image_gen_mode", "ساخت تصویر 🎨")) # دکمه جدید
    .row(ChatKeypadBuilder().button("account_info", "حساب کاربری 👤"))
    .build()
)

# --- منطق اصلی ربات ---
@bot.on_message()
def process_messages(bot: Robot, msg):
    try:
        user_text = msg.text
        chat_id = msg.chat_id
        if not user_text:
            return

        print(f"Received: '{user_text}' from {chat_id}", file=sys.stderr)

        # --- مدیریت کاربر ---
        today = str(date.today())
        if chat_id not in user_data:
            user_data[chat_id] = {"usage_count": 0, "last_used_date": today, "plan": "free", "mode": None}
        
        if user_data[chat_id]["last_used_date"] != today:
            user_data[chat_id]["usage_count"] = 0
            user_data[chat_id]["last_used_date"] = today

        # --- بررسی دستورات و دکمه‌ها ---
        if user_text == "/start":
            user_data[chat_id]["mode"] = None # ریست کردن حالت کاربر
            msg.reply_keypad("سلام! به ربات هوش مصنوعی جمنای خوش آمدید.", keypad=main_keypad)
            return
            
        if user_text == "حساب کاربری 👤":
            # ... (کد این بخش بدون تغییر باقی میماند)
            user_info = user_data[chat_id]
            plan = "رایگان" if user_info['plan'] == 'free' else "ویژه (نامحدود)"
            usage_left = 2 - user_info['usage_count']
            if usage_left < 0: usage_left = 0
            reply_text = f"👤 اطلاعات حساب شما:\n\n- طرح اشتراک: **{plan}**\n"
            if user_info['plan'] == 'free':
                reply_text += f"- پیام‌های باقی‌مانده امروز: **{usage_left}** عدد"
            msg.reply_keypad(reply_text, keypad=main_keypad)
            return

        # قرار دادن ربات در حالت تولید تصویر
        if user_text == "ساخت تصویر 🎨":
            user_data[chat_id]["mode"] = "image_gen"
            msg.reply("لطفاً موضوع یا متن مورد نظر خود را برای ساخت تصویر ارسال کنید (به انگلیسی):")
            return

        # --- بررسی حالت فعلی کاربر ---
        current_mode = user_data[chat_id].get("mode")

        # اگر کاربر در حالت تولید تصویر بود
        if current_mode == "image_gen":
            sent_message = msg.reply("⏳ در حال ساخت تصویر شما... لطفاً کمی صبر کنید.")
            try:
                # ارسال درخواست به API تصویرساز
                api_url = f"http://v3.api-free.ir/image/?text={user_text}"
                response = requests
