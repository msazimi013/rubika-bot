from flask import Flask, request
import requests
import os

app = Flask(__name__)

# خواندن توکن از متغیرهای محیطی Render
RUBIKA_BOT_TOKEN = os.environ.get("RUBIKA_BOT_TOKEN")

@app.route('/receiveUpdate', methods=['POST'])
def webhook():
    try:
        # داده‌ها داخل یک آبجکت به نام 'update' قرار دارند
        data = request.get_json(force=True)
        update_object = data.get('update', {})

        # استخراج اطلاعات از داخل آبجکت 'update'
        chat_id = update_object.get('chat_id')
        user_text = update_object.get('text')

        # اگر همه چیز درست بود، پاسخ را ارسال کن
        if chat_id and user_text:
            final_response = "تبریک! ربات شما با موفقیت کامل ساخته شد و پاسخ داد. 🎉"
            send_message_to_rubika(chat_id, final_response)

    except Exception as e:
        # ثبت هرگونه خطای احتمالی
        print(f"Error processing request: {e}")

    return "OK"

def send_message_to_rubika(chat_id, text):
    url = f"https://botapi.rubika.ir/v1/bots/{RUBIKA_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": chat_id, "text": text}
    requests.post(url, json=payload)
