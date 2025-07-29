from rubka import Robot
import os
import sys

# خواندن کلید از متغیرهای محیطی
AUTH_KEY = os.environ.get("RUBIKA_AUTH_KEY")

if not AUTH_KEY:
    print("کلید RUBIKA_AUTH_KEY تنظیم نشده است. برنامه متوقف شد.", file=sys.stderr)
    exit()

print("در حال اجرای اسکریپت تست روبیکا...", file=sys.stderr)
bot = Robot(AUTH_KEY)

@bot.on_message()
def handle_rubika_message(bot: Robot, msg):
    try:
        print(f"--- پیام در روبیکا دریافت شد ---", file=sys.stderr)
        print(f"متن: {msg.text}", file=sys.stderr)
        print(f"شناسه چت: {msg.chat_id}", file=sys.stderr)
        msg.reply("تست موفقیت آمیز بود! اتصال با روبیکا کار می‌کند.")
    except Exception as e:
        print(f"خطا در پردازش پیام: {e}", file=sys.stderr)

print("ربات در حال گوش دادن به پیام‌های روبیکا است...", file=sys.stderr)
bot.run()
