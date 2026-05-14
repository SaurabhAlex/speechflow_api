# SpeechFlow API

SpeechFlow API is a FastAPI backend service that provides authentication, text-to-speech conversion, speech-to-text processing, and protected API endpoints for voice-enabled applications.

## Features

- JWT Authentication
- Protected User Profile API
- Text-to-Speech using gTTS
- Speech-to-Text using SpeechRecognition
- File Upload Support
- Paginated Dummy User Records

## Tech Stack

- FastAPI
- Python
- JWT Authentication
- gTTS
- SpeechRecognition
- Uvicorn

## Setup

git clone <repo-url>
cd speechflow_api

python -m venv venv
source venv/bin/activate

pip install -r requirements.txt

uvicorn main:app --reload
