import time
import threading
import requests
import yfinance as yf
import pandas as pd
import numpy as np
from flask import Flask

# ================= SERVIDOR WEB PARA O RENDER NÃO ADORMECER =================
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot Quotex 1M a funcionar a todo o vapor!"

def run_flask():
    app.run(host='0.0.0.0', port=10000)

# ================= CONFIGURAÇÕES DO TELEGRAM =================
TOKEN = "7950796339:AAESd5H2HlJmFfS5X2w4p7k1L8m9N0v3Q2w"
CHAT_ID = "6172559092"

def enviar_telegram(mensagem):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": mensagem,
        "parse_mode": "Markdown"
    }
    try:
        response = requests.post(url, json=payload, timeout=10)
        if response.status_code == 200:
            print("Mensagem enviada com sucesso para o Telegram!")
        else:
            print(f"Erro ao enviar para o Telegram: {response.text}")
    except Exception as e:
        print(f"Exceção ao enviar mensagem: {e}")

# ================= LISTA DE ATIVOS =================
TODOS_ATIVOS = [
    "EURUSD=X", "GBPUSD=X", "USDJPY=X", "AUDUSD=X", "USDCAD=X", 
    "NZDUSD=X", "EURGBP=X", "EURJPY=X", "GBPJPY=X", "AUDJPY=X", 
    "CHFJPY=X", "EURCHF=X", "AUDCAD=X", "EURAUD=X", "GBPCAD=X",
    "BTC-USD", "ETH-USD", "SOL-USD", "XRP-USD"
]

def calcular_indicadores(df):
    df['EMA_9'] = df['close'].ewm(span=9, adjust=False).mean()
    df['EMA_21'] = df['close'].ewm(span=21, adjust=False).mean()
    
    delta = df['close'].diff()
    ganho = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    perda = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = ganho / perda
    df['RSI'] = 100 - (100 / (1 + rs))
    
    exp12 = df['close'].ewm(span=12, adjust=False).mean()
    exp26 = df['close'].ewm(span=26, adjust=False).mean()
    df['MACD'] = exp12 - exp26
    df['MACD_Signal'] = df['MACD'].ewm(span=9, adjust=False).mean()
    df['MACD_Hist'] = df['MACD'] - df['MACD_Signal']
    
    return df

def monitorizar_mercado():
    print("🤖 Bot Quotex 1M iniciado com sucesso na nuvem.")
    enviar_telegram("🤖 *Bot Quotex 1M Online!* A monitorizar o mercado 24/7.")
    
    while True:
        for ticker in TODOS_ATIVOS:
            try:
                df = yf.download(ticker, period="1d", interval="1m", progress=False)
                if df.empty or len(df) < 35:
                    continue
                
                if isinstance(df.columns, pd.MultiIndex):
                    df.columns = df.columns.get_level_values(0)
                    
                df = df.reset_index()
                df = df.rename(columns={
                    'Open': 'open', 'High': 'high', 'Low': 'low', 
                    'Close': 'close', 'Volume': 'volume'
                })
                
                df = calcular_indicadores(df)
                
                anterior = df.iloc[-2]
                atual = df.iloc[-1]
                
                preco = float(anterior['close'])
                rsi = float(anterior['RSI'])
                ema9 = float(anterior['EMA_9'])
                ema21 = float(anterior['EMA_21'])
                macd_hist = float(anterior['MACD_Hist'])
                
                preco_seguinte = float(atual['close'])
                
                nome_quotex = ticker.replace("-USD", "/USD").replace("=X", "")
                if len(nome_quotex) == 6 and "/" not in nome_quotex:
                    nome_quotex = nome_quotex[:3] + "/" + nome_quotex[3:]
                
                casas = 5 if "=X" in ticker else 2

                # ================= LÓGICA DE ENTRADA =================
                # COMPRA (CALL)
                if rsi <= 46 and ema9 > ema21 and macd_hist > 0:
                    resultado = "✅ GREEN (WIN)" if preco_seguinte > preco else "❌ RED (LOSS)"
                    
                    mensagem = (
                        f"🟢 *ENTRADA PERFEITA - COMPRA (CALL)*\n\n"
                        f"📊 Ativo: `{nome_quotex}`\n"
                        f"💵 Preço Entrada: `{preco:.{casas}f}`\n"
                        f"📈 RSI: `{rsi:.1f}` | MACD Hist: `{macd_hist:.{casas}f}`\n"
                        f"🏁 Resultado (Vela Seguinte): *{resultado}*"
                    )
                    enviar_telegram(mensagem)
                    print(f"Sinal de COMPRA detetado em {nome_quotex} -> Enviado para o Telegram.")

                # VENDA (PUT)
                elif rsi >= 54 and ema9 < ema21 and macd_hist < 0:
                    resultado = "✅ GREEN (WIN)" if preco_seguinte < preco else "❌ RED (LOSS)"
                    
                    mensagem = (
                        f"🔴 *ENTRADA PERFEITA - VENDA (PUT)*\n\n"
                        f"📊 Ativo: `{nome_quotex}`\n"
                        f"💵 Preço Entrada: `{preco:.{casas}f}`\n"
                        f"📉 RSI: `{rsi:.1f}` | MACD Hist: `{macd_hist:.{casas}f}`\n"
                        f"🏁 Resultado (Vela Seguinte): *{resultado}*"
                    )
                    enviar_telegram(mensagem)
                    print(f"Sinal de VENDA detetado em {nome_quotex} -> Enviado para o Telegram.")
                
                time.sleep(1)
                
            except Exception as e:
                print(f"Erro ao analisar {ticker}: {e}")
                continue
        
        time.sleep(15)

if __name__ == "__main__":
    # Inicia o servidor Flask numa thread separada para o Render aceitar o deploy
    t = threading.Thread(target=run_flask)
    t.daemon = True
    t.start()
    
    # Inicia a rotina de monitorização do mercado
    monitorizar_mercado()
