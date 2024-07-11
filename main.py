import json
import os

import requests
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from openai import OpenAI
from openai.types.audio import Transcription
from openai.types.chat import ChatCompletion

load_dotenv()

client = OpenAI(organization=os.getenv("OPEN_AI_ORG"),
                api_key=os.getenv("OPEN_AI_KEY"))
elevenlabs_key = os.getenv("ELEVENLABS_KEY")

app = FastAPI()

origins = [
    "http://localhost:5174",
    "http://localhost:5173",
    "http://localhost:8000",
    "http://localhost:8001",
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
    return {"message": "Hello ChatGPT!"}


@app.post("/talk")
async def post_audio(file: UploadFile):
    user_message = transcribe_audio(file)
    chat_response = get_chat_response(user_message)
    audio_output = text_to_speech(chat_response)

    def iterfile():
        yield audio_output

    return StreamingResponse(iterfile(), media_type="audio/mpeg")


def transcribe_audio(file: UploadFile) -> Transcription:
    filename = file.filename

    if filename is None:
        raise HTTPException(status_code=400, detail="No file uploaded")

    audio_file = open(filename, 'rb')
    transcription = client.audio.transcriptions.create(
        model="whisper-1",
        file=audio_file
    )

    return transcription


# def get_chat_response(user_message: dict[str, str]):
def get_chat_response(user_message: Transcription) -> str:
    messages = load_messages()
    messages.append({"role": "user", "content": user_message.text})

    # Send to ChatGpt/OpenAi
    gpt_response: ChatCompletion = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=messages
    )

    parsed_gpt_response = gpt_response.choices[0].message.content or 'No response'

    # Save messages
    save_messages(user_message.text, parsed_gpt_response)

    return parsed_gpt_response


# def load_messages() -> list[dict[str, str]]:
def load_messages():
    # messages: list[dict[str, str]] = []
    messages = []
    file = 'database.json'

    empty = os.stat(file).st_size == 0

    if not empty:
        with open(file) as db_file:
            data: list[dict[str, str]] = json.load(db_file)
            for item in data:
                messages.append(item)
    else:
        messages.append(
            {"role": "system", "content": "You are interviewing the user for a front-end React developer position. Ask short questions that are relevant to a junior level developer. Your name is Sherlock. The user is Nikouz. Keep responses under 30 words and be funny sometimes."}
        )
    return messages


def save_messages(user_message: str, gpt_response: str):
    file = 'database.json'
    messages = load_messages()
    messages.append({"role": "user", "content": user_message})
    messages.append({"role": "assistant", "content": gpt_response})
    with open(file, 'w') as f:
        json.dump(messages, f)


def text_to_speech(text: str) -> bytes | None:
    voice_id = 'oDNl0oYmPNBE23Z3VlWf'

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
        "Accept": "audio/mpeg",
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
