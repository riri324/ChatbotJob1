from dotenv import load_dotenv
load_dotenv()

import os, json, io, logging, requests
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# --- CONFIG ---
from app.core.config import settings

openai_api_key      = settings.open_ai_key
openai_org          = settings.open_ai_org
elevenlabs_key      = settings.elevenlabs_key

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DATABASE_FILE = 'database.json'
messages = []
interview_mode = False

class ChatRequest(BaseModel):
    text: str

# ---- LOAD/SAVE ----
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
                    messages = []
            except json.JSONDecodeError:
                messages = []
    return messages

def save_messages(user_message, gpt_response):
    global messages
    messages.append({"role": "user", "content": user_message})
    messages.append({"role": "assistant", "content": gpt_response})
    with open(DATABASE_FILE, 'w') as f:
        json.dump({ "messages": messages }, f)

# ---- CHAT LOGIC ----
def get_chat_response(user_message):
    global messages, interview_mode
    user_text = user_message['text'].strip()

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

    filtered_messages = [m for m in messages if m["role"] != "system"]
    current_messages = [
        {"role": "system", "content": SYSTEM_PROMPT}
    ] + filtered_messages + [{"role": "user", "content": user_text}]

    try:
        import openai
        client = openai.OpenAI(api_key=openai_api_key)
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

def transcribe_audio(file):
    import openai
    temp_file_path = f"temp_{file.filename}"
    try:
        with open(temp_file_path, 'wb') as buffer:
            buffer.write(file.file.read())
        with open(temp_file_path, "rb") as audio_file:
            client = openai.OpenAI(api_key=openai_api_key)
            transcript = client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file
            )
        transcript_text = transcript.text
        return transcript_text
    except Exception as e:
        raise RuntimeError(f"Audio transcription failed: {e}")
    finally:
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)

def text_to_speech(text):
    if not elevenlabs_key:
        logger.warning("ElevenLabs API key not found. Skipping text-to-speech.")
        return None
    voice_id = 'pNInz6obpgDQGcFmaJgB'
    body = {...}  # (same as before)
    headers = {...}
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
    try:
        logger.info(f"Sending text to ElevenLabs TTS: {text[:50]}...")
        response = requests.post(url, json=body, headers=headers, timeout=15)
        if response.status_code == 200:
            logger.info("TTS conversion successful")
            return response.content
        else:
            logger.error(f"ElevenLabs API error: {response.status_code} - {response.text}")
            return None
    except requests.exceptions.Timeout:
        logger.error("TTS request timed out.")
        return None
    except Exception as e:
        logger.error(f"Error in text_to_speech: {str(e)}")
        return None


# ---- API ROUTES ----
@app.get("/")
async def root():
    return {"message": "Backend server is running", "status": "ok"}

@app.post("/chat")
async def post_chat_message(request: ChatRequest):
    user_message = request.text
    if not user_message:
        raise HTTPException(status_code=400, detail="No text provided")
    chat_response = get_chat_response({"text": user_message})
    return JSONResponse(content={"bot_response": chat_response})

@app.post("/talk")
async def post_audio(file: UploadFile = File(...)):
    if not file:
        raise HTTPException(status_code=400, detail="No file provided")
    file.file.seek(0)
    user_message = transcribe_audio(file)
    if not user_message:
        raise HTTPException(status_code=500, detail="Failed to transcribe audio")
    chat_response = get_chat_response({"text": user_message})
    audio_content = text_to_speech(chat_response)
    response_data = {
        "transcription": user_message,
        "bot_response": chat_response,
        "has_audio": audio_content is not None
    }
    return JSONResponse(content=response_data)

@app.get("/clear")
async def clear_history():
    global messages, interview_mode
    interview_mode = False
    messages = []
    with open(DATABASE_FILE, 'w') as f:
        json.dump({"messages": messages}, f)
    load_messages()
    return {"message": "Chat history has been cleared", "status": "success"}

@app.get("/audio/{text}")
async def get_audio(text: str):
    if not elevenlabs_key:
        raise HTTPException(status_code=501, detail="Text-to-speech functionality not available")
    audio_content = text_to_speech(text)
    if not audio_content:
        raise HTTPException(status_code=500, detail="Failed to generate audio")
    return StreamingResponse(
        io.BytesIO(audio_content),
        media_type="audio/mpeg"
    )

@app.get("/status")
async def get_status():
    return {
        "openai_api": bool(openai_api_key),
        "elevenlabs_api": bool(elevenlabs_key),
        "interview_mode": interview_mode,
        "message_count": len(messages)
    }

# ---- MAIN ----
if __name__ == "__main__":
    import uvicorn
    logger.info("Starting the server...")
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)

# ---- Load messages ON startup
messages = load_messages()
