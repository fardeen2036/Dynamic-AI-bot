A powerful Telegram bot built with Python that uses Google's Gemini API to generate intelligent responses. It supports voice input, sentiment detection, short-term memory using Redis, and user feedback logging. Ideal for smart, emotionally aware conversations!

🚀 Features
🧠 Gemini 1.5 Pro / Flash AI response generation

🎤 Voice message to text (using SpeechRecognition + FFmpeg + pydub)

💬 Text message handling

😄 Sentiment detection (positive, negative, neutral with emotional responses)

🧠 Redis-based short-term memory for user context

📝 Feedback collection (type: feedback:<your message>)

🛠️ Robust logging and error handling

👤 Creator credit handling (e.g., "Who created you?")

📦 Tech Stack
Python 3.10+

python-telegram-bot

google-generativeai

textblob

redis

speechrecognition, pydub, ffmpeg

httpx, logging

📌 Commands
/start – Start the bot

Send text or voice message – Get Gemini-powered replies

Send feedback:<your message> – Log your feedback

⚙️ Requirements
Python packages from requirements.txt

Redis server running locally or on cloud

FFmpeg installed and properly configured

🌐 Deployment
Can be deployed to Render, Railway, Heroku, VPS, or Dockerized for production use.

👨‍💻 Creator
Made with 💙 by Fardeen
