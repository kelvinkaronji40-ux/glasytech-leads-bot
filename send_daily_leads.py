"""Send today's GlasyTech leads to Telegram and WhatsApp."""
from __future__ import annotations

import json
import os
from datetime import date
from pathlib import Path

try:
    from dotenv import load_dotenv
except Exception:  # pragma: no cover
    def load_dotenv(**kwargs):  # type: ignore[misc]
        return None

import urllib.request

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(dotenv_path=BASE_DIR / ".env", override=False)

TODAY = date.today().isoformat()
LEADS_PATH = Path(
    os.environ.get(
        "SOURCE_DIR",
        r"C:\Users\Kelvin Karonji\.hermes-niches\active\research",
    )
) / f"glasytech-leads-{TODAY}.md"

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "")
WHATSAPP_TOKEN = os.environ.get("WHATSAPP_ACCESS_TOKEN", "")
WHATSAPP_PHONE_NUMBER_ID = os.environ.get("WHATSAPP_PHONE_NUMBER_ID", "")
WHATSAPP_RECIPIENTS = [
    x.strip() for x in os.environ.get("WHATSAPP_RECIPIENTS", "").split(",") if x.strip()
]


def _load_leads(path: Path) -> str:
    if not path.exists():
        raise FileNotFoundError(f"Leads file not found: {path}")
    text = path.read_text(encoding="utf-8")
    # strip markdown table markers and footer for sending
    lines = []
    in_table = False
    for line in text.splitlines():
        if line.strip().startswith("| #"):
            in_table = True
            continue
        if in_table and line.strip().startswith("|---"):
            continue
        if in_table and line.strip().startswith("|"):
            parts = [p.strip() for p in line.strip().strip("|").split("|")]
            if len(parts) >= 6:
                name, location, phone, email, website = parts[1], parts[2], parts[3], parts[4], parts[5]
                lines.append(
                    f"{len(lines)+1}. {name} | {location} | {phone} | {email} | {website}"
                )
                continue
        if line.strip().startswith("— Tisement Media"):
            continue
        if line.strip().startswith("#"):
            continue
    if not lines:
        raise ValueError("No leads parsed from file")
    header = "GlasyTech Daily Leads"
    footer = "- Tisement Media | Automation services for businesses"
    return "\n\n".join([header, "", "\n".join(lines), "", footer])


def _send_telegram(text: str) -> dict:
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        return {"skipped": True, "reason": "missing telegram config"}
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = json.dumps({"chat_id": int(TELEGRAM_CHAT_ID), "text": text}).encode("utf-8")
    req = urllib.request.Request(
        url, data=payload, headers={"Content-Type": "application/json"}, method="POST"
    )
    with urllib.request.urlopen(req) as r:
        return {"ok": True, "status": r.status, "body": json.loads(r.read().decode())}


def _send_whatsapp(text: str, to: str) -> dict:
    if not WHATSAPP_TOKEN or not WHATSAPP_PHONE_NUMBER_ID:
        return {"skipped": True, "reason": "missing whatsapp config"}
    url = f"https://graph.facebook.com/v19.0/{WHATSAPP_PHONE_NUMBER_ID}/messages"
    payload = json.dumps(
        {
            "messaging_product": "whatsapp",
            "to": to,
            "type": "text",
            "text": {"body": text},
        }
    ).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=payload,
        headers={
            "Authorization": f"Bearer {WHATSAPP_TOKEN}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    with urllib.request.urlopen(req) as r:
        return {"ok": True, "status": r.status, "body": json.loads(r.read().decode())}


def main() -> int:
    try:
        message = _load_leads(LEADS_PATH)
    except Exception as e:
        print(f"LOAD_ERROR: {e}")
        return 1

    results = []
    results.append(("telegram", _send_telegram(message)))
    for recipient in WHATSAPP_RECIPIENTS:
        results.append((f"whatsapp:{recipient}", _send_whatsapp(message, recipient)))

    print(json.dumps({"leads_file": str(LEADS_PATH), "results": results}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
