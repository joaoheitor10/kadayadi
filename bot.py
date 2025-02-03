import discord
import requests
import openai
from googletrans import Translator
import speech_recognition as sr
from gtts import gTTS
import os

# Discord Bot Token
DISCORD_TOKEN = "MTMzNjAzMDM3ODU4MTgyMzU0MA.GvkV5n.uVyBQ2CqvWYsxRt3znerFmdrur62_Ut9wooEDk"

# OpenAI API Key (for Whisper AI)
OPENAI_API_KEY = "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"

# Google Perspective API Key
PERSPECTIVE_API_KEY = "AIzaSyAGOFZpzh6oY-MR8n1m6eF4SANvUvY7HrE"

# Initialize translator
translator = Translator()

# Discord bot setup
intents = discord.Intents.default()
intents.messages = True
intents.voice_states = True
intents.guilds = True
client = discord.Client(intents=intents)

# Function to analyse toxicity using Perspective API
def analyse_toxicity(text):
    url = f"https://commentanalyzer.googleapis.com/v1alpha1/comments:analyze?key={PERSPECTIVE_API_KEY}"
    headers = {"Content-Type": "application/json"}
    data = {
        "comment": {"text": text},
        "languages": ["en"],
        "requestedAttributes": {"TOXICITY": {}}
    }
    
    response = requests.post(url, headers=headers, json=data)
    if response.status_code == 200:
        result = response.json()
        toxicity_score = result["attributeScores"]["TOXICITY"]["summaryScore"]["value"]
        return toxicity_score
    else:
        return None

# Function to transcribe Malayalam speech using Whisper AI
def transcribe_audio(audio):
    recogniser = sr.Recognizer()
    try:
        text = recogniser.recognize_whisper(audio, language="ml")  # Whisper AI for Malayalam
        return text
    except sr.UnknownValueError:
        return None
    except sr.RequestError:
        return None

# Function to translate Malayalam to English
def translate_to_english(text):
    translated_text = translator.translate(text, src="ml", dest="en")
    return translated_text.text

# Function to generate voice alert using TTS
def generate_voice_alert(player_name):
    message = f"{player_name}, calm down! No toxicity allowed!"
    tts = gTTS(text=message, lang="en")
    filename = "warning.mp3"
    tts.save(filename)
    return filename

# Event when bot starts
@client.event
async def on_ready():
    print(f"✅ Logged in as {client.user}")

# Event when a user joins a voice channel
@client.event
async def on_voice_state_update(member, before, after):
    if after.channel is not None:  # If user joins a channel
        print(f"🎤 {member.name} joined voice channel {after.channel.name}")
        await monitor_voice_channel(after.channel, member)

# Function to monitor Discord voice chat
async def monitor_voice_channel(channel, player):
    recogniser = sr.Recognizer()
    with sr.Microphone() as source:
        print("🎤 Listening in Discord voice chat...")
        while True:
            try:
                audio = recogniser.listen(source, timeout=5)
                text = transcribe_audio(audio)

                if text:
                    print(f"📝 {player.name} said (Malayalam): {text}")

                    # Translate to English
                    translated_text = translate_to_english(text)
                    print(f"🔄 Translated: {translated_text}")

                    # Analyse toxicity
                    toxicity_score = analyse_toxicity(translated_text)
                    if toxicity_score is not None and toxicity_score > 0.75:
                        print(f"🚨 {player.name} is being toxic!")

                        # Generate and play TTS voice warning
                        warning_file = generate_voice_alert(player.name)
                        voice_channel = channel.guild.voice_client

                        if voice_channel:  # If bot is already connected to a voice channel
                            voice_channel.play(discord.FFmpegPCMAudio(warning_file))
                        else:
                            # Connect to the channel and play the audio
                            vc = await channel.connect()
                            vc.play(discord.FFmpegPCMAudio(warning_file))

            except Exception as e:
                print(f"❌ Error: {e}")
                break  # Stop listening if there's an issue

# Run the bot
client.run(DISCORD_TOKEN)

