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
            final_response = "آخرین آزمایش: ارسال با فرمت متفاوت."
            send_message_to_rubika(chat_id, final_response)
    except Exception as e:
        print(f"Error processing request: {e}", file=sys.stderr)
    return "OK"

def send_message_to_rubika(chat_id, text):
    # آدرس صحیح متد طبق مستندات
    url = f"https://botapi.rubika.ir/v1/bots/{RUBIKA_BOT_TOKEN}/sendMessage"

    # ساختار payload به صورت یک دیکشنری ساده
    payload = {
        "chat_id": chat_id,
        "text": text
    }

    # مهم: ارسال با پارامتر 'data' به جای 'json'
    print(f"--- Sending as Form Data to Rubika: {payload} ---", file=sys.stderr)
    response = requests.post(url, data=payload)
    print(f"--- Final Rubika API Response --- Status: {response.status_code}, Body: {response.text}", file=sys.stderr)
