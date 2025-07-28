from flask import Flask
from rubka import Robot
from rubka.keypad import ChatKeypadBuilder
import google.generativeai as genai
import os
import sys
import threading
from datetime import date
import uuid

# --- Setup ---
app = Flask(__name__)
AUTH_KEY = os.environ.get("RUBIKA_AUTH_KEY")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

# --- User Data Management ---
conversation_history = {}
user_data = {}

# --- AI Model Configuration ---
model = None
if GEMINI_API_KEY:
    try:
        genai.configure(api_key=GEMINI_API_KEY)
        model = genai.GenerativeModel('gemini-1.5-pro-latest')
    except Exception as e:
        print(f"Error configuring Gemini: {e}", file=sys.stderr)
else:
    print("Gemini API Key not set!", file=sys.stderr)

bot = Robot(AUTH_KEY)

# --- Keyboards ---
main_keypad = (
    ChatKeypadBuilder()
    .row(ChatKeypadBuilder().button("start_chat", "💬 چت با هوش مصنوعی"))
    .row(ChatKeypadBuilder().button("image_gen_mode", "🎨 ساخت تصویر"))
    .row(ChatKeypadBuilder().button("account_info", "👤 حساب کاربری"))
    .build()
)

aspect_ratio_keypad = (
    ChatKeypadBuilder()
    .row(ChatKeypadBuilder().button("aspect_1_1", "مربع (1:1)"))
    .row(ChatKeypadBuilder().button("aspect_16_9", "افقی (16:9)"), ChatKeypadBuilder().button("aspect_9_16", "عمودی (9:16)"))
    .row(ChatKeypadBuilder().button("cancel", "انصراف"))
    .build()
)

# --- Main Bot Logic ---
@bot.on_message()
def process_messages(bot: Robot, msg):
    try:
        user_text = msg.text
        chat_id = msg.chat_id
        if not user_text or not model:
            return

        print(f"Received: '{user_text}' from {chat_id}", file=sys.stderr)

        # Initialize user data if new
        if chat_id not in user_data:
            user_data[chat_id] = {"mode": None, "image_options": {}}

        # Command Handling
        if user_text == "/start" or user_text == "انصراف":
            user_data[chat_id]["mode"] = None
            msg.reply_keypad("خوش آمدید!", keypad=main_keypad)
            return
        
        # Start image generation flow
        if user_text == "🎨 ساخت تصویر":
            user_data[chat_id]["mode"] = "awaiting_aspect_ratio"
            msg.reply_keypad("لطفاً نسبت ابعاد تصویر خود را انتخاب کنید:", keypad=aspect_ratio_keypad)
            return

        current_mode = user_data[chat_id].get("mode")

        # Handle aspect ratio selection
        if current_mode == "awaiting_aspect_ratio":
            aspect_map = {"مربع (1:1)": 1, "افقی (16:9)": 2, "عمودی (9:16)": 3}
            if user_text in aspect_map:
                user_data[chat_id]["image_options"]["aspect_ratio"] = aspect_map[user_text]
                user_data[chat_id]["mode"] = "awaiting_image_prompt"
                msg.reply("عالی! حالا موضوع خود را برای ساخت تصویر ارسال کنید:")
            else:
                msg.reply_keypad("انتخاب نامعتبر است. لطفاً از دکمه‌ها استفاده کنید.", keypad=aspect_ratio_keypad)
            return

        # Handle image prompt and generate image
        if current_mode == "awaiting_image_prompt":
            sent_msg = msg.reply("⏳ در حال ساخت تصویر شما... لطفاً کمی صبر کنید.")
            try:
                # Use the user's Persian text directly as the prompt
                generation_prompt = user_text
                
                response = model.generate_content(generation_prompt, generation_config={"response_mime_type": "image/png"})
                image_bytes = response.parts[0].data
                
                filename = f"/tmp/{uuid.uuid4()}.png"
                with open(filename, "wb") as f:
                    f.write(image_bytes)

                bot.send_photo(chat_id, photo=filename, caption=f"تصویر شما با موضوع: {user_text}")
                os.remove(filename)
                bot.delete_messages(chat_id, [sent_msg["data"]["message_id"]])

            except Exception as e:
                print(f"Imagen error: {e}", file=sys.stderr)
                bot.edit_message_text(chat_id, sent_msg["data"]["message_id"], "❌ خطایی هنگام ساخت تصویر رخ داد.")
            
            user_data[chat_id]["mode"] = None # Reset mode
            return

        # --- Default Text Generation Flow ---
        if chat_id not in conversation_history:
            conversation_history[chat_id] = []
        
        chat_session = model.start_chat(history=conversation_history[chat_id])
        response = chat_session.send_message(user_text)
        ai_response = response.text
        conversation_history[chat_id] = chat_session.history
        
        msg.reply_keypad(ai_response, keypad=main_keypad)

    except Exception as e:
        print(f"A general error occurred: {e}", file=sys.stderr)
        msg.reply("خطایی رخ داد. لطفاً با دستور /start مجدداً شروع کنید.")

# --- Web Server and Bot Execution (No changes here) ---
@app.route('/')
def index():
    return "Gemini/Imagen Rubika Bot is active."

def run_bot():
    print("Starting the Rubika bot's main loop...", file=sys.stderr)
    bot.run()

bot_thread = threading.Thread(target=run_bot)
bot_thread.daemon = True
bot_thread.start()
