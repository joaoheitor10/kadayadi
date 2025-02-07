from dotenv import load_dotenv
import os
import discord
import requests
import openai
from googletrans import Translator
import nacl
import wave
import io
from discord.ext import commands
from gtts import gTTS
import asyncio  # Import asyncio

load_dotenv()

# Load API keys from environment variables
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
PERSPECTIVE_API_KEY = os.getenv("PERSPECTIVE_API_KEY")

# Set up OpenAI API Key
openai.api_key = OPENAI_API_KEY

# Initialize the bot
intents = discord.Intents.default()
intents.messages = True
intents.voice_states = True
client = commands.Bot(command_prefix="!", intents=intents)

# Initialize Translator (for translation from Malayalam to English)
translator = Translator()

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

# Function to transcribe audio using OpenAI Whisper
def transcribe_audio(audio_bytes):
    try:
        audio = openai.Audio.transcribe(
            model="whisper-1",
            file=audio_bytes,
            language="ml"  # Transcribe Malayalam speech
        )
        return audio["text"]
    except Exception as e:
        print(f"Error with transcription: {e}")
        return None

# Function to translate Malayalam to English
def translate_to_english(text):
    translated_text = translator.translate(text, src="ml", dest="en")
    return translated_text.text

# Function to generate voice alert (for toxicity warning)
def generate_voice_alert(player_name):
    message = f"{player_name}, calm down! No toxicity allowed!"
    tts = gTTS(text=message, lang="en")
    tts.save("warning.mp3")
    return discord.FFmpegPCMAudio("warning.mp3")

# Event when bot joins a voice channel
@client.event
async def on_voice_state_update(member, before, after):
    if after.channel:  # When user joins a voice channel
        print(f"{member.name} joined {after.channel.name}")
        if member != client.user:  # Prevent the bot from connecting to a channel it is already in
            await after.channel.connect()

# Function to capture audio from voice channel (simplified version for example)
async def capture_audio(vc):
    while True:
        # Capture raw audio data from the voice channel
        audio_data = await vc.recv()  # This is where you need to handle actual audio input

        if audio_data:
            with io.BytesIO(audio_data):
                # Send to transcription service (Malayalam speech transcription)
                transcribed_text = transcribe_audio(audio_data)
        
            if transcribed_text:
                print(f"Transcribed (Malayalam): {transcribed_text}")
                
                # Translate from Malayalam to English
                translated_text = translate_to_english(transcribed_text)
                print(f"Translated (English): {translated_text}")
                
                # Check toxicity
                toxicity = analyse_toxicity(translated_text)
                if toxicity and toxicity > 0.75:
                    print(f"Toxic behavior detected!")
                    # Send toxicity warning or TTS message here
                    await vc.channel.send(f"🚨 {vc.channel.guild.owner} is being toxic!")
                    voice_alert = generate_voice_alert(vc.channel.guild.owner)
                    vc.play(voice_alert)
        
        await asyncio.sleep(1)

# Run the bot using the hardcoded token
client.run(DISCORD_TOKEN)
