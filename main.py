# uvicorn main:app --reload (to run fastapi application in terminal)
# use postman to upload mp3 file (maybe you also need to watch youtube video for this as well)

# Main Goal
# 1. Send in audio, and have it transcribed
# 2. send it to chatgpt and get a response
# 3. save the chat history to send back and forth for context

from fastapi import FastAPI, UploadFile, HTTPException
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import openai
import os
import json
import uuid
import aiofiles # type: ignore
import httpx

# Load environment variables
load_dotenv(override=True)

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

import traceback

@app.post("/talk")
async def post_audio(file: UploadFile):
    try:
        # Transcribe the audio file
        user_message = await transcribe_audio(file)
        # Get the chat response from GPT
        chat_response = await get_chat_response(user_message)

        return {"transcription": user_message.get("text", ""), "bot_response": chat_response}

    except Exception as e:
        # Print the full traceback to the terminal
        traceback.print_exc()
        # Return the error in the response for easier debugging (only for development)
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

@app.get("/clear")
async def clear_history():
    """
    Clears the chat history stored in `database.json`.
    """
    try:
        async with aiofiles.open("database.json", "w") as db_file:
            await db_file.write("")
        return {"message": "Chat history has been cleared"}
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to clear chat history.")

# Functions
async def transcribe_audio(file: UploadFile):
    """
    Transcribes the uploaded audio file using OpenAI Whisper.
    """
    temp_filename = f"temp_{uuid.uuid4().hex}.mp3"
    try:
        # Save file asynchronously
        async with aiofiles.open(temp_filename, "wb") as out_file:
            content = await file.read()
            await out_file.write(content)

        # Call OpenAI Whisper API
        with open(temp_filename, "rb") as audio_file:
            response = openai.Audio.transcribe("whisper-1", file=audio_file)
        return response

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error transcribing audio: {str(e)}")

    finally:
        # Clean up temporary file
        if os.path.exists(temp_filename):
            os.remove(temp_filename)

async def get_chat_response(user_message):
    """
    Sends the user message to OpenAI ChatGPT and returns the response.
    """
    try:
        messages = await load_messages()
        messages.append({"role": "user", "content": user_message.get("text", "")})

        # Call OpenAI ChatGPT
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=messages
        )
        chat_content = response["choices"][0]["message"]["content"]

        # Save messages
        await save_messages(user_message.get("text", ""), chat_content)

        return chat_content
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting chat response: {str(e)}")

async def load_messages():
    """
    Loads the chat history from `database.json`.
    Initializes the file if it doesn't exist.
    """
    if not os.path.exists("database.json"):
        initial_data = [{"role": "system", "content": "You are Greg, a humorous React interviewer."}]
        async with aiofiles.open("database.json", "w") as db_file:
            await db_file.write(json.dumps(initial_data))
        return initial_data

    try:
        async with aiofiles.open("database.json", "r") as db_file:
            content = await db_file.read()
            return json.loads(content) if content else []
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error loading messages: {str(e)}")

async def save_messages(user_message, bot_response):
    """
    Saves user and bot messages to `database.json`.
    """
    try:
        messages = await load_messages()
        messages.append({"role": "user", "content": user_message})
        messages.append({"role": "assistant", "content": bot_response})

        async with aiofiles.open("database.json", "w") as db_file:
            await db_file.write(json.dumps(messages))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error saving messages: {str(e)}")

async def text_to_speech(text):
    """
    Converts text to speech using ElevenLabs API.
    """
    url = f"https://api.elevenlabs.io/v1/text-to-speech/pNInz6obpgDQGcFmaJgB"
    headers = {
        "Content-Type": "application/json",
        "accept": "audio/mpeg",
        "xi-api-key": elevenlabs_key
    }
    payload = {
        "text": text,
        "model_id": "eleven_monolingual_v1",
        "voice_settings": {
            "stability": 0,
            "similarity_boost": 0,
            "style": 0.5,
            "use_speaker_boost": True
        }
    }
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(url, headers=headers, json=payload)
            if response.status_code == 200:
                return StreamingResponse(response.content, media_type="audio/mpeg")
            else:
                raise HTTPException(status_code=response.status_code, detail="Failed to convert text to speech.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error in text-to-speech: {str(e)}")



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



# uvicorn main:app --reload
# npm start  (command to run FrontEnd)
# you need a two terminal, first terminal to run backend and second one to run FrontEnd