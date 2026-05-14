from fastapi import FastAPI, Depends, HTTPException, UploadFile, File
from fastapi.responses import StreamingResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from gtts import gTTS
import speech_recognition as sr
from pydub import AudioSegment
from io import BytesIO
import json
import jwt
import os
import tempfile
from pathlib import Path

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
security = HTTPBearer()
SECRET_KEY = "your-secret-key"

class LoginRequest(BaseModel):
    username: str
    password: str

FIXED_USERNAME = "test"
FIXED_PASSWORD = "123"

class TTSRequest(BaseModel):
    text: str
    lang: str = "en"

recognizer = sr.Recognizer()

SUPPORTED_AUDIO_TYPES = {
    "audio/wav",
    "audio/x-wav",
    "audio/flac",
    "audio/x-flac",
    "audio/mpeg",
    "audio/mp3",
}

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        jwt.decode(credentials.credentials, SECRET_KEY, algorithms=["HS256"])
    except:
        raise HTTPException(status_code=401, detail="Invalid token")
    return credentials.credentials

# 🟢 Public API (login)
@app.post("/login")
def login(data: LoginRequest):
    if data.username != FIXED_USERNAME or data.password != FIXED_PASSWORD:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = jwt.encode({"user": data.username}, SECRET_KEY, algorithm="HS256")
    return {"access_token": token, "token_type": "bearer"}

# Simple text-to-speech API
@app.post("/tts")
def text_to_speech(data: TTSRequest):
    try:
        mp3_fp = BytesIO()
        tts = gTTS(text=data.text, lang=data.lang)
        tts.write_to_fp(mp3_fp)
        mp3_fp.seek(0)
        return StreamingResponse(
            mp3_fp,
            media_type="audio/mpeg",
            headers={"Content-Disposition": "attachment; filename=tts.mp3"},
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# Simple speech-to-text API
@app.post("/stt")
async def speech_to_text(file: UploadFile = File(...)):
    if file.content_type not in SUPPORTED_AUDIO_TYPES:
        raise HTTPException(status_code=400, detail="Unsupported audio file type")

    tmp_file_path = None
    converted_wav_path = None
    try:
        audio_bytes = await file.read()
        suffix = Path(file.filename).suffix.lower() or ".wav"
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            tmp.write(audio_bytes)
            tmp_file_path = tmp.name

        if suffix in {".mp3", ".mpeg", ".m4a", ".aac"} or file.content_type in {"audio/mpeg", "audio/mp3", "audio/x-mp3"}:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as converted:
                converted_wav_path = converted.name
            AudioSegment.from_file(tmp_file_path).export(converted_wav_path, format="wav")
            audio_path = converted_wav_path
        else:
            audio_path = tmp_file_path

        with sr.AudioFile(audio_path) as source:
            audio = recognizer.record(source)

        transcription = recognizer.recognize_google(audio)
        return {"text": transcription}
    except sr.UnknownValueError:
        raise HTTPException(status_code=400, detail="Could not understand audio")
    except sr.RequestError as e:
        raise HTTPException(status_code=502, detail=f"Speech recognition service error: {e}")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        for path in (tmp_file_path, converted_wav_path):
            if path and os.path.exists(path):
                os.unlink(path)

# Protected API
@app.get("/profile")
def get_profile(token: str = Depends(verify_token)):
    return {"message": "Welcome user!"}

# 📄 Read dummy user record from text file
@app.get("/user")
def get_user(token: str = Depends(verify_token), page: int = 1, limit: int = 10):
    with open("user_record.txt", "r") as f:
        users = json.load(f)
    start = (page - 1) * limit
    end = start + limit
    paginated_users = users[start:end]
    total = len(users)
    total_pages = (total + limit - 1) // limit
    return {
        "data": paginated_users,
        "page": page,
        "limit": limit,
        "total": total,
        "total_pages": total_pages
    }
