# Visual regression testing with playwright and openai

This GitHub Action is designed to streamline visual regression testing by automatically comparing images and highlighting differences between them. Ideal for CI/CD pipelines, it helps developers catch unintended visual changes in web apps, design systems, or any UI-driven project. With easy integration and configurable thresholds, it ensures your visuals stay consistent—enabling fast, automated feedback for every commit or pull request.

# Install

## Start virtual environment

`python3.10 -m venv venv310 && source venv310/bin/activate`

## Install dependencies

`(python3 -m )pip install -r requirements.txt`

## Run playwright mcp

`npm install -g @playwright/mcp`

## Run mcp server

`npx @playwright/mcp@latest --port 8931`

## Run script

```
python3 scripts/run_agent.py --base-url https://www.brunivisual.com/ --pr-url https://bruni-website-git-actionexp-nevinbuilds.vercel.app
```

## Add .env openai key

`OPENAI_API_KEY=`
