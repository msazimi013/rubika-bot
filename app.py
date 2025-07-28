from flask import Flask
import requests
import os
import sys
import time
import threading

# --- تنظیمات اولیه اپلیکیشن وب ---
app = Flask(__name__)
RUBIKA_BOT_TOKEN = os.environ.get("RUBIKA_BOT_TOKEN")


# --- منطق اصلی ربات (که در پشت صحنه اجرا می‌شود) ---
def poll_for_updates():
    print("Starting Rubika bot polling thread...", file=sys.stderr)
    last_update_id = 0
    while True:
        try:
            BASE_URL = f"https://botapi.rubika.ir/v3/bots/{RUBIKA_BOT_TOKEN}/"
            response = requests.post(BASE_URL + "getUpdates", json={"offset_id": last_update_id + 1}, timeout=30)
            updates = response.json().get("data", {}).get("updates", [])

            if updates:
                for update in updates:
                    chat_id = update.get("chat_id")
                    text = update.get("text")

                    if chat_id and text:
                        print(f"New message: '{text}' from {chat_id}", file=sys.stderr)
                        response_text = f"پاسخ از سرور رایگان: {text}"
                        send_message_to_rubika(chat_id, response_text)

                    last_update_id = update["update_id"]
        except Exception as e:
            print(f"Error in polling loop: {e}", file=sys.stderr)

        time.sleep(1)

def send_message_to_rubika(chat_id, text):
    url = f"https://botapi.rubika.ir/v3/bots/{RUBIKA_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": chat_id, "text": text}
    try:
        requests.post(url, json=payload, timeout=10)
    except Exception as e:
        print(f"Error sending message: {e}", file=sys.stderr)


# --- صفحه‌ای برای بیدار نگه داشتن سرور ---
@app.route('/')
def index():
    return "Rubika Bot is running. Uptime check successful."


# --- اجرای ربات در پشت صحنه ---
polling_thread = threading.Thread(target=poll_for_updates)
polling_thread.daemon = True
polling_thread.start()
