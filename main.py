from fastapi import FastAPI, UploadFile, File, HTTPException, Form, Request
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, Any
import io
import logging
from dotenv import load_dotenv
import os

load_dotenv()

print("Loaded OPEN_AI_KEY:", os.getenv("OPEN_AI_KEY"))
print("Loaded OPEN_AI_ORG:", os.getenv("OPEN_AI_ORG"))
print("Loaded ELEVENLABS_KEY:", os.getenv("ELEVENLABS_KEY"))

from dotenv import load_dotenv

import openai
import os
import json
import requests

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv(override=True)

# Set up API keys
openai.api_key = os.getenv("OPEN_AI_KEY")
openai.organization = os.getenv("OPEN_AI_ORG")
elevenlabs_key = os.getenv("ELEVENLABS_KEY")

# Check if API keys are set
if not openai.api_key:
    logger.warning("OpenAI API key not found. Set OPEN_AI_KEY in your .env file.")
if not elevenlabs_key:
    logger.warning("ElevenLabs API key not found. Set ELEVENLABS_KEY in your .env file.")

# Initialize FastAPI app
app = FastAPI()

# Configure CORS
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

class ChatRequest(BaseModel):
    text: str

DATABASE_FILE = 'database.json'
messages = []
interview_started = False

# Load conversation history at startup
def load_messages():
    messages = []
    interview_started = False

    if os.path.exists(DATABASE_FILE) and os.stat(DATABASE_FILE).st_size > 0:
        with open(DATABASE_FILE) as db_file:
            try:
                data = json.load(db_file)

                if isinstance(data, dict): 
                    messages = data.get("messages", [])
                    interview_started = data.get("interview_started", False)
                else:
                    logger.warning("⚠️ Unexpected JSON format. Resetting.")
                    messages = []
            except json.JSONDecodeError:
                logger.warning("⚠️ Corrupted database.json. Resetting.")
                messages = []

    if not messages:
        messages.append({
            "role": "system",
            "content": (
                "You are Greg, an AI technical interviewer for a software engineering job. "
                "Do not introduce yourself. Do not say 'Nice to meet you'. "
                "Start the interview immediately. Ask only one technical interview question at a time. "
                "Never say general compliments. Stay strictly in the role of an interviewer. "
                "Keep your questions short and focused. Wait for the user's answer, then continue with the next question."
            )
        })

    return messages, interview_started

# Save conversation to file
def save_messages(user_message, gpt_response, interview_started_flag=None):
    global messages, interview_started
    messages.append({"role": "user", "content": user_message})
    messages.append({"role": "assistant", "content": gpt_response})

    if interview_started_flag is not None:
        interview_started = interview_started_flag

    data = {
        "messages": messages,
        "interview_started": interview_started
    }

    try:
        with open(DATABASE_FILE, 'w') as f:
            json.dump(data, f)
    except Exception as e:
        logger.error(f"Error saving messages to database: {str(e)}")

# Transcribe audio using OpenAI's Whisper API
def transcribe_audio(file):
    try:
        temp_file_path = f"temp_{file.filename}"
        with open(temp_file_path, 'wb') as buffer:
            buffer.write(file.file.read())
        
        logger.info(f"Transcribing audio file: {file.filename}")
        
        with open(temp_file_path, "rb") as audio_file:
            client = openai.OpenAI(api_key=os.getenv("OPEN_AI_KEY"))
            transcript = client.audio.transcriptions.create(
                        model="whisper-1",
                        file=audio_file
                    )

        transcript = transcript.text
        
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)
            
        logger.info(f"Transcription successful: {transcript}")
        return transcript
    except Exception as e:
        logger.error(f"Error transcribing audio: {str(e)}")
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)
        raise e

# Get response from OpenAI
def get_chat_response(user_message):
    global messages, interview_started
    user_text = user_message['text'].strip()
    greetings = ["hello", "hi", "hey", "good morning", "good afternoon", "good evening"]
    if user_text.lower() in greetings:
        return "Hello! Write '/start' to start an interview!"

    if not interview_started:
        if user_text == "/start":
            interview_started = True
            first_question = "Can you introduce yourself?"
            save_messages(user_text, first_question, interview_started_flag=True)
            return first_question
        else:
            return "Please type '/start' to begin the interview."

    try:
        logger.info(f"Sending message to OpenAI: {user_text}")

        SYSTEM_PROMPT = (
            "You are Greg, an AI technical interviewer for a software engineering job. "
            "Do not introduce yourself. Do not say 'Nice to meet you'. "
            "Start the interview immediately. Ask only one technical interview question at a time. "
            "Never say general compliments. Stay strictly in the role of an interviewer. "
            "Keep your questions short and focused. Wait for the user's answer, then continue with the next question."
        )

        filtered_messages = [m for m in messages if m["role"] != "system"]
        current_messages = [
            { "role": "system", "content": SYSTEM_PROMPT }
        ] + filtered_messages + [{ "role": "user", "content": user_text }]


        client = openai.OpenAI(api_key=os.getenv("OPEN_AI_KEY"))
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=current_messages
        )
        parsed_gpt_response = response.choices[0].message.content
        logger.info(f"Received response from OpenAI: {parsed_gpt_response[:50]}...")

        save_messages(user_text, parsed_gpt_response)
        return parsed_gpt_response

    except Exception as e:
        logger.error(f"Error in OpenAI API call: {str(e)}")
        return "I'm sorry, there was an error processing your request. Please try again."

# Convert text to speech using ElevenLabs
def text_to_speech(text):
    if not elevenlabs_key:
        logger.warning("ElevenLabs API key not found. Skipping text-to-speech.")
        return None
        
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
        logger.info(f"Sending text to ElevenLabs TTS: {text[:50]}...")
        response = requests.post(url, json=body, headers=headers)
        
        if response.status_code == 200:
            logger.info("TTS conversion successful")
            return response.content
        else:
            logger.error(f"ElevenLabs API error: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        logger.error(f"Error in text_to_speech: {str(e)}")
        return None

# Initialize global variables
messages, interview_started = load_messages()

# API Routes
@app.get("/")
async def root():
    return {"message": "Backend server is running", "status": "ok"}

@app.post("/talk")
async def post_audio(file: UploadFile = File(...)):
    try:
        if not file:
            raise HTTPException(status_code=400, detail="No file provided")
            
        if hasattr(file, "file") and hasattr(file.file, "seek"):
            file.file.seek(0)
            
        user_message = transcribe_audio(file)
        
        if not user_message:
            raise HTTPException(status_code=500, detail="Failed to transcribe audio")
            
        chat_response = get_chat_response({"text": user_message})
        
        logger.info(f"User message: {user_message}")
        logger.info(f"Bot response: {chat_response}")
        
        audio_content = None
        if elevenlabs_key:
            audio_content = text_to_speech(chat_response)
        
        response_data = {
            "transcription": user_message, 
            "bot_response": chat_response,
            "has_audio": audio_content is not None
        }
        
        return JSONResponse(content=response_data)
    except Exception as e:
        logger.error(f"Error in post_audio: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/chat")
async def post_chat_message(request: ChatRequest):
    try:
        user_message = request.text
        if not user_message:
            raise HTTPException(status_code=400, detail="No text provided")
        
        chat_response = get_chat_response({"text": user_message})
        logger.info(f"User message: {user_message}")
        logger.info(f"Bot response: {chat_response}")
        
        return JSONResponse(content={"bot_response": chat_response})
    except Exception as e:
        logger.error(f"Error in post_chat_message: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/clear")
async def clear_history():
    try:
        global messages, interview_started
        
        interview_started = False
        
        messages = [{
            "role": "system",
            "content": (
                "You are Greg, an AI interviewer. You are interviewing a candidate "
                "for a software developer position. Ask one question at a time."
                "Start with easy questions and gradually increase difficulty. "
                "Do not respond with generic messages—only ask interview questions. "
                "Keep questions short and clear."
            )
        }]
        
        with open(DATABASE_FILE, 'w') as f:
            json.dump({"messages": messages, "interview_started": interview_started}, f)
            
        return {"message": "Chat history has been cleared", "status": "success"}
    except Exception as e:
        logger.error(f"Error in clear_history: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/audio/{text}")
async def get_audio(text: str):
    try:
        if not elevenlabs_key:
            raise HTTPException(status_code=501, detail="Text-to-speech functionality not available")
            
        audio_content = text_to_speech(text)
        
        if not audio_content:
            raise HTTPException(status_code=500, detail="Failed to generate audio")
            
        return StreamingResponse(
            io.BytesIO(audio_content),
            media_type="audio/mpeg"
        )
    except Exception as e:
        logger.error(f"Error in get_audio: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/status")
async def get_status():
    """Check if all required API keys are available"""
    status = {
        "openai_api": bool(openai.api_key),
        "elevenlabs_api": bool(elevenlabs_key),
        "interview_started": interview_started,
        "message_count": len(messages)
    }
    return status

# Run the application
if __name__ == "_main_":
    import uvicorn
    logger.info("Starting the server...")
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
    
    