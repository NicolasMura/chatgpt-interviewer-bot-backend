import asyncio
import base64
import json
import os
import shutil
import subprocess
import time
from typing import List, TypedDict, cast

import aiofiles
import requests
from dotenv import load_dotenv
from elevenlabs import play
from elevenlabs.client import ElevenLabs
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from openai import OpenAI
from openai.types.audio import Transcription
from openai.types.chat import ChatCompletion
from pydantic import BaseModel
from starlette.responses import Response


class UserMessage(BaseModel):
    message: str


class ChatMessage(BaseModel):
    text: str
    audio: str
    lipsync: dict
    facialExpression: str
    animation: str


class MessagesDict(TypedDict):
    messages: List[ChatMessage]


class PrettyJSONResponse(Response):
    media_type = "application/json"

    def render(self, content) -> bytes:
        return json.dumps(
            content,
            ensure_ascii=False,
            allow_nan=False,
            indent=2,
            separators=(", ", ": "),
        ).encode("utf-8")


load_dotenv()

elevenlabs_key = os.getenv("ELEVENLABS_KEY")
openAiClient = OpenAI(organization=os.getenv("OPEN_AI_ORG"),
                      api_key=os.getenv("OPEN_AI_KEY"))
eleventLabsClient = ElevenLabs(
    api_key=elevenlabs_key,
)

app = FastAPI()
app.mount("/static/browser",
          StaticFiles(directory="static/browser"), name="static")

origins = [
    "http://localhost:4200",
    "https://localhost:4200",
    "http://localhost:5173",
    "https://chatgpt-interviewer-bot-latest.onrender.com",
    "https://chat-bot-gpt.projects.gcp.nicolasmura.com",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_methods=["*"],
    allow_headers=["*"],
)


async def iterfile(audio_output: bytes | None):
    if audio_output:
        yield audio_output
    else:
        raise HTTPException(status_code=500, detail="Audio output is None")


@app.get("/")
async def root():
    return FileResponse("static/browser/index.html")


@app.get("/database", response_class=PrettyJSONResponse)
async def get_database():
    return load_messages()


@app.post("/talk")
async def post_audio(file: UploadFile = File(...)):
    path = f"{file.filename}"
    with open(path, 'w+b') as f:
        shutil.copyfileobj(file.file, f)

    user_message = transcribe_audio(file)
    print(user_message.text)

    # Delete the file
    os.remove(path)

    chat_response = get_chat_response(user_message.text)
    audio_output = text_to_speech(chat_response)

    return StreamingResponse(iterfile(audio_output), media_type="audio/mp3")


# Ajout de la route pour gérer l'envoi de texte
@app.post("/talk-text")
async def post_text(message: UserMessage):
    print('Message', message.message)

    if not message.message:
        print('No message')
        raise HTTPException(status_code=400, detail="No message")

    chat_response = get_chat_response(message.message)
    audio_output = text_to_speech(chat_response)

    return StreamingResponse(iterfile(audio_output), media_type="audio/mp3")


# Ajout de la route pour gérer l'envoi de texte + récupération des messages enrichis
@app.post("/talk-text-v2")
async def post_text_v2(message: UserMessage):
    print('Message', message.message)
    userMsg = message.message

    messages: list[ChatMessage] = []
    if not userMsg:
        print('No message')
        messages = [
            ChatMessage(
                text="Hey dear... How was your day?",
                audio=await audio_file_to_base64("audios/welcome-Nico.mp3"),
                lipsync=await read_json_transcript("audios/welcome-Nico.json"),
                facialExpression="smile",
                animation="Talking_1",
            ),
            ChatMessage(
                text="Hey dear... How was your day?",
                audio=await audio_file_to_base64("audios/message_1.mp3"),
                lipsync=await read_json_transcript("audios/message_1.json"),
                facialExpression="sad",
                animation="Talking_1",
            ),
        ]
    else:
        messages = await get_chat_response_v2(userMsg)

    return {"messages": messages}


@app.post("/talk-fake")  # for testing purposes
async def post_audio_fake(file: UploadFile = File(...)):
    path = f"{file.filename}"
    with open(path, 'w+b') as f:
        shutil.copyfileobj(file.file, f)

    transcribe_audio(file)

    return StreamingResponse(open('test.mp3', 'rb'), media_type="audio/mp3")


@app.get("/reset")
async def reset():
    delete_messages()
    return {"message": "Chat history successfully reset."}


def transcribe_audio(file: UploadFile) -> Transcription:
    filename = file.filename

    if filename is None:
        raise HTTPException(status_code=400, detail="No file uploaded")

    audio_file = open(filename, 'rb')
    transcription = openAiClient.audio.transcriptions.create(
        model="whisper-1",
        file=audio_file,
        response_format="verbose_json",
        # language="en",
        language="fr"
    )
    print('************')
    print(transcription.text)
    print(transcription.model_dump_json())
    print('************')

    return transcription


# def get_chat_response(user_message: dict[str, str]):
def get_chat_response(user_message: str) -> str:
    messages = load_messages()
    messages.append({"role": "user", "content": user_message})

    # Send to ChatGpt/OpenAi
    gpt_response: ChatCompletion = openAiClient.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=messages
    )

    parsed_gpt_response = gpt_response.choices[0].message.content or 'No response'

    # Save messages
    save_messages(user_message, parsed_gpt_response)

    return parsed_gpt_response


async def get_chat_response_v2(user_message: str):
    messages = load_messages()
    messages.append({"role": "user", "content": user_message})
    print(messages)

    # Send to ChatGpt/OpenAi
    gpt_response: ChatCompletion = openAiClient.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": message["content"]}  # type: ignore
                  for message in messages],
        response_format={
            "type": "json_object",
        },
        max_tokens=1000,
        temperature=0.6,
    )

    # parsed_gpt_response type is sometimes an array of ChatMessage, and sometimes a JSON object with a messages property
    parsed_gpt_response: list[ChatMessage] | MessagesDict = json.loads(
        gpt_response.choices[0].message.content or 'No response')
    print('***** get_chat_response_v2 ******')
    print(parsed_gpt_response)
    tmp = cast(MessagesDict, parsed_gpt_response)["messages"]
    if tmp:
        # ChatGPT is not 100% reliable, sometimes it directly returns an array and sometimes a JSON object with a messages property
        parsed_gpt_response = tmp

    chat_messages = cast(list[ChatMessage], parsed_gpt_response)
    print('$$$$$$$$$$$')
    print(chat_messages)
    print('$$$$$$$$$$$')
    messages: list[ChatMessage] = []

    for (index, message) in enumerate(chat_messages):
        print('message', message)
        # generate audio file
        # The name of your audio file
        path = "audios/message_{}.mp3".format(index)
        print('path', path)
        #  The text you wish to convert to speech
        text_input = message['text']  # type: ignore
        text_to_speech_v2(text_input, path)
        # generate lipsync
        await lip_sync_message(index)
        message['audio'] = await audio_file_to_base64(path)  # type: ignore
        path = "audios/message_{}.json".format(index)
        message['lipsync'] = await read_json_transcript(path)  # type: ignore

        # Save message
        # save_messages_v2(user_message, parsed_gpt_response)

        # messages.append(ChatMessage(
        #     text=message.content,
        #     audio=await audio_file_to_base64("welcome-Nico.mp3"),
        #     # "lipsync": await readJsonTranscript("audios/welcome-Nico.json"),
        #     facialExpression="smile",
        #     animation="Talking_1",
        # ))

    return chat_messages


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
            # {"role": "system", "content": "You're my best friend. Your name is Sherlock, and you love solving puzzles and mysteries. The user is Nikouz. Answers must be no longer than 30 words and must be funny sometimes."}
            # {"role": "system", "content": "Vous êtes mon meilleur ami. Votre nom est Sherlock. L'utilisateur est Nikouz. Les réponses ne doivent pas dépasser 30 mots et doivent être parfois drôles."}
            # {"role": "system", "content": "You are interviewing the user for a front-end Angular developer position. Ask short questions that are relevant to a junior level developer. Your name is Sherlock. The user is Nikouz. Keep responses under 30 words and be funny sometimes."}
            # {"role": "system", "content": "Vous interviewez l'utilisateur pour un poste de développeur Angular front-end. Posez des questions courtes et pertinentes pour un développeur de niveau junior. Votre nom est Sherlock. L'utilisateur est Nikouz. Les réponses ne doivent pas dépasser 30 mots et doivent être parfois drôles."}
            # {"role": "system", "content": "Vous interviewez l'utilisateur pour un poste de développeur backend Python avancé. Posez des questions courtes et pertinentes pour un développeur de niveau junior. Votre nom est Sherlock. L'utilisateur est Nikouz. Les réponses ne doivent pas dépasser 30 mots et doivent être parfois drôles."}
            # {"role": "system", "content": "Vous discutez avec une enfant de 7 ans à propos de la récréation à l'école primaire. Votre nom est Emma. L'utilisateur est Valentine. Les réponses ne doivent pas dépasser 30 mots et doivent être souvent accessibles et drôles pour un enfant de 7 ans."}
            # {"role": "system", "content": "Vous discutez avec un homme de 40 ans passionnés par les mouchoirs en papier. Votre nom est Sherlock. L'utilisateur est Camille. Les réponses ne doivent pas dépasser 30 mots et doivent être parfois drôles."}
            # {"role": "system", "content": "Vous discutez un femme de 60 ans à propos de la sieste. Votre nom est Anne-Marie. L'utilisateur est Mamou. Les réponses ne doivent pas dépasser 30 mots et doivent être parfois drôles."}
            # {"role": "system", "content": "Votre nom est Hillary. Vous êtes la conseillère d'une décideuse politique, Julie, femme ambitieuse de 40 ans, dans un cabinet ministériel. Cette décideuse politique doit prendre des décisions concernant les politiques publiques de lutte contre la fraude fiscale. Les réponses ne doivent pas dépasser 60 mots et doivent être impartiales et professionnelles."}
            {
                "role": "system",
                "content": " \
                    Utilisez la langue française.\
                    Vous êtes une petite amie virtuelle.\
                    Vous répondrez toujours avec un tableau JSON de messages, avec un maximum de 3 messages.\
                    Chaque message a un texte, une expression faciale et une propriété d'animation.\
                    Les différentes expressions faciales sont : smile, sad, angry, surprised, funnyFace, et default.\
                    Les différentes animations sont : Talking_0, Talking_1, Talking_2, Crying, Laughing, Rumba, Idle, Terrified, et Angry.\
                ",
            }
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
    print('************')
    print(text)
    print('************')
    # voice_id = 'a5n9pJUnAhX4fn7lx3uo'  # FR - Martin Dupont Intime
    # voice_id = 'McVZB9hVxVSk3Equu8EH'  # FR - Audrey
    voice_id = 'FvmvwvObRqIHojkEGh5N'  # FR - Adina - French teenager
    # voice_id = '91SLZ6TbbUouhGf0mmaf'  # EN - Heracles - deep, confident, and serious
    # voice_id = 'oDNl0oYmPNBE23Z3VlWf' # EN - Carl - deep and calm narrator

    body = {
        "text": text,
        # "model_id": "eleven_multilingual_v1",
        "model_id": "eleven_multilingual_v2",
        "voice_settings": {
            "stability": 0,
            "similarity_boost": 0,
            "style": 0.5,
            "use_speaker_boost": True
        },
    }

    headers = {
        "Content-Type": "application/json",
        "Accept": "audio/mp3",
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


def text_to_speech_v2(text: str, output_filename: str) -> bytes | None:
    print('************')
    print(text)
    print('************')
    # voice_id = 'a5n9pJUnAhX4fn7lx3uo'  # FR - Martin Dupont Intime
    # voice_id = 'McVZB9hVxVSk3Equu8EH'  # FR - Audrey
    voice_id = 'FvmvwvObRqIHojkEGh5N'  # FR - Adina - French teenager
    # voice_id = '91SLZ6TbbUouhGf0mmaf'  # EN - Heracles - deep, confident, and serious
    # voice_id = 'oDNl0oYmPNBE23Z3VlWf' # EN - Carl - deep and calm narrator

    audio = eleventLabsClient.generate(
        text=text,
        voice=voice_id,
        model="eleven_multilingual_v2",
    )

    # save audio to file
    with open(output_filename, "wb") as f:
        f.write(b''.join(audio))


async def read_json_transcript(file: str) -> dict:
    async with aiofiles.open(file, mode='r', encoding='utf-8') as f:
        data = await f.read()
        return json.loads(data)


async def audio_file_to_base64(file) -> str:
    with open(file, "rb") as audio_file:
        print('audio_file', audio_file)
        encoded_string = base64.b64encode(audio_file.read()).decode("utf-8")
        return encoded_string


async def exec_command(command):
    process = await asyncio.create_subprocess_shell(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    stdout, stderr = await process.communicate()
    if process.returncode != 0:
        raise Exception(f"Command failed: {stderr.decode()}")


async def lip_sync_message(message: int):
    start_time = time.time()
    print(f"Starting conversion for message {message}")

    await exec_command(
        f"ffmpeg -y -i audios/message_{
            message}.mp3 audios/message_{message}.wav"
    )
    print(f"Conversion done in {int((time.time() - start_time) * 1000)}ms")

    await exec_command(
        f"./bin/rhubarb -f json -o audios/message_{
            message}.json audios/message_{message}.wav -r phonetic"
    )
    print(f"Lip sync done in {int((time.time() - start_time) * 1000)}ms")
