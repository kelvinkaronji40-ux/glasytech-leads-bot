import os
import re
from pathlib import Path
from datetime import datetime
from contextlib import asynccontextmanager
from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

load_dotenv()
TOKEN = os.environ.get("TOKEN")
if not TOKEN:
    raise RuntimeError("Missing TOKEN. Set it in .env or environment.")
SOURCE_DIR = Path(os.environ.get("SOURCE_DIR", r"C:\Users\Kelvin Karonji\.hermes-niches\active\research"))
ALLOWED_USERS = {int(x) for x in os.environ.get("ALLOWED_USERS", "").split(",") if x.strip()}
WEBHOOK_PATH = f"/telegram/{TOKEN}"
WEBHOOK_URL = os.environ.get("WEBHOOK_URL", "")
PORT = int(os.environ.get("PORT", "10000"))


def allowed(user_id: int) -> bool:
    return not ALLOWED_USERS or user_id in ALLOWED_USERS


def latest_leads_file() -> Path | None:
    files = sorted(SOURCE_DIR.glob("glasytech-leads-*.md"), reverse=True)
    return files[0] if files else None


def parse_leads(path: Path) -> tuple[int, int, str]:
    text = path.read_text(encoding="utf-8")
    rows = len(re.findall(r"^\| *\d+ *\|", text, flags=re.MULTILINE))
    phones = len(re.findall(r"\b(?:\+?254|0)[17]\d{8}\b", text))
    summary = f"Latest: {path.name}\nLeads: {rows}\nWith phone: {phones}"
    return rows, phones, summary


async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not allowed(update.effective_user.id):
        await update.message.reply_text("Unauthorized.")
        return
    await update.message.reply_text(
        "GlasyTech Leads Bot\nCommands:\n/latest - latest leads\n/file - send latest leads file\n/help - this message"
    )


async def cmd_latest(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not allowed(update.effective_user.id):
        await update.message.reply_text("Unauthorized.")
        return
    path = latest_leads_file()
    if not path:
        await update.message.reply_text("No leads file found yet.")
        return
    _, _, summary = parse_leads(path)
    await update.message.reply_text(summary)


async def cmd_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not allowed(update.effective_user.id):
        await update.message.reply_text("Unauthorized.")
        return
    path = latest_leads_file()
    if not path:
        await update.message.reply_text("No leads file found yet.")
        return
    await update.message.reply_document(document=path.open("rb"), filename=path.name, caption="GlasyTech leads")


@asynccontextmanager
async def lifespan(app: FastAPI):
    telegram_app = ApplicationBuilder().token(TOKEN).build()
    telegram_app.add_handler(CommandHandler("start", cmd_start))
    telegram_app.add_handler(CommandHandler("latest", cmd_latest))
    telegram_app.add_handler(CommandHandler("file", cmd_file))
    await telegram_app.initialize()
    await telegram_app.start()
    app.state.telegram_app = telegram_app
    if WEBHOOK_URL:
        await telegram_app.bot.set_webhook(url=WEBHOOK_URL.rstrip("/") + WEBHOOK_PATH)
    print(f"READY token={TOKEN} webhook={WEBHOOK_URL}{WEBHOOK_PATH} port={PORT}")
    yield
    await telegram_app.stop()


app = FastAPI(lifespan=lifespan)


@app.get("/health")
async def health():
    return {"status": "ok", "time": datetime.utcnow().isoformat()}


@app.get("/")
async def root():
    return {"ok": True, "service": "glasytech-leads-bot"}


@app.post(WEBHOOK_PATH)
async def telegram_webhook(request: Request):
    data = await request.json()
    update = Update.de_json(data, app.state.telegram_app.bot)
    await app.state.telegram_app.update_queue.put(update)
    return JSONResponse({"ok": True})
