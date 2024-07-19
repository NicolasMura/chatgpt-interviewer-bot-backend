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
print('OPEN_AI_KEY: ', os.getenv("OPEN_AI_KEY"))
