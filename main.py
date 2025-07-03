
# main.py (or app/main.py)
from dotenv import load_dotenv
load_dotenv()  # optional; Pydantic will load .env itself too

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings

app = FastAPI()

# CORS using our settings
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from fastapi import FastAPI, UploadFile, File, HTTPException, Form, Request
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, Any
import io
import logging
from dotenv import load_dotenv
import os




# Load environment variables
load_dotenv()

# Print to confirm the keys are loaded
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

# Set up API keys via Pydantic settings
openai.api_key      = settings.open_ai_key
openai.organization = settings.open_ai_org
elevenlabs_key      = settings.elevenlabs_key

# Check if API keys are set
if not openai.api_key:
    logger.warning("OpenAI API key not found. Set OPEN_AI_KEY in your .env file.")
if not elevenlabs_key:
    logger.warning("ElevenLabs API key not found. Set ELEVENLABS_KEY in your .env file.")

# Initialize FastAPI app
app = FastAPI()

# Configure CORS via Pydantic settings
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Define request models for type hinting and validation
class ChatRequest(BaseModel):
    text: str

# Database file path
DATABASE_FILE = 'database.json'

# Global variables to track conversation state
messages = []
interview_mode = False  # <-- NEW

# ---- LOAD/SAVE CHAT HISTORY ----
def load_messages():
    global messages
    messages = []
    if os.path.exists(DATABASE_FILE) and os.stat(DATABASE_FILE).st_size > 0:
        with open(DATABASE_FILE) as db_file:
            try:
                data = json.load(db_file)
                if isinstance(data, dict):
                    messages = data.get("messages", [])
                else:
                    logger.warning("⚠️ Unexpected JSON format. Resetting.")
                    messages = []
            except json.JSONDecodeError:
                logger.warning("⚠️ Corrupted database.json. Resetting.")
                messages = []
    return messages

def save_messages(user_message, gpt_response):
    global messages
    messages.append({"role": "user", "content": user_message})
    messages.append({"role": "assistant", "content": gpt_response})
    data = { "messages": messages }
    try:
        with open(DATABASE_FILE, 'w') as f:
            json.dump(data, f)
    except Exception as e:
        logger.error(f"Error saving messages to database: {str(e)}")

# ---- CHAT LOGIC (MODE SWITCHING) ----
def get_chat_response(user_message):
    global messages, interview_mode
    user_text = user_message['text'].strip()

    # Mode switching: /start or /end
    if user_text.lower() == "/start":
        interview_mode = True
        first_question = "Can you introduce yourself?"
        save_messages(user_message['text'], first_question)
        return first_question

    if user_text.lower() == "/end":
        interview_mode = False
        reply = "Interview ended. How else can I help you?"
        save_messages(user_message['text'], reply)
        return reply

    # Decide system prompt based on mode
    if interview_mode:
        SYSTEM_PROMPT = (
            "You are Greg, an AI technical interviewer for a software engineering job. "
            "Do not introduce yourself. Do not say 'Nice to meet you'. "
            "Start the interview immediately. Ask only one technical interview question at a time. "
            "Never say general compliments. Stay strictly in the role of an interviewer. "
            "Keep your questions short and focused. Wait for the user's answer, then continue with the next question."
        )
    else:
        SYSTEM_PROMPT = (
            "You are a helpful, friendly AI assistant. You can answer questions, help with tasks, and chat about anything."
        )

    # Build context (no system roles from history)
    filtered_messages = [m for m in messages if m["role"] != "system"]
    current_messages = [
        {"role": "system", "content": SYSTEM_PROMPT}
    ] + filtered_messages + [{"role": "user", "content": user_text}]

    try:
        client = openai.OpenAI(api_key=os.getenv("OPEN_AI_KEY"))
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=current_messages
        )
        parsed_gpt_response = response.choices[0].message.content
        save_messages(user_text, parsed_gpt_response)
        return parsed_gpt_response

    except Exception as e:
        logger.error(f"Error in OpenAI API call: {str(e)}")
        return "I'm sorry, there was an error processing your request. Please try again."

# ---- INIT ON STARTUP ----
messages = load_messages()

# ---- FASTAPI ROUTES ----
@app.get("/")
async def root():
    return {"message": "Backend server is running", "status": "ok"}

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
        global messages, interview_mode
        interview_mode = False
        messages = []
        with open(DATABASE_FILE, 'w') as f:
            json.dump({"messages": messages}, f)
        load_messages()
        return {"message": "Chat history has been cleared", "status": "success"}
    except Exception as e:
        logger.error(f"Error in clear_history: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
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
messages = load_messages()

# API Routes
@app.get("/")
async def root():
    return {"message": "Backend server is running", "status": "ok"}

@app.post("/talk")
async def post_audio(file: UploadFile = File(...)):
    try:
        if not file:
            raise HTTPException(status_code=400, detail="No file provided")
            
        # Reset file cursor position if needed
        if hasattr(file, "file") and hasattr(file.file, "seek"):
            file.file.seek(0)
            
        # Transcribe the audio
        user_message = transcribe_audio(file)
        
        if not user_message:
            raise HTTPException(status_code=500, detail="Failed to transcribe audio")
            
        # Get chat response
        chat_response = get_chat_response({"text": user_message})
        
        # Log for debugging
        logger.info(f"User message: {user_message}")
        logger.info(f"Bot response: {chat_response}")
        
        # Generate speech if ElevenLabs key is available (optional)
        audio_content = None
        if elevenlabs_key:
            audio_content = text_to_speech(chat_response)
        
        # Return the results
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
        
        # Get chat response
        chat_response = get_chat_response({"text": user_message})
        # Log for debugging
        logger.info(f"User message: {user_message}")
        logger.info(f"Bot response: {chat_response}")
        
        # Return the results
        return JSONResponse(content={"bot_response": chat_response})
    except Exception as e:
        logger.error(f"Error in post_chat_message: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/clear")
async def clear_history():
    try:
        global messages, interview_started
        
        # Reset conversation state
        interview_started = False
        
        # Reset messages to just the system prompt
        messages = [{
            "role": "system",
            "content": (
                "You are Greg, an interviewer. You are interviewing a candidate "
                "for a position that they introduced themselvse. Ask one question at a time."
                "Start with easy questions and gradually increase difficulty. "
                "Do not respond with generic messages—only ask interview questions. "
                "Keep questions short and clear."
            )
        }]
        
        # Clear the database file
        with open(DATABASE_FILE, 'w') as f:
            json.dump({"messages": messages, "interview_started": interview_started}, f)
            
        load_messages()    
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
    status = {
        "openai_api": bool(openai.api_key),
        "elevenlabs_api": bool(elevenlabs_key),
        "interview_mode": interview_mode,
        "message_count": len(messages)
    }
    return status


# Run the application
if __name__ == "_main_":
    import uvicorn
    logger.info("Starting the server...")
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
    
    