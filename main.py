from fastapi import FastAPI
from pydantic import BaseModel
from datetime import datetime, timedelta
from fastapi.responses import JSONResponse

app = FastAPI()

# Simulated database
conversations = {}

class WhatsAppMessage(BaseModel):
    wa_id: str
    message: str

@app.post("/webhook")
async def receive_message(msg: WhatsAppMessage):
    user_id = msg.wa_id
    now = datetime.utcnow()

    # Get last message timestamp
    last_time = conversations.get(user_id, {}).get("last_message")

    if last_time and now - last_time > timedelta(hours=24):
        return JSONResponse(status_code=403, content={"error": "24h window expired"})

    # Save timestamp and history
    conversations[user_id] = {
        "last_message": now,
        "history": conversations.get(user_id, {}).get("history", []) + [msg.message]
    }

    # Simulação de IA
    ai_reply = f"Recebido: {msg.message}. (resposta simulada)"

    return {"reply": ai_reply}

@app.get("/status")
def status():
    return {"conversations": conversations}

@app.get("/")
def home():
    return {"message": "FastAPI WhatsApp Webhook is running"}