# uvicorn main:app --reload (to run fastapi application in terminal)
# use postman to upload mp3 file (maybe you also need to watch youtube video for this as well)

# Main Goal
# 1. Send in audio, and have it transcribed
# 2. send it to chatgpt and get a response
# 3. save the chat history to send back and forth for context

from fastapi import FastAPI, UploadFile
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware

from dotenv import load_dotenv

import openai
import os
import json
import requests

load_dotenv()

openai.api_key = os.getenv("OPEN_AI_KEY")
openai.organization = os.getenv("OPEN_AI_ORG")
elevenlabs_key = os.getenv("ELEVENLABS_KEY")

app = FastAPI()

origins = [
    "http://localhost:5174",
    "http://localhost:5173",
    "http://localhost:8000",
    "http://localhost:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "Hello World"}

@app.post("/talk")
async def post_audio(file: UploadFile):
    user_message = transcribe_audio(file)
    chat_response = get_chat_response(user_message)
    audio_output = text_to_speech(chat_response)

    def iterfile():
        yield audio_output

    return StreamingResponse(iterfile(), media_type="application/octet-stream")

@app.get("/clear")
async def clear_history():
    file = 'database.json'
    open(file, 'w')
    return {"message": "Chat history has been cleared"}

# Functions
def transcribe_audio(file):
    # Save the blob first
    with open(file.filename, 'wb') as buffer:
        buffer.write(file.file.read())
    audio_file = open(file.filename, "rb")
    transcript = openai.Audio.transcribe("whisper-1", audio_file)
    print(transcript)
    return transcript

def get_chat_response(user_message):
    messages = load_messages()
    messages.append({"role": "user", "content": user_message['text']})

    # Send to ChatGpt/OpenAi
    gpt_response = gpt_response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=messages
        )

    parsed_gpt_response = gpt_response['choices'][0]['message']['content']

    # Save messages
    save_messages(user_message['text'], parsed_gpt_response)

    return parsed_gpt_response

def load_messages():
    messages = []
    file = 'database.json'

    empty = os.stat(file).st_size == 0

    if not empty:
        with open(file) as db_file:
            data = json.load(db_file)
            for item in data:
                messages.append(item)
    else:
        messages.append(
            {"role": "system", "content": "You are interviewing the user for a front-end React developer position. Ask short questions that are relevant to a junior level developer. Your name is Greg. The user is Travis. Keep responses under 30 words and be funny sometimes."}
        )
    return messages

def save_messages(user_message, gpt_response):
    file = 'database.json'
    messages = load_messages()
    messages.append({"role": "user", "content": user_message})
    messages.append({"role": "assistant", "content": gpt_response})
    with open(file, 'w') as f:
        json.dump(messages, f)

def text_to_speech(text):
    voice_id = 'pNInz6obpgDQGcFmaJgB'
    
    body = {
        "text": text,
        "model_id": "eleven_monolingual_v1",
        "voice_settings": {
            "stability": 0,
            "similarity_boost": 0,
            "style": 0.5,
            "use_speaker_boost": True
        }
    }

    headers = {
        "Content-Type": "application/json",
        "accept": "audio/mpeg",
        "xi-api-key": elevenlabs_key
    }

    url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"

    try:
        response = requests.post(url, json=body, headers=headers)
        if response.status_code == 200:
            return response.content
        else:
            print('something went wrong')
    except Exception as e:
        print(e)


#1. Send in audio, and have it transcribed
#2. We want to send it to chatgpt and get a response
#3. We want to save the chat history to send back and forth for context.



# Yousef Notes : I did everything you did and fixed some things you didn’t do from the video, and I also just checked the Postman, and it didn’t work again. :{

# Notes:
# 1. Make sure `.env` file is properly configured with OpenAI and ElevenLabs API keys. Use `.env_sample` as a reference if needed.(but i did this just make sure you connect it properly) .
# 2. If Postman is not working, double-check:
#    - The endpoint URL (http://localhost:8000/talk). (you need to watch the video to understand this) 
# 3. Test the `/clear` endpoint after interacting with the app to verify that the chat history is cleared properly.
# 4. Make sure to install all necessary dependencies (`pip install fastapi uvicorn python-dotenv openai requests`).
# 5. If ElevenLabs TTS fails, verify that the `voice_id` matches a valid voice in your ElevenLabs account.

