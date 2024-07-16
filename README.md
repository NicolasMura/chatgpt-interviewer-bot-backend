## Create a Talking ChatGPT Interview Bot Project

Full tutorial found on YouTube at https://youtu.be/4y1a4syMJHM

```shell
conda create --name ChatGPT-Interview-Bot python fastapi uvicorn[standard] openai python-dotenv python-multipart requests
conda activate ChatGPT-Interview-Bot

uvicorn main:app --reload
```

Add `node_modules` to `.gitignore` file.

Add NPM, Nx and Angular app on this project:

```shell
npm init # don't forget to add "serve": "nx serve chat-frontend" to scrip section in package.json
npx nx@latest init
npx nx add @nx/angular
npx nx g @nx/angular:app chat-frontend --directory=apps --e2eTestRunner=none --unitTestRunner=none --routing=false --standalone=true --style=scss --addTailwind=true --skipTests=true --bundler=esbuild --ssr=false
```

Dev & contribute:

```shell
yarn serve
```

Build:

```shell

```
