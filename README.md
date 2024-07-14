## Create a Talking ChatGPT Interview Bot Project

Full tutorial found on YouTube at https://youtu.be/4y1a4syMJHM

```shell
conda create --name ChatGPT-Interview-Bot python fastapi uvicorn[standard] openai python-dotenv python-multipart requests
conda activate ChatGPT-Interview-Bot

uvicorn main:app --reload
```

http://127.0.0.1:8000
http://127.0.0.1:8000/docs
