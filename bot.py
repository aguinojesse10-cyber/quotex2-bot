import time
import threading
import os
import requests
import yfinance as yf
import pandas as pd
import numpy as np
from flask import Flask

# Servidor Flask para manter o Render acordado
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot Quotex 1M Online com Pré-Alerta Ajustado!"

def correr_flask():
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)

# Credenciais do Telegram validadas
TOKEN = "9160642609:AAETghLIx8PbcWOe7YfSFe411MKmcYIABcY"
CHAT_ID = "9005778571"

def enviar_telegram(mensagem):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": mensagem,
        "parse_mode": "Markdown"
    }
    try:
        response = requests.post(url, json=payload, timeout=10)
        print(f"Telegram Status: {response.status_code}", flush=True)
    except Exception as e:
        print(f"Erro no Telegram: {e}", flush=True)

TODOS_ATIVOS = [
    "EURUSD=X", "GBPUSD=X", "USDJPY=X", "AUDUSD=X", "USDCAD=X", 
    "NZDUSD=X", "EURGBP=X", "EURJPY=X", "GBPJPY=X", "AUDJPY=X", 
    "CHFJPY=X", "EURCHF=X", "AUDCAD=X", "EURAUD=X", "GBPCAD=X",
    "BTC-USD", "ETH-USD", "SOL-USD", "XRP-USD"
]

# Dicionário para controlar os pré-alertas e evitar spam no mesmo ativo
estado_pre_alerta = {}

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
    print(">>> BOT INICIADO COM SUCESSO (PRÉ-ALERTA AJUSTADO) <<<", flush=True)
    enviar_telegram("🤖 *Bot Quotex 1M Online!* Sistema de Pré-Alerta refinado ativado.")
    
    while True:
        try:
            for ticker in TODOS_ATIVOS:
                try:
                    df = yf.download(ticker, period="1d", interval="1m", progress=False)
                    if df.empty or len(df) < 35:
                        continue
                    
                    if isinstance(df.columns, pd.MultiIndex):
                        df.columns = df.columns.get_level_values(0)
                        
                    df = df.reset_index().rename(columns={
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

                    if ticker not in estado_pre_alerta:
                        estado_pre_alerta[ticker] = None

                    # ---------------------------------------------------------
                    # 1. LÓGICA DE PRÉ-ALERTA (Janela muito próxima do gatilho)
                    # ---------------------------------------------------------
                    # Pré-alerta de Compra (RSI entre 40.1 e 41.5)
                    if 40.1 <= rsi <= 41.5 and ema9 > ema21 and estado_pre_alerta[ticker] != 'COMPRA':
                        msg_pre = (
                            f"⚠️ *PREPARA O PAR - COMPRA*\n\n"
                            f"📊 Ativo: `{nome_quotex}`\n"
                            f"📈 RSI Muito Perto da Zona: `{rsi:.1f}`\n"
                            f"👉 *Abre já a Quotex, o tiro pode sair na próxima vela!*"
                        )
                        enviar_telegram(msg_pre)
                        estado_pre_alerta[ticker] = 'COMPRA'

                    # Pré-alerta de Venda (RSI entre 58.5 e 59.9)
                    elif 58.5 <= rsi <= 59.9 and ema9 < ema21 and estado_pre_alerta[ticker] != 'VENDA':
                        msg_pre = (
                            f"⚠️ *PREPARA O PAR - VENDA*\n\n"
                            f"📊 Ativo: `{nome_quotex}`\n"
                            f"📉 RSI Muito Perto da Zona: `{rsi:.1f}`\n"
                            f"👉 *Abre já a Quotex, o tiro pode sair na próxima vela!*"
                        )
                        enviar_telegram(msg_pre)
                        estado_pre_alerta[ticker] = 'VENDA'

                    # ---------------------------------------------------------
                    # 2. LÓGICA DE SINAL DEFINITIVO (Filtros Rigorosos)
                    # ---------------------------------------------------------
                    # Sinal de Compra
                    if rsi <= 40 and ema9 > ema21 and macd_hist > 0.00005:
                        resultado = "✅ GREEN (WIN)" if preco_seguinte > preco else "❌ RED (LOSS)"
                        msg = (
                            f"🟢 *ENTRADA DE ALTA PRECISÃO - COMPRA (CALL)*\n\n"
                            f"📊 Ativo: `{nome_quotex}`\n"
                            f"⏰ Entrada: *PRÓXIMA VELA (Abertura)*\n"
                            f"⏳ Expiração: *1 MINUTO (M1)*\n"
                            f"💵 Preço de Referência: `{preco:.{casas}f}`\n"
                            f"📈 RSI: `{rsi:.1f}` | MACD: `{macd_hist:.{casas}f}`\n\n"
                            f"🏁 Resultado: *{resultado}*"
                        )
                        enviar_telegram(msg)
                        estado_pre_alerta[ticker] = None

                    # Sinal de Venda
                    elif rsi >= 60 and ema9 < ema21 and macd_hist < -0.00005:
                        resultado = "✅ GREEN (WIN)" if preco_seguinte < preco else "❌ RED (LOSS)"
                        msg = (
                            f"🔴 *ENTRADA DE ALTA PRECISÃO - VENDA (PUT)*\n\n"
                            f"📊 Ativo: `{nome_quotex}`\n"
                            f"⏰ Entrada: *PRÓXIMA VELA (Abertura)*\n"
                            f"⏳ Expiração: *1 MINUTO (M1)*\n"
                            f"💵 Preço de Referência: `{preco:.{casas}f}`\n"
                            f"📉 RSI: `{rsi:.1f}` | MACD: `{macd_hist:.{casas}f}`\n\n"
                            f"🏁 Resultado: *{resultado}*"
                        )
                        enviar_telegram(msg)
                        estado_pre_alerta[ticker] = None
                    
                    # Limpa o estado se o preço afastar-se
                    elif 45 < rsi < 55:
                        estado_pre_alerta[ticker] = None

                    time.sleep(1)
                except Exception as e:
                    continue
            time.sleep(15)
        except Exception as e:
            print(f"Erro geral no loop: {e}", flush=True)
            time.sleep(10)

if __name__ == "__main__":
    t_flask = threading.Thread(target=correr_flask)
    t_flask.daemon = True
    t_flask.start()
    
    monitorizar_mercado()
    
