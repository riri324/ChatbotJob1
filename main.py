# uvicorn main:app --reload (to run fastapi application in terminal)
# use postman to upload mp3 file (maybe you also need to watch youtube video for this as well)

# Main Goal
# 1. Send in audio, and have it transcribed
# 2. send it to chatgpt and get a response
# 3. save the chat history to send back and forth for context

from fastapi import FastAPI, UploadFile
from dotenv import load_dotenv
import openai
import os
import json  # Added import for JSON file handling

# Load environment variables
load_dotenv()

openai.api_key = os.getenv("OPENAI_API_KEY")
openai.organization = os.getenv("OPENAI_ORG")

app = FastAPI()


@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.post("/talk")  # Transcription API
async def post_audio(file: UploadFile):
    # **Error**: Opening `file.filename` directly won't work as it's not stored on disk.
    # **Fix**: Use `await file.read()` to access uploaded file content.
    audio_content = await file.read()
    transcription = openai.Audio.transcribe(
        model="whisper-1", file=audio_content, response_format="text"
    )
    user_message = transcribe_audio(file)
    chat_response = get_chat_response(user_message)
    print(transcription)
    return {"transcription": transcription, "chat_response": chat_response}


@app.post("/translate")  # Translation API
async def post_translate(file: UploadFile):
    # **Error**: Same issue with accessing `file.filename`. Fixed below.
    audio_content = await file.read()
    translation = openai.Audio.translations.create(
        model="whisper-1", file=audio_content, response_format="text"
    )
    print(translation)
    return {"translation": translation}


@app.post("/uploadfile/")
async def create_upload_file(file: UploadFile):
    return {"filename": file.filename}


# Test OpenAI API
# **Error**: Duplicated `openai.api_key` initialization; not needed here.
try:
    models = openai.Model.list()
    print("Available Models:", models)
except Exception as e:
    print("Error:", e)

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