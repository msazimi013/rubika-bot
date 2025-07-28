from flask import Flask
from rubka import Robot
from rubka.keypad import ChatKeypadBuilder
import google.generativeai as genai
import os
import sys
import threading
from datetime import date
import uuid # Needed for unique filenames
import requests

# --- Setup ---
app = Flask(__name__)
AUTH_KEY = os.environ.get("RUBIKA_AUTH_KEY")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

# --- User Data Management ---
conversation_history = {}
# 'mode' can be: None, 'awaiting_aspect_ratio', 'awaiting_image_prompt'
# 'image_options' will store the chosen aspect ratio
user_data = {}

# --- AI Model Configuration ---
text_model = None
image_model = None
if GEMINI_API_KEY:
    try:
        genai.configure(api_key=GEMINI_API_KEY)
        text_model = genai.GenerativeModel('gemini-1.5-flash-latest')
        image_model = genai.GenerativeModel('imagen-3') # Using Imagen model
    except Exception as e:
        print(f"Error configuring Gemini/Imagen: {e}", file=sys.stderr)
else:
    print("Gemini API Key not set!", file=sys.stderr)

bot = Robot(AUTH_KEY)

# --- Keyboards ---
main_keypad = (
    ChatKeypadBuilder()
    .row(ChatKeypadBuilder().button("start_chat", "💬 Chat with AI"))
    .row(ChatKeypadBuilder().button("image_gen_mode", "🎨 Generate Image (Imagen)"))
    .row(ChatKeypadBuilder().button("account_info", "👤 User Account"))
    .build()
)

aspect_ratio_keypad = (
    ChatKeypadBuilder()
    .row(ChatKeypadBuilder().button("aspect_1_1", "Square (1:1)"))
    .row(ChatKeypadBuilder().button("aspect_16_9", "Widescreen (16:9)"), ChatKeypadBuilder().button("aspect_9_16", "Portrait (9:16)"))
    .row(ChatKeypadBuilder().button("cancel", "Cancel"))
    .build()
)

# --- Main Bot Logic ---
@bot.on_message()
def process_messages(bot: Robot, msg):
    try:
        user_text = msg.text
        chat_id = msg.chat_id
        if not user_text:
            return

        print(f"Received: '{user_text}' from {chat_id}", file=sys.stderr)

        # --- User Data Initialization ---
        today = str(date.today())
        if chat_id not in user_data:
            user_data[chat_id] = {"usage_count": 0, "last_used_date": today, "plan": "free", "mode": None, "image_options": {}}
        
        # Reset daily usage count if needed
        if user_data[chat_id]["last_used_date"] != today:
            user_data[chat_id]["usage_count"] = 0
            user_data[chat_id]["last_used_date"] = today

        # --- Command Handling ---
        if user_text == "/start" or user_text == "Cancel":
            user_data[chat_id]["mode"] = None
            msg.reply_keypad("Welcome to the Gemini AI bot!", keypad=main_keypad)
            return

        # --- Image Generation Flow ---
        if user_text == "🎨 Generate Image (Imagen)":
            user_data[chat_id]["mode"] = "awaiting_aspect_ratio"
            msg.reply_keypad("Please select the aspect ratio for your image:", keypad=aspect_ratio_keypad)
            return

        current_mode = user_data[chat_id].get("mode")

        if current_mode == "awaiting_aspect_ratio":
            aspect_map = {
                "Square (1:1)": "1:1",
                "Widescreen (16:9)": "16:9",
                "Portrait (9:16)": "9:16"
            }
            if user_text in aspect_map:
                user_data[chat_id]["image_options"]["aspect_ratio"] = aspect_map[user_text]
                user_data[chat_id]["mode"] = "awaiting_image_prompt"
                msg.reply("Great! Now, please send your prompt in English:")
            else:
                msg.reply_keypad("Invalid selection. Please use the buttons.", keypad=aspect_ratio_keypad)
            return

        if current_mode == "awaiting_image_prompt":
            sent_msg = msg.reply("⏳ Generating your image with Imagen... Please wait.")
            try:
                aspect_ratio = user_data[chat_id]["image_options"]["aspect_ratio"]
                # Generate image and get the raw bytes
                image_bytes = image_model.generate_content([user_text]).parts[0].data
                
                # Save bytes to a temporary file
                filename = f"/tmp/{uuid.uuid4()}.png"
                with open(filename, "wb") as f:
                    f.write(image_bytes)

                # Send the photo from the file
                bot.send_photo(chat_id, photo=filename, caption=f"Your image for: {user_text}\nAspect Ratio: {aspect_ratio}")
                os.remove(filename) # Clean up the temp file
                bot.delete_messages(chat_id, [sent_msg["data"]["message_id"]])

            except Exception as e:
                print(f"Imagen error: {e}", file=sys.stderr)
                bot.edit_message_text(chat_id, sent_msg["data"]["message_id"], "❌ An error occurred while generating the image.")
            
            user_data[chat_id]["mode"] = None # Reset mode
            return

        # --- Text Generation Flow (Default) ---
        # (This part for checking user plan and calling Gemini for text remains the same)
        # ...

        if chat_id not in conversation_history:
            conversation_history[chat_id] = []
        
        chat_session = text_model.start_chat(history=conversation_history[chat_id])
        response = chat_session.send_message(user_text)
        ai_response = response.text
        conversation_history[chat_id] = chat_session.history
        
        msg.reply_keypad(ai_response, keypad=main_keypad)

    except Exception as e:
        print(f"A general error occurred: {e}", file=sys.stderr)
        msg.reply("An error occurred. Please start over with /start.")

# --- Web Server and Bot Execution (No changes here) ---
@app.route('/')
def index():
    return "Gemini/Imagen Rubika Bot is active."

def run_bot():
    print("Starting the Rubika bot's main loop (Gemini/Imagen)...", file=sys.stderr)
    bot.run()

bot_thread = threading.Thread(target=run_bot)
bot_thread.daemon = True
bot_thread.start()
