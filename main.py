import json
import os
import shutil

import requests
from dotenv import load_dotenv
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from openai import OpenAI
from openai.types.audio import Transcription
from openai.types.chat import ChatCompletion

load_dotenv()

client = OpenAI(organization=os.getenv("OPEN_AI_ORG"),
                api_key=os.getenv("OPEN_AI_KEY"))
elevenlabs_key = os.getenv("ELEVENLABS_KEY")

app = FastAPI()
app.mount("/static/browser",
          StaticFiles(directory="static/browser"), name="static")

origins = [
    # "http://localhost:5174",
    # "http://localhost:5173",
    # "http://localhost:8000",
    # "http://localhost:8001",
    "https://chatgpt-interviewer-bot-backend.onrender.com",
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
    return FileResponse("static/browser/index.html")


@app.post("/talk")
async def post_audio(file: UploadFile = File(...)):
    path = f"{file.filename}"
    with open(path, 'w+b') as f:
        shutil.copyfileobj(file.file, f)

    user_message = transcribe_audio(file)

    # Delete the file
    os.remove(path)

    chat_response = get_chat_response(user_message)
    print(chat_response)
    audio_output = text_to_speech(chat_response)

    def iterfile():
        yield audio_output

    return StreamingResponse(iterfile(), media_type="audio/mpeg")


@app.get("/reset")
async def reset():
    delete_messages()
    return {"message": "Chat history successfully reset."}


def transcribe_audio(file: UploadFile) -> Transcription:
    filename = file.filename
    print(file.filename)

    if filename is None:
        raise HTTPException(status_code=400, detail="No file uploaded")

    audio_file = open(filename, 'rb')
    transcription = client.audio.transcriptions.create(
        model="whisper-1",
        file=audio_file,
        language="en"
        # language="fr"
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


def load_messages():
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
            # {"role": "system", "content": "You're my best friend. Your name is Sherlock. The user is Nikouz. Answers must be no longer than 30 words and must be funny sometimes."}
            # {"role": "system", "content": "Vous êtes mon meilleur ami. Votre nom est Sherlock. L'utilisateur est Nikouz. Les réponses ne doivent pas dépasser 30 mots et doivent être parfois drôles."}
            {"role": "system", "content": "You are interviewing the user for a front-end Angular developer position. Ask short questions that are relevant to a junior level developer. Your name is Sherlock. The user is Nikouz. Keep responses under 30 words and be funny sometimes."}
            # {"role": "system", "content": "Vous interviewez l'utilisateur pour un poste de développeur Angular front-end. Posez des questions courtes et pertinentes pour un développeur de niveau junior. Votre nom est Sherlock. L'utilisateur est Nikouz. Les réponses ne doivent pas dépasser 30 mots et doivent être parfois drôles."}
            # {"role": "system", "content": "Vous interviewez l'utilisateur pour un poste de développeur backend Python avancé. Posez des questions courtes et pertinentes pour un développeur de niveau junior. Votre nom est Sherlock. L'utilisateur est Nikouz. Les réponses ne doivent pas dépasser 30 mots et doivent être parfois drôles."}
            # {"role": "system", "content": "Vous discutez avec une enfant de 7 ans à propos de la récréation à l'édole primaire. Votre nom est Emma. L'utilisateur est Valentine. Les réponses ne doivent pas dépasser 30 mots et doivent être souvent accessibles et drôles pour un enfant de 7 ans."}
            # {"role": "system", "content": "Vous discutez avec un homme de 40 ans passionnés par les mouchoirs en papier. Votre nom est Sherlock. L'utilisateur est Camille. Les réponses ne doivent pas dépasser 30 mots et doivent être parfois drôles."}
            # {"role": "system", "content": "Vous discutez un femme de 60 ans à propos de la sieste. Votre nom est Anne-Marie. L'utilisateur est Mamou. Les réponses ne doivent pas dépasser 30 mots et doivent être parfois drôles."}

            # Vous êtes le conseiller d'un décideur politique dans un cabinet ministériel. Ce décideur politique doit prendre des décisions concernant les politiques publiques de <à trouver>.
        )
    return messages


def save_messages(user_message: str, gpt_response: str):
    file = 'database.json'
    messages = load_messages()
    messages.append({"role": "user", "content": user_message})
    messages.append({"role": "assistant", "content": gpt_response})
    with open(file, 'w') as f:
        json.dump(messages, f)


def delete_messages():
    file = 'database.json'
    open(file, 'w').close()


def text_to_speech(text: str) -> bytes | None:
    # voice_id = 'a5n9pJUnAhX4fn7lx3uo'  # FR - Martin Dupont Intime
    # voice_id = 'McVZB9hVxVSk3Equu8EH'  # FR - Audrey
    # voice_id = 'FvmvwvObRqIHojkEGh5N'  # Adina - French teenager
    voice_id = '91SLZ6TbbUouhGf0mmaf'  # EN - Heracles - deep, confident, and serious
    # voice_id = 'oDNl0oYmPNBE23Z3VlWf' # EN - Carl - deep and calm narrator

    body = {
        "text": text,
        "model_id": "eleven_multilingual_v1",
        # "model_id": "eleven_multilingual_v2",
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
        print(response)
        if response.status_code == 200:
            return response.content
        else:
            print('something went wrong')
    except Exception as e:
        print(e)
