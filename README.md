# Create a Talking ChatGPT Interview Bot Project

I built a small bot as a POC, that uses GPT's OpenAI `whisper-1` speech-to-text transcription model & gpt-3.5-turbo chat completion model, as well as some Eleven Labs voices to get a fancy result.
From the tutorial I found on YouTube at https://youtu.be/4y1a4syMJHM, big thanks to @TravisMedia.

## Quick start

```shell
conda create --name ChatGPT-Interview-Bot python fastapi uvicorn[standard] openai python-dotenv python-multipart requests base64
conda activate ChatGPT-Interview-Bot

cp .env-sample .env # fill environment variables with your own

uvicorn main:app --port 3000 --reload
```

A documenter - ajout de elevenlabs :

```shell
pip install elevenlabs
```

Add `node_modules` to `.gitignore` file.

## Frontend setup (as a cheatsheet)

Add NPM, Nx and Angular app on this project:

```shell
yarn init
npx nx@latest init
npx nx add @nx/angular
npx nx g @nx/angular:app chat-frontend --directory=apps --e2eTestRunner=none --unitTestRunner=none --routing=false --standalone=true --style=scss --addTailwind=true --skipTests=true --bundler=esbuild --ssr=false
```

Add these 2 scripts to the `package.json` file:

```json
(...)
"scripts": {
  "serve": "nx serve chat-frontend",
  "build": "nx build chat-frontend --deploy-url ./static/browser/ && sed -i '' 's/favicon.ico/.\\/static\\/browser\\/favicon.ico/g' static/browser/index.html"
},
(...)
```

> :warning: **_Important_**
>
> `sed -i '' (...)` command will work on Mac OS X only

Adapt the target Angular build in `apps/chat-frontend/project.json`:

```json
{
  (...)
  "targets": {
    "build": {
      "executor": "@angular-devkit/build-angular:application",
      "outputs": [
        "{options.outputPath}"
      ],
      "options": {
        "outputPath": "static", // <-- here
        "index": "apps/chat-frontend/src/index.html",
        "browser": "apps/chat-frontend/src/main.ts",
        (...)
      },
      "configurations": {
        (...)
      },
      "defaultConfiguration": "production"
    },
    "serve": {
      (...)
    },
    (...)
  }
}
```

## Dev & contribute (for the frontend app)

```shell
yarn serve
```

Tested locally on an iPhone 8 (Safari only - Not working on Chrome and Firefox because we can't access the microphone):

```shell
yarn serve --host 0.0.0.0
uvicorn main:app --host <your_machine_IP> --port 3000 --reload
```

To make it work during development, connect your iPhone to your machine via a USB cable, on your iPhone open a tab at http://<your_IP>:4200 on Safari and accept the security risk.
Finally, go to Safari on your machine, open Develop > your machine > your iPhone's browser to inspect, click on the "Device Settings" button and check the "allow media capture on insecure sites" and "Disable cross-origin restrictions" options:

![alt text](Safari-allow-media-capture-on-insecure-sites.png)

## Build (for the frontend app)

```shell
yarn build
```

## Deploy on Render

### Direct method with `render.yaml`

I've tested [Render](https://dashboard.render.com/web) to quickly deploy this app as a FastAPI app, and it does the job pretty well. See the `render.yaml` file to get some insight and the live app at https://chatgpt-interviewer-bot-latest.onrender.com.

The only tricky point is that you have to remember adding a `PORT` environment variable (as well as `OPEN_AI_KEY`, `OPEN_AI_ORG` and `ELEVENLABS_KEY` ones) binded to 3000, and putting it in the start command in the Render's Web Service settings:

```shell
uvicorn main:app --host 0.0.0.0 --port $PORT
```

Don't forget to run `yarn build` and add frontend static files before pushing on the repo.

### Docker method

@TODO A documenter

## Credits

[![AWS S3](https://yt3.googleusercontent.com/ytc/AIdro_l00TDaIm6OxCv6eJtOwdn2RHbFjeUJ8OJYVGmgdA4pEQ=s160-c-k-c0x00ffffff-no-rj)](https://www.youtube.com/@TravisMedia 'Travis Media')

## Next steps

- Intégrer le build sur un hook pre-push Husky
- N° de build ou n° de tag / commit + timestamp à intégrer au build via les GitHub actions
- PWA
- Dé-contextualiser la conversation
- Rapatrier les features backend dans le frontend ? (si possible)
- Robot 2D ou 3D avec expression faciale minimale et synchronisation labiale
  - v1 "simple" en utilisant l’avatar de synthèse vocale de Microsoft Azure AI (Tuto dispo ici : https://raokarthik83.medium.com/building-a-text-to-speech-avatar-app-with-reactjs-and-azure-tts-avatar-ai-c9d2da0e9f75)
  - v2 complète en récupérant un modèle sympa et en l'animant (cf. conversation ChatGPT)

## To be investigated

https://www.youtube.com/watch?v=taJlPG82Ucw (Coolify course)
https://www.radiantmediaplayer.com/blog/at-last-safari-17.1-now-brings-the-new-managed-media-source-api-to-iphone.html
https://developer.apple.com/videos/play/wwdc2023/10122/
https://github.com/KenMwaura1/Fast-Api-Vue
