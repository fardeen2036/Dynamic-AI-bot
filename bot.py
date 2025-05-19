import os
import uuid
import logging
import redis
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
import google.generativeai as genai
from textblob import TextBlob
import speech_recognition as sr
from pydub import AudioSegment

# FFMPEG 
AudioSegment.converter = r"D:\Downloads\ffmpeg-7.1.1-essentials_build\ffmpeg-7.1.1-essentials_build\bin\ffmpeg.exe"

# Logging config
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

logger = logging.getLogger(__name__)

# Redis 
redis_client = redis.Redis(host="localhost", port=6379, db=0, decode_responses=True)

# Gemini
GEMINI_API_KEY = "YOUR_GEMINI_API_KEY"
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-2.0-flash-exp")

CREATOR_NAME = "Fardeen"
user_sentiment_tracker = {}

def detect_sentiment(text: str) -> str:
    blob = TextBlob(text)
    polarity = blob.sentiment.polarity
    if polarity > 0.2:
        return "positive"
    elif polarity < -0.2:
        return "negative"
    else:
        return "neutral"

async def generate_reply(user_id: str, text: str) -> str:
    if "who created you" in text.lower():
        return f"I was created by {CREATOR_NAME}, a brilliant mind! 🧠"

    try:
        # Store message history in Redis
        redis_client.lpush(f"user:{user_id}:history", text)
        response = model.generate_content(text)
        redis_client.lpush(f"user:{user_id}:history", response.text.strip())
        return response.text.strip()
    except Exception as e:
        logger.error(f"Error generating reply: {e}")
        return "Sorry, something went wrong while generating the reply."

def voice_to_text(file_path):
    recognizer = sr.Recognizer()
    try:
        wav_path = file_path.replace(".ogg", ".wav")
        audio = AudioSegment.from_ogg(file_path)
        audio.export(wav_path, format="wav")
        with sr.AudioFile(wav_path) as source:
            audio_data = recognizer.record(source)
            return recognizer.recognize_google(audio_data)
    except Exception as e:
        logger.error(f"Voice-to-text error: {e}")
        return f"Sorry, I couldn’t understand the audio. Error: {str(e)}"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Hello! I’m your AI-powered assistant 🤖. Type or send voice to begin!")

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        user_id = str(update.message.from_user.id)
        user_input = update.message.text
        sentiment = detect_sentiment(user_input)
        logger.info(f"User [{user_id}] sent: {user_input}")

        # Sentiment response logic
        last = user_sentiment_tracker.get(user_id, {"count":0, "last_sentiment": None})
        if sentiment in ("positive", "negative"):
            if last["count"] >= 3 or last["last_sentiment"] != sentiment:
                msg = "😊 You sound happy!" if sentiment == "positive" else "😟 You sound down. I'm here for you."
                await update.message.reply_text(msg)
                user_sentiment_tracker[user_id] = {"count": 0, "last_sentiment": sentiment}
            else:
                user_sentiment_tracker[user_id]["count"] += 1
        else:
            user_sentiment_tracker[user_id] = {"count": last.get("count", 0) + 1, "last_sentiment": sentiment}

        reply = await generate_reply(user_id, user_input)
        await update.message.reply_text(reply)
        logger.info(f"Replied to [{user_id}]: {reply}")

    except Exception as e:
        logger.error(f"handle_text error: {e}")
        await update.message.reply_text("⚠️ An error occurred while processing your message.")

async def handle_voice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        user_id = str(update.message.from_user.id)
        voice = update.message.voice
        file = await context.bot.get_file(voice.file_id)
        file_name = f"voice_{uuid.uuid4()}.ogg"
        await file.download_to_drive(file_name)

        text = voice_to_text(file_name)
        await update.message.reply_text(f"🗣️ You said: {text}")
        logger.info(f"Voice from [{user_id}] converted to: {text}")

        sentiment = detect_sentiment(text)
        last = user_sentiment_tracker.get(user_id, {"count":0, "last_sentiment": None})

        if sentiment in ("positive", "negative"):
            if last["count"] >= 3 or last["last_sentiment"] != sentiment:
                msg = "😊 You sound happy!" if sentiment == "positive" else "😟 You sound down. I'm here for you."
                await update.message.reply_text(msg)
                user_sentiment_tracker[user_id] = {"count": 0, "last_sentiment": sentiment}
            else:
                user_sentiment_tracker[user_id]["count"] += 1
        else:
            user_sentiment_tracker[user_id] = {"count": last.get("count", 0) + 1, "last_sentiment": sentiment}

        reply = await generate_reply(user_id, text)
        await update.message.reply_text(reply)
        logger.info(f"Voice reply to [{user_id}]: {reply}")

        os.remove(file_name)
        wav_file = file_name.replace(".ogg", ".wav")
        if os.path.exists(wav_file):
            os.remove(wav_file)

    except Exception as e:
        logger.error(f"handle_voice error: {e}")
        await update.message.reply_text("⚠️ Error processing voice message.")

# Feedback handler
async def feedback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        user_id = str(update.message.from_user.id)
        feedback_text = ' '.join(context.args)
        if feedback_text:
            redis_client.rpush("user_feedback", f"{user_id}: {feedback_text}")
            await update.message.reply_text("✅ Thank you for your feedback!")
            logger.info(f"Feedback from [{user_id}]: {feedback_text}")
        else:
            await update.message.reply_text("Please provide feedback after the command, like /feedback Your thoughts...")
    except Exception as e:
        logger.error(f"Feedback error: {e}")
        await update.message.reply_text("⚠️ Could not record feedback.")

if __name__ == "__main__":
    TELEGRAM_TOKEN = "TOKEN"

    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("feedback", feedback))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_text))
    app.add_handler(MessageHandler(filters.VOICE, handle_voice))

    print("✅ Bot with Redis memory & feedback is running...")
    app.run_polling()
