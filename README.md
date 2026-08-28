# GlasyTech Leads Bot
Telegram bot that serves the latest GlasyTech Solutions automotive-garage leads file from Kiambu County.

## Setup
```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
```

## Configure `.env`
- `TOKEN`: Telegram bot token from @BotFather
- `SOURCE_DIR`: leads folder, default `C:\Users\Kelvin Karonji\.hermes-niches\active\research`
- `ALLOWED_USERS`: comma-separated Telegram user IDs, optional
- `WEBHOOK_URL`: public HTTPS URL when deploying, e.g. `https://glasytech-leads.onrender.com`
- `PORT`: port for webhook server, default `10000`

## Run locally
```bash
python main.py
```

## Bot commands
- `/start` - usage
- `/latest` - show latest leads summary
- `/file` - send latest leads markdown file

## Deploy
Recommended: Render free web service.
- Build command: `pip install -r requirements.txt`
- Start command: `uvicorn main:app --host 0.0.0.0 --port $PORT`
- Set env vars in dashboard
- After first deploy, set webhook by visiting:
  `https://api.telegram.org/bot<TOKEN>/setWebhook?url=<WEBHOOK_URL>/telegram/<TOKEN>`
