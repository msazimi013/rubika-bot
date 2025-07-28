from flask import Flask
from rubka import Robot
import google.generativeai as genai
import os
import sys
import threading

# --- Setup ---
app = Flask(__name__)
AUTH_KEY = os.environ.get("RUBIKA_AUTH_KEY")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

# Configure the Gemini API and model
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

# --- Bot Logic ---
@bot.on_message()
def process_messages(bot: Robot, msg):
    try:
        user_text = msg.text
        if not user_text or not model:
            return

        print(f"Received: '{user_text}' from {msg.chat_id}", file=sys.stderr)
        
        # Call the Gemini API
        response = model.generate_content(user_text)
        ai_response = response.text

        # Send the reply
        msg.reply(ai_response)
        
    except Exception as e:
        print(f"An error occurred: {e}", file=sys.stderr)
        try:
            msg.reply("An error occurred while contacting the AI.")
        except Exception as e2:
            print(f"Could not send error reply: {e2}", file=sys.stderr)

# --- Web Server to Keep Bot Alive ---
@app.route('/')
def index():
    return "Gemini Rubika Bot is active."

# --- Start the Bot ---
def run_bot():
    print("Starting the Rubika bot's main loop (Gemini)...", file=sys.stderr)
    bot.run()

bot_thread = threading.Thread(target=run_bot)
bot_thread.daemon = True
bot_thread.start()
