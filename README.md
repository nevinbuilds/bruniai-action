# Install

## Start virtual environment

`python3.10 -m venv venv310 && source venv310/bin/activate`

## Install dependencies

`(python3 -m )pip install -r requirements.txt`

## RUn playwright mcp

`npm install -g @playwright/mcp`

## Run mcp server

`npx @playwright/mcp@latest --port 8931`

## Run script

```
python3 scripts/run_agent.py --base-url https://www.brunivisual.com/ --pr-url https://bruni-website-git-actionexp-nevinbuilds.vercel.app
```

## Add .env openai key

`OPENAI_API_KEY=`
