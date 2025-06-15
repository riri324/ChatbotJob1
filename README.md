# VoiceGPT Interview Assistant

A voice-based AI interview chatbot built using **FastAPI** (backend) and **React** (frontend). Speak or upload audio, get transcribed responses powered by **OpenAI** and optionally converted to voice using **ElevenLabs**.

---

## Features

- Upload or record your voice
- Transcription using OpenAI's Whisper API
- ChatGPT (GPT-3.5) answers in context
- Chat history maintained throughout the session
- Optional Text-to-Speech with ElevenLabs
- Clear chat history at any time

---

## 📁 Project Structure

```bash
ChatbotJob/
├── main.py               # FastAPI backend
├── database.json         # Chat history
├── .env                  # API keys (not committed)
├── client/               # React frontend
│   ├── App.js
│   ├── AudioUpload.js
│   └── ...
└── README.md
```
---

# Setup Instructions

## 1. Clone the Repository

```bash
git clone https://github.com/yourusername/ChatbotJob.git
cd ChatbotJob
```

## 2. Backend Setup (FastAPI)

```bash
# Create a virtual environment
python -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Or manually
pip install fastapi uvicorn python-dotenv openai requests
```

## 3. Environment Variables

Create a .env file in the root folder:
```bash
OPEN_AI_KEY=your_openai_api_key
OPEN_AI_ORG=your_openai_org_id
ELEVENLABS_KEY=your_elevenlabs_api_key  # Optional for TTS
```
## 4. Frontend Setup (React)

```bash
cd client
npm install
npm start
```
---

# Running the App

In two terminals:
## 1. Backend (FastAPI):

```bash
uvicorn main:app --reload
```

## 2. Frontend (React)

```bash
cd client
npm start
```
---

# Usage

- Upload an audio file or record using the microphone.
- Click /start to begin an AI-driven technical interview.
- Interact with the bot using text or speech.
- Use /clear endpoint to reset the interview.
- All conversations are stored in database.json.

---

<img width="985" alt="Screenshot 2025-06-16 at 1 26 32 AM" src="https://github.com/user-attachments/assets/f8ec023e-505c-4fb6-b7fa-f0b374dc01f4" />

<img width="981" alt="Screenshot 2025-06-16 at 1 44 55 AM" src="https://github.com/user-attachments/assets/42384fc9-9f75-409e-9cc0-1995a57936ea" />

---

## 🛠️ Dependencies

- FastAPI
- OpenAI API
- Whisper API
- ElevenLabs TTS
- React
- Uvicorn

---

## 📄 License

This project is licensed under the MIT License.  
See [LICENSE](./LICENSE) for details.

