#uvicorn main:app --reload (to run fastapi application in terminal)
#use postman to upload mp3 file(maybe you also need to watch youtube video for this as well)

# Main Goal
# 1. Send in audio, and have it transcribed
# 2. send it to chatgpt and get a response
# 3. save the chat history to send back and forth for context

from fastapi import FastAPI, UploadFile
from dotenv import load_dotenv

import openai
import os

load_dotenv()


openai.api_key = os.getenv("OPEN_AI_KEY")
openai.organization = os.getenv("OPEN_AI_ORG")


app = FastAPI()


@app.get("/")
async def root():
    return {"message": "Hello World"}

@app.post("/talk") ## transcription api (takes input the audio file  and the desired output file format for the transcription)
async def post_audio(file: UploadFile):
    audio_file= open(file.filename, "rb")
    transcription = openai.audio.transcriptions.create(model="whisper-1", file=audio_file, response_format="text")
    print(transcription)


@app.post("/translate")  ## Translation api (takes as input the audio file in any of the supported languages and transcribes)
##the example file "Kaudiotest.mp3" was in Korean so it translates to english.
async def post_translate(file: UploadFile):
    audio_file= open(file.filename, "rb") ## now I inputted audio as german
    translation = openai.audio.translations.create(model="whisper-1", file=audio_file, response_format="text")
    print(translation)

@app.post("/uploadfile/")
async def create_upload_file(file: UploadFile):
    return {"filename": file.filename}


## Everything works perfectly fine till here, 
## I did it till MAIN GOAL 1