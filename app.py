from flask import Flask
from rubka import Robot
from rubka.keypad import ChatKeypadBuilder
import google.generativeai as genai
import os
import sys
import threading

# --- Setup ---
app = Flask(__name__)
AUTH_KEY = os.environ.get("RUBIKA_AUTH_KEY")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

conversation_history = {}
model = None

if GEMINI_API_KEY:
    try:
        genai.configure(api_key=GEMINI_API_KEY)
        model = genai.GenerativeModel('gemini-1.5-flash-latest')
    except Exception as e:
        print(f"Error configuring Gemini: {e}", file=sys.stderr)
else:
    print("Gemini API Key not set!", file=sys.stderr)

bot = Robot(AUTH_KEY)

clear_keypad = (
    ChatKeypadBuilder()
    .row(ChatKeypadBuilder().button("clear_btn", "شروع مجدد 🔄"))
    .build()
)

# --- Bot Logic ---
@bot.on_message()
def process_messages(bot: Robot, msg):
    try:
        user_text = msg.text
        chat_id = msg.chat_id
        if not user_text or not model:
            return

        print(f"Received: '{user_text}' from {chat_id}", file=sys.stderr)

        if user_text == "/clear" or user_text == "شروع مجدد 🔄":
            conversation_history[chat_id] = []
            msg.reply_keypad("History cleared.", keypad=clear_keypad)
            return

        if chat_id not in conversation_history:
            conversation_history[chat_id] = []

        chat_session = model.start_chat(history=conversation_history[chat_id])
        response = chat_session.send_message(user_text)
        ai_response = response.text
        conversation_history[chat_id] = chat_session.history

        # Use reply_keypad to send the AI response with the keyboard
        msg.reply_keypad(ai_response, keypad=clear_keypad)

    except Exception as e:
        print(f"An error occurred: {e}", file=sys.stderr)
        try:
            # Use reply_keypad to send the error message with the keyboard
            msg.reply_keypad("An error occurred while contacting the AI.", keypad=clear_keypad)
        except Exception as e2:
            print(f"Could not send error reply: {e2}", file=sys.stderr)

# --- Web Server to Keep Bot Alive ---
@app.route('/')
def index():
    return "Gemini Rubika Bot with history and keypad is active."

# --- Start the Bot ---
def run_bot():
    print("Starting the Rubika bot's main loop...", file=sys.stderr)
    bot.run()

bot_thread = threading.Thread(target=run_bot)
bot_thread.daemon = True
bot_thread.start()
