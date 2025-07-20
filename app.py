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
            final_response = "این پاسخ نهایی است. ربات با موفقیت ساخته شد! ✅"
            send_message_to_rubika(chat_id, final_response)
    except Exception as e:
        print(f"Error processing request: {e}", file=sys.stderr)
    return "OK"

def send_message_to_rubika(chat_id, text):
    # آدرس API را بدون نام متد در انتها میسازیم
    url = f"https://botapi.rubika.ir/v1/bots/{RUBIKA_BOT_TOKEN}/"

    # ساختار صحیح payload طبق تحلیل جدید
    payload = {
        "method": "sendMessage",
        "data": {
            "chat_id": chat_id,
            "text": text
        }
    }

    print(f"--- Sending Correct Payload to Rubika: {payload} ---", file=sys.stderr)
    response = requests.post(url, json=payload)
    print(f"--- Rubika API Response --- Status: {response.status_code}, Body: {response.text}", file=sys.stderr)
