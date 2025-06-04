from fastapi import FastAPI, Request, Query
from pydantic import BaseModel
from datetime import datetime, timedelta
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import httpx
import os

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://wppwebfront.vercel.app"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

conversations = {}
VERIFY_TOKEN = "meutoken123"

WHATSAPP_API_URL = "https://graph.facebook.com/v18.0/598348203371773/messages"
WHATSAPP_TOKEN = "EAAOg3iog2D0BO4I0TSD2xAfZAiZANGyGkmT1TIojp7vNl5RAFi7iCmCNJrkEkwQ1EkCYMVV3haj8W3ZAZC01rfBLw1wdqQgxi3IRxclGsvNzjEbhuz3aVjbLGMiZBMEi3RffcPharCUtNHot39OcJPBQ2nRL737KfLEedmlDxfJfQEhP0zcTzG87PMHDvnotgGOPrBWYPpf1mmjnMoXBhxKWsIEvm6HJvocIZD"

async def enviar_mensagem_resposta(numero_destino: str, texto: str):
    headers = {
        "Authorization": f"Bearer {WHATSAPP_TOKEN}",
        "Content-Type": "application/json"
    }
    payload = {
        "messaging_product": "whatsapp",
        "to": numero_destino,
        "type": "text",
        "text": {"body": texto}
    }
    async with httpx.AsyncClient() as client:
        resp = await client.post(WHATSAPP_API_URL, json=payload, headers=headers)
        print(f"Resposta enviada: {resp.status_code} | {resp.text}")

@app.get("/webhook")
def verify_webhook(
    hub_mode: str = Query(..., alias="hub.mode"),
    hub_challenge: str = Query(..., alias="hub.challenge"),
    hub_verify_token: str = Query(..., alias="hub.verify_token")
):
    if hub_mode == "subscribe" and hub_verify_token == VERIFY_TOKEN:
        return int(hub_challenge)
    return JSONResponse(status_code=403, content={"error": "Token inválido"})

@app.post("/webhook")
async def receive_message(request: Request):
    body = await request.json()
    print("Webhook recebido:", body)
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

                    # IA simulada
                    ai_reply = f"Recebido: {message_text}. (resposta simulada)"

                    # Enviar resposta automática
                    await enviar_mensagem_resposta(user_id, ai_reply)

    return {"status": "received"}

@app.get("/status")
def status():
    return {"conversations": conversations}

@app.get("/")
def home():
    return {"message": "FastAPI WhatsApp Webhook is running"}
