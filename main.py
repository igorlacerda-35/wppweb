from fastapi import FastAPI, Query
from pydantic import BaseModel
from datetime import datetime, timedelta
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# ✅ Libera acesso do frontend no Vercel
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://wppwebfront.vercel.app"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Simulated database (em memória)
conversations = {}

# ✅ Token de verificação da Meta
VERIFY_TOKEN = "meutoken123"

# ✅ 1. VERIFICAÇÃO DO WEBHOOK (GET)
@app.get("/webhook")
def verify_webhook(
    hub_mode: str = Query(..., alias="hub.mode"),
    hub_challenge: str = Query(..., alias="hub.challenge"),
    hub_verify_token: str = Query(..., alias="hub.verify_token")
):
    if hub_mode == "subscribe" and hub_verify_token == VERIFY_TOKEN:
        return int(hub_challenge)
    return JSONResponse(status_code=403, content={"error": "Token inválido"})

# ✅ 2. RECEBIMENTO DE MENSAGENS (POST)
class WhatsAppMessage(BaseModel):
    wa_id: str
    message: str

@app.post("/webhook")
async def receive_message(msg: WhatsAppMessage):
    user_id = msg.wa_id
    now = datetime.utcnow()

    last_time = conversations.get(user_id, {}).get("last_message")

    if last_time and now - last_time > timedelta(hours=24):
        return JSONResponse(status_code=403, content={"error": "24h window expired"})

    conversations[user_id] = {
        "last_message": now,
        "history": conversations.get(user_id, {}).get("history", []) + [msg.message]
    }

    ai_reply = f"Recebido: {msg.message}. (resposta simulada)"
    return {"reply": ai_reply}

# ✅ 3. Visualização no painel React
@app.get("/status")
def status():
    return {"conversations": conversations}

# ✅ 4. Página básica
@app.get("/")
def home():
    return {"message": "FastAPI WhatsApp Webhook is running"}
