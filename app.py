from flask import Flask, request
import requests
import os

# ساخت اپلیکیشن فلسک
app = Flask(__name__)

# خواندن توکن از متغیرهای محیطی که بعدا در Render تنظیم میکنیم
RUBIKA_BOT_TOKEN = os.environ.get("RUBIKA_BOT_TOKEN", "YOUR_DEFAULT_TOKEN")

@app.route('/', methods=['POST'])
def webhook():
    try:
        data = request.get_json(force=True)
        chat_id = data['chat_id']
        test_response = "ربات با موفقیت از سرور Render پاسخ داد!"
        send_message_to_rubika(chat_id, test_response)
    except Exception as e:
        print(f"Error: {e}")
    return "OK"

def send_message_to_rubika(chat_id, text):
    url = f"https://botapi.rubika.ir/v1/bots/{RUBIKA_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": chat_id, "text": text}
    requests.post(url, json=payload)
