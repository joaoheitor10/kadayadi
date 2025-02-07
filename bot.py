import os  # Ensure this is at the top
import discord
import requests
import openai
from googletrans import Translator
import nacl
import wave
import io
from discord.ext import commands
from gtts import gTTS

# Your API keys (hardcoded for this example)
DISCORD_TOKEN = "MTMzNjAzMDM3ODU4MTgyMzU0MA.GvkV5n.uVyBQ2CqvWYsxRt3znerFmdrur62_Ut9wooEDk"
OPENAI_API_KEY = "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"
PERSPECTIVE_API_KEY = "AIzaSyAGOFZpzh6oY-MR8n1m6eF4SANvUvY7HrE"

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
        await after.channel.connect()

# Event to capture audio from voice channel (this is simplified for this example)
@client.event
async def on_voice_server_update(self, data):
    print("Capturing voice data...")

# Function to capture audio (simplified version for example)
async def capture_audio(vc):
    while True:
        # Capture raw audio data from the voice channel
        audio_data = await vc.recv()  # Receiving voice data

        # Assuming audio_data is in a WAV format or raw byte data
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
