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
yarn init
npx nx@latest init
npx nx add @nx/angular
npx nx g @nx/angular:app chat-frontend --directory=apps --e2eTestRunner=none --unitTestRunner=none --routing=false --standalone=true --style=scss --addTailwind=true --skipTests=true --bundler=esbuild --ssr=false
```

Don't forget to add these 2 scripts to the `package.json` file:

```json
(...)
"scripts": {
  "serve": "nx serve chat-frontend",
  "build": "nx build chat-frontend --deploy-url ./static/browser/ && sed -i '' 's/favicon.ico/.\\/static\\/browser\\/favicon.ico/g' static/browser/index.html"
},
(...)
```

(sed command will work on Mac OS X only)

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

# Dev & contribute:

```shell
yarn serve
```

# Build:

```shell
yarn build
```
