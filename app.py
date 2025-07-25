from flask import Flask, request
import requests
import os
import sys

app = Flask(__name__)
RUBIKA_BOT_TOKEN = os.environ.get("RUBIKA_BOT_TOKEN")

# ----- بخش تست جدید -----
@app.route('/test-api', methods=['GET'])
def test_api():
    """
    این تابع وقتی آدرس /test-api را باز کنید، اجرا میشود.
    """
    print("--- RUNNING getMe TEST ---", file=sys.stderr)

    METHOD_NAME = "getMe"
    url = f"https://botapi.rubika.ir/v1/bots/{RUBIKA_BOT_TOKEN}/{METHOD_NAME}"

    log_message = ""
    try:
        # یک درخواست ساده برای متد getMe ارسال میکنیم
        response = requests.post(url, json={}, timeout=10)

        # نتیجه را آماده میکنیم تا هم در لاگ چاپ شود و هم در مرورگر نمایش داده شود
        log_message = f"Status: {response.status_code}, Body: {response.text}"
        print(log_message, file=sys.stderr)

    except Exception as e:
        log_message = f"An error occurred: {e}"
        print(log_message, file=sys.stderr)

    return log_message


# ----- بخش وبهوک اصلی ربات -----
@app.route('/receiveUpdate', methods=['POST'])
def webhook():
    # این بخش بدون تغییر باقی میماند
    try:
        data = request.get_json(force=True)
        update_object = data.get('update', {})
        chat_id = update_object.get('chat_id')

        if chat_id:
            response_text = "در حال ارسال پاسخ..."
            send_message_to_rubika(chat_id, response_text)
    except Exception as e:
        print(f"Error processing request: {e}", file=sys.stderr)
    return "OK"

def send_message_to_rubika(chat_id, text):
    url = f"https://botapi.rubika.ir/v1/bots/{RUBIKA_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": chat_id, "text": text}
    requests.post(url, json=payload)
