from fastapi import FastAPI, Request, Query
from pydantic import BaseModel
from datetime import datetime, timedelta
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import httpx

app = FastAPI()

# CORS para o frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://wppwebfront.vercel.app"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Base em memória
conversations = {}

# Token de verificação da Meta
VERIFY_TOKEN = "meutoken123"

# Endpoint GET para validar o webhook da Meta
@app.get("/webhook")
def verify_webhook(
    hub_mode: str = Query(..., alias="hub.mode"),
    hub_challenge: str = Query(..., alias="hub.challenge"),
    hub_verify_token: str = Query(..., alias="hub.verify_token")
):
    if hub_mode == "subscribe" and hub_verify_token == VERIFY_TOKEN:
        return int(hub_challenge)
    return JSONResponse(status_code=403, content={"error": "Token inválido"})

# Endpoint POST para receber mensagens reais da Meta
@app.post("/webhook")
async def receive_message(request: Request):
    body = await request.json()
    entry = body.get("entry", [])
    for e in entry:
        changes = e.get("changes", [])
        for change in changes:
            value = change.get("value", {})
            messages = value.get("messages", [])
            if messages:
                msg = messages[0]
                user_id = msg["from"]
                message_text = msg["text"]["body"]
                now = datetime.utcnow()

                last_time = conversations.get(user_id, {}).get("last_message")
                if not last_time or now - last_time <= timedelta(hours=24):
                    conversations[user_id] = {
                        "last_message": now,
                        "history": conversations.get(user_id, {}).get("history", []) + [message_text]
                    }

                    # Chamada a IA (exemplo com Perplexity ou outro modelo via API externa)
                    try:
                        async with httpx.AsyncClient() as client:
                            response = await client.post("https://your-ai-api.com/ask", json={"question": message_text})
                            ai_reply = response.json().get("answer", "Desculpe, não entendi.")
                    except Exception:
                        ai_reply = "Erro ao consultar a IA."

                    # (Opcional) enviar resposta de volta usando a API da Meta aqui
                    # ...

    return {"status": "received"}

# Ver histórico das conversas
@app.get("/status")
def status():
    return {"conversations": conversations}

# Página inicial
@app.get("/")
def home():
    return {"message": "FastAPI WhatsApp Webhook is running"}
