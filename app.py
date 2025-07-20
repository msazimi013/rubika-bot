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
            final_response = "✅ این یک شروع تازه است! ربات با آخرین تحلیل از مستندات پاسخ داد."
            send_message_to_rubika(chat_id, final_response)
    except Exception as e:
        print(f"Error processing request: {e}", file=sys.stderr)
    return "OK"

def send_message_to_rubika(chat_id, text):
    # آدرس پایه API بدون هیچ متدی در انتها
    url = f"https://botapi.rubika.ir/v1/bots/{RUBIKA_BOT_TOKEN}/"

    # ساختار نهایی payload که شامل نام متد نیز می‌باشد
    payload = {
        "method": "sendMessage",
        "chat_id": chat_id,
        "text": text
    }

    print(f"--- Sending Final Payload Structure: {payload} ---", file=sys.stderr)
    response = requests.post(url, json=payload)
    print(f"--- Final Rubika API Response --- Status: {response.status_code}, Body: {response.text}", file=sys.stderr)
