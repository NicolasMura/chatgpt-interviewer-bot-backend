import os

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, UploadFile
from openai import OpenAI

load_dotenv()

client = OpenAI(organization=os.getenv("OPEN_AI_ORG"),
                api_key=os.getenv("OPEN_AI_KEY"))

app = FastAPI()


@app.get("/")
async def root():
    return {"message": "Audio has been transcribed!"}


@app.post("/talk")
async def post_audio(file: UploadFile):
    filename = file.filename

    if filename is None:
        raise HTTPException(status_code=400, detail="No file uploaded")

    audio_file = open(filename, 'rb')
    transcription = client.audio.transcriptions.create(
        model="whisper-1",
        file=audio_file
    )
    print(transcription)
