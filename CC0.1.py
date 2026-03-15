import os
from openai import OpenAI
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, CommandHandler, filters, ContextTypes
from flask import Flask
from threading import Thread

# ---------------- WEB SERVER ----------------
app_web = Flask('')

@app_web.route('/')
def home():
    return "CC AI Bot Running 🚀"

def run():
    port = int(os.environ.get("PORT", 10000))
    app_web.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run)
    t.start()


# ---------------- API KEYS ----------------
OPENROUTER_API_KEY_LLAMA = os.getenv("OPENROUTER_API_KEY_LLAMA")
OPENROUTER_API_KEY_NVIDIA = os.getenv("OPENROUTER_API_KEY_NVIDIA")

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")


# ---------------- AI CLIENTS ----------------
client_llama = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=OPENROUTER_API_KEY_LLAMA
)

client_nvidia = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=OPENROUTER_API_KEY_NVIDIA
)


# ---------------- USER MEMORY ----------------
user_memory = {}


# ---------------- START COMMAND ----------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🤖 Hello! I am CC AI Bot.\nAsk me anything."
    )


# ---------------- AI RESPONSE FUNCTION ----------------
def generate_ai_response(messages):

    # ---- TRY LLAMA 3.2 3B FIRST (FAST) ----
    try:
        response = client_llama.chat.completions.create(
            model="meta-llama/llama-3.2-3b-instruct:free",
            messages=messages
        )

        return response.choices[0].message.content

    except Exception as e:
        print("Llama model failed:", e)

    # ---- FALLBACK NVIDIA MODEL ----
    try:
        response = client_nvidia.chat.completions.create(
            model="nvidia/nemotron-nano-9b-v2:free",
            messages=messages
        )

        return response.choices[0].message.content

    except Exception as e:
        print("Nvidia model failed:", e)

    return "⚠️ AI server busy. Please try again."


# ---------------- MESSAGE HANDLER ----------------
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user_id = update.message.chat_id
    user_input = update.message.text

    if user_id not in user_memory:
        user_memory[user_id] = []

    user_memory[user_id].append(
        {"role": "user", "content": user_input}
    )

    messages = [
        {"role": "system", "content": "You are a helpful AI assistant."}
    ] + user_memory[user_id]

    ai_reply = generate_ai_response(messages)

    user_memory[user_id].append(
        {"role": "assistant", "content": ai_reply}
    )

    await update.message.reply_text(ai_reply)


# ---------------- BOT START ----------------
keep_alive()

app = ApplicationBuilder().token(BOT_TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.TEXT, handle_message))

print("CC AI Bot Running...")

app.run_polling()
