import os
import pandas as pd
from fastapi import FastAPI, Request
import httpx

app = FastAPI()

# Lê as planilhas a partir da pasta 'data'
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

EXCEL_FILES = {
    "mg": pd.read_excel(os.path.join(BASE_DIR, "data", "Tabelas - Matriz.xlsx")),
    "ba": pd.read_excel(os.path.join(BASE_DIR, "data", "Tabela - Filial Feira.xlsx")),
    "pe": pd.read_excel(os.path.join(BASE_DIR, "data", "Tabelas - Filial Caruaru.xlsx")),
    "go": pd.read_excel(os.path.join(BASE_DIR, "data", "Tabelas - Filial Goiás.xlsx")),
}

# Token e ID fixos para envio via WhatsApp
TOKEN = "EAAOg3iog2D0BO0f5WONuxqxpZAC3mw6us5Ce0TBxRS7KfgAT5v3Jtjwdb4F4TgHG8ofmSk3ftCSgSWdejI5i4OSR9R70M42zBWSxAwyBjFMEZBRt1cChnXtpBENps6MowZCZBPDszgOi4W8VXzOFe8B4sEczTZC3ZBT2lE7VFBm2aDIaUx4iMGZA4XKYLyZCSo6ZCUFrH6oYZC5m736JoAZADONZBNKDMJ2HNtdZBzHN5uQZDZD"
PHONE_NUMBER_ID = "691595807367343"

@app.get("/status")
def status():
    return {"status": "ok"}

@app.post("/webhook")
async def webhook(request: Request):
    body = await request.json()
    print("Webhook recebido:", body)

    try:
        entry = body["entry"][0]
        changes = entry["changes"][0]
        value = changes["value"]
        messages = value.get("messages")

        if messages:
            msg = messages[0]
            phone = msg["from"]
            text = msg["text"]["body"].lower()

            response = processar_mensagem(text)
            await enviar_mensagem(phone, response)

    except Exception as e:
        print("Erro ao processar webhook:", e)

    return {"status": "received"}

def processar_mensagem(texto: str) -> str:
    import re

    match = re.search(r"produto\s+(\d+).*?(mg|ba|pe|go)", texto)
    if not match:
        return "Mensagem inválida. Envie no formato: qual o valor do produto 12345 em MG"

    cod_produto, uf = match.groups()
    df = EXCEL_FILES.get(uf)
    if df is None:
        return f"Não encontrei a planilha da região '{uf.upper()}'."

    resultado = df[df["seqproduto"] == int(cod_produto)]

    if resultado.empty:
        return f"Produto {cod_produto} não encontrado para {uf.upper()}."
    
    preco = resultado["preco"].values[0]
    return f"O valor do produto {cod_produto} em {uf.upper()} é R$ {float(preco):.2f}"

async def enviar_mensagem(telefone: str, mensagem: str):
    url = f"https://graph.facebook.com/v19.0/{PHONE_NUMBER_ID}/messages"
    headers = {
        "Authorization": f"Bearer {TOKEN}",
        "Content-Type": "application/json"
    }
    payload = {
        "messaging_product": "whatsapp",
        "to": telefone,
        "type": "text",
        "text": {"body": mensagem}
    }

    async with httpx.AsyncClient() as client:
        r = await client.post(url, headers=headers, json=payload)
        print("Resposta WhatsApp:", r.status_code, r.text)
