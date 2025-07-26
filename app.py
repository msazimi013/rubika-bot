from flask import Flask, request
import requests
import os
import sys

app = Flask(__name__)
RUBIKA_BOT_TOKEN = os.environ.get("RUBIKA_BOT_TOKEN")

@app.route('/receiveUpdate', methods=['POST'])
def webhook():
    try:
        data = request.get_json(force=True)
        update_object = data.get('update', {})
        chat_id = update_object.get('chat_id')

        if chat_id:
            final_response = "✅ ربات با API نسخه ۳ پاسخ داد! مشکل حل شد."
            send_message_to_rubika(chat_id, final_response)
    except Exception as e:
        print(f"Error processing request: {e}", file=sys.stderr)
    return "OK"

def send_message_to_rubika(chat_id, text):
    # **تغییر اصلی اینجاست: استفاده از v3**
    url = f"https://botapi.rubika.ir/v3/bots/{RUBIKA_BOT_TOKEN}/sendMessage"

    payload = {
        "chat_id": chat_id,
        "text": text
    }

    print(f"--- Sending to Rubika v3 API: {payload} ---", file=sys.stderr)
    # استفاده از json=payload که روش استاندارد ارسال JSON است
    response = requests.post(url, json=payload, timeout=10)
    print(f"--- Rubika v3 API Response --- Status: {response.status_code}, Body: {response.text}", file=sys.stderr)
