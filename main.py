from fastapi import FastAPI, Request
from pydantic import BaseModel
from datetime import datetime, timedelta
from fastapi.responses import JSONResponse
import httpx

app = FastAPI()

# Simulated database
conversations = {}

# Replace with your external AI model endpoint
AI_MODEL_ENDPOINT = "https://your-ai-model.com/ask"

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

    # Save timestamp
    conversations[user_id] = {"last_message": now, "history": conversations.get(user_id, {}).get("history", []) + [msg.message]}

    # Send to external AI model
    async with httpx.AsyncClient() as client:
        response = await client.post(AI_MODEL_ENDPOINT, json={"question": msg.message})
        ai_reply = response.json().get("answer", "Desculpe, não entendi.")

    return {"reply": ai_reply}

@app.get("/status")
def status():
    return {"conversations": conversations}  

@app.get("/")
def home():
    return {"message": "FastAPI WhatsApp Webhook is running"}