from fastapi import FastAPI, Request
from pydantic import BaseModel
import pandas as pd
import os
import httpx
import re

app = FastAPI()

# Carregar planilhas uma vez na memória
BASE_DIR = "/mnt/data"
PLANILHAS = {
    "mg": pd.read_excel(os.path.join(BASE_DIR, "Tabelas - Matriz.xlsx")),
    "pe": pd.read_excel(os.path.join(BASE_DIR, "Tabelas - Filial Caruaru.xlsx")),
    "ba": pd.read_excel(os.path.join(BASE_DIR, "Tabela - Filial Feira.xlsx")),
    "go": pd.read_excel(os.path.join(BASE_DIR, "Tabelas - Filial Goiás.xlsx"))
}

# Padronizar colunas
for df in PLANILHAS.values():
    df.columns = df.columns.str.lower()

# Dados fixos
WPP_TOKEN = "EAAOg3iog2D0BO0f5WONuxqxpZAC3mw6us5Ce0TBxRS7KfgAT5v3Jtjwdb4F4TgHG8ofmSk3ftCSgSWdejI5i4OSR9R70M42zBWSxAwyBjFMEZBRt1cChnXtpBENps6MowZCZBPDszgOi4W8VXzOFe8B4sEczTZC3ZBT2lE7VFBm2aDIaUx4iMGZA4XKYLyZCSo6ZCUFrH6oYZC5m736JoAZADONZBNKDMJ2HNtdZBzHN5uQZDZD"
PHONE_ID = "691595807367343"
GRAPH_URL = f"https://graph.facebook.com/v19.0/{PHONE_ID}/messages"

# Webhook para receber mensagens
@app.post("/webhook")
async def receber_mensagem(request: Request):
    payload = await request.json()
    try:
        mensagem = payload['entry'][0]['changes'][0]['value']['messages'][0]
        texto = mensagem['text']['body'].lower()
        telefone = mensagem['from']
        resposta = buscar_preco(texto)
        await enviar_resposta(telefone, resposta)
    except Exception as e:
        print("Erro ao processar mensagem:", e)
    return {"status": "ok"}

def buscar_preco(texto):
    match = re.search(r'(\d+)[^\d\w]+([a-z]{2})', texto)
    if not match:
        return "Por favor, envie no formato: 'valor do produto 8576 em MG'."

    codigo = int(match.group(1))
    uf = match.group(2).lower()

    if uf not in PLANILHAS:
        return f"Região '{uf.upper()}' não reconhecida. Use: MG, PE, BA ou GO."

    df = PLANILHAS[uf]
    linha = df[df['seqproduto'] == codigo]

    if linha.empty:
        return f"Produto {codigo} não encontrado na planilha de {uf.upper()}."

    preco = linha.iloc[0][uf]
    produto = linha.iloc[0]['produto']
    return f"Produto: {produto}\nCódigo: {codigo}\nPreço em {uf.upper()}: R$ {preco:.2f}"

async def enviar_resposta(telefone, mensagem):
    headers = {
        "Authorization": f"Bearer {WPP_TOKEN}",
        "Content-Type": "application/json"
    }
    body = {
        "messaging_product": "whatsapp",
        "to": telefone,
        "type": "text",
        "text": {"body": mensagem}
    }
    async with httpx.AsyncClient() as client:
        r = await client.post(GRAPH_URL, headers=headers, json=body)
        print("Resposta API:", r.status_code, r.text)
