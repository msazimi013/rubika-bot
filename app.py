from flask import Flask, request
import requests
import os
import sys

app = Flask(__name__)

# خواندن توکن از متغیرهای محیطی Render
RUBIKA_BOT_TOKEN = os.environ.get("RUBIKA_BOT_TOKEN")

# گوش دادن به آدرس صحیح که روبیکا به آن پیام میفرستد
@app.route('/receiveUpdate', methods=['POST'])
def webhook():
    try:
        data = request.get_json(force=True)
        update_object = data.get('update', {})
        chat_id = update_object.get('chat_id')
        
        if chat_id:
            final_response = "✅ ربات با موفقیت به پیام شما پاسخ داد."
            send_message_to_rubika(chat_id, final_response)
    except Exception as e:
        print(f"Error processing request: {e}", file=sys.stderr)
    return "OK"

def send_message_to_rubika(chat_id, text):
    # استفاده از آدرس صحیح متد طبق مستندات
    url = f"https://botapi.rubika.ir/v1/bots/{RUBIKA_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": chat_id, "text": text}
    
    print(f"--- Sending to Rubika: {payload} ---", file=sys.stderr)
    response = requests.post(url, json=payload)
    print(f"--- Rubika API Response --- Status: {response.status_code}, Body: {response.text}", file=sys.stderr)
