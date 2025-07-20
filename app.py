from flask import Flask, request
import requests
import os
import sys # برای لاگ‌گیری دقیق

app = Flask(__name__)
RUBIKA_BOT_TOKEN = os.environ.get("JHFC0XRMULRIXCNUCKEEPVBCOIYMTSPPBXQYIKKDASNGDIQDGJFXECIPHYOXABPE")

@app.route('/receiveUpdate', methods=['POST'])
def webhook():
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

    print(f"--- Sending POST to Rubika API at {url} ---", file=sys.stderr)
    response = requests.post(url, json=payload)

    # این خط مهم‌ترین بخش است: ما پاسخ روبیکا را در لاگ چاپ می‌کنیم
    print(f"--- Rubika API Response --- Status: {response.status_code}, Body: {response.text}", file=sys.stderr)
