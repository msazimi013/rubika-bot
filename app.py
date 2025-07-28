from flask import Flask
from rubka import Robot
import openai
import os
import sys
import threading

# --- Setup ---
app = Flask(__name__)
AUTH_KEY = os.environ.get("RUBIKA_AUTH_KEY")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")

if OPENAI_API_KEY:
    openai.api_key = OPENAI_API_KEY
else:
    print("OpenAI API Key not set!", file=sys.stderr)

bot = Robot(AUTH_KEY)

# --- Bot Logic ---
# Use the decorator to define the message handler
@bot.on_message()
def process_messages(bot: Robot, msg): # The function that will handle messages
    try:
        user_text = msg.text
        if not user_text:
            return

        print(f"Received: '{user_text}' from {msg.chat_id}", file=sys.stderr)

        response = openai.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": user_text}]
        )
        ai_response = response.choices[0].message.content

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
    return "ChatGPT Rubika Bot is active."

# --- Start the Bot ---
def run_bot():
    print("Starting the Rubika bot's main loop...", file=sys.stderr)
    bot.run()

# Run the bot in a background thread
bot_thread = threading.Thread(target=run_bot)
bot_thread.daemon = True
bot_thread.start()
