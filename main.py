import os
import pandas as pd
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import uvicorn

app = FastAPI()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")

planilhas = {
    "mg": pd.read_excel(os.path.join(DATA_DIR, "Tabelas - Matriz.xlsx")),
    "ba": pd.read_excel(os.path.join(DATA_DIR, "Tabela - Filial Feira.xlsx")),
    "pe": pd.read_excel(os.path.join(DATA_DIR, "Tabelas - Filial Caruaru.xlsx")),
    "go": pd.read_excel(os.path.join(DATA_DIR, "Tabelas - Filial Goiás.xlsx")),
}

@app.post("/webhook")
async def whatsapp_webhook(request: Request):
    try:
        body = await request.json()
        print("Webhook recebido:", body)

        mensagens = body["entry"][0]["changes"][0]["value"].get("messages")
        if not mensagens:
            return JSONResponse(content={"status": "ignorado"}, status_code=200)

        msg = mensagens[0]["text"]["body"].lower()
        telefone = mensagens[0]["from"]

        # Extrair código do produto e estado (uf) da mensagem
        import re
        codigo_match = re.search(r"\d{3,}", msg)
        estado_match = re.search(r"\b(mg|ba|pe|go)\b", msg)

        if not codigo_match or not estado_match:
            resposta = "Por favor, envie no formato: 'Qual o valor do produto [código] em [uf]'"
        else:
            codigo = int(codigo_match.group())
            regiao = estado_match.group()
            df = planilhas[regiao]

            resultado = df[df["seqproduto"] == codigo]

            if resultado.empty:
                resposta = f"Produto {codigo} não encontrado para {regiao.upper()}."
            else:
                preco = resultado["preco"].values[0]
                resposta = f"O valor do produto {codigo} em {regiao.upper()} é R$ {float(preco):.2f}"

        # Apenas imprime no console
        print(f"Resposta para {telefone}: {resposta}")
        return JSONResponse(content={"status": "mensagem recebida"}, status_code=200)

    except Exception as e:
        print("Erro ao processar webhook:", e)
        return JSONResponse(content={"erro": str(e)}, status_code=500)

@app.get("/status")
def status():
    return {"status": "ok"}

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
