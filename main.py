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

elevenlabs_key = os.getenv("ELEVENLABS_KEY")
print('OPEN_AI_KEY: ', os.getenv("OPEN_AI_KEY"))
print('elevenlabs_key: ', elevenlabs_key)

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
