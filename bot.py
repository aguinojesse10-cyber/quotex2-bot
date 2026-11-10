import time
import requests
import yfinance as yf
import pandas as pd
import numpy as np

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
        requests.post(url, json=payload, timeout=10)
    except Exception as e:
        print(f"Erro ao enviar mensagem: {e}")

# ================= LISTA DE ATIVOS =================
PARES = [
    "EURUSD=X", "GBPUSD=X", "USDJPY=X", "AUDUSD=X", "USDCAD=X", 
    "USDCHF=X", "NZDUSD=X", "EURGBP=X", "EURJPY=X", "GBPJPY=X",
    "AUDJPY=X", "EURAUD=X", "EURNZD=X", "GBPAUD=X", "GBPNZD=X",
    "CHFJPY=X", "CADJPY=X", "AUDNZD=X", "BTC-USD", "ETH-USD"
]

def calcular_indicadores(df):
    # EMA 9 e EMA 21
    df['EMA9'] = df['Close'].ewm(span=9, adjust=False).mean()
    df['EMA21'] = df['Close'].ewm(span=21, adjust=False).mean()
    
    # RSI (14)
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    df['RSI'] = 100 - (100 / (1 + rs))
    
    # MACD Histograma
    exp1 = df['Close'].ewm(span=12, adjust=False).mean()
    exp2 = df['Close'].ewm(span=26, adjust=False).mean()
    df['MACD'] = exp1 - exp2
    df['MACD_Signal'] = df['MACD'].ewm(span=9, adjust=False).mean()
    df['MACD_Hist'] = df['MACD'] - df['MACD_Signal']
    
    return df

def monitorizar_mercado():
    enviar_telegram("🤖 *Bot Quotex 1M Online!* A monitorizar o mercado com validação automática de Win/Loss.")
    
    while True:
        for par in PARES:
            try:
                # Descarregar dados de 1 minuto
                dados = yf.download(par, period="1d", interval="1m", progress=False)
                
                if dados.empty or len(dados) < 30:
                    continue
                
                # Tratar multi-index do yfinance se houver
                if isinstance(dados.columns, pd.MultiIndex):
                    dados.columns = dados.columns.get_level_values(0)
                
                df = calcular_indicadores(dados)
                
                # Pegar na última vela fechada (penúltima linha, pois a última está a abrir)
                atual = df.iloc[-2]
                
                preco = float(atual['Close'])
                rsi = float(atual['RSI'])
                ema9 = float(atual['EMA9'])
                ema21 = float(atual['EMA21'])
                macd_hist = float(atual['MACD_Hist'])
                
                nome_ativo = par.replace("=X", "").replace("-USD", "/USD")
                
                # ================= LÓGICA DE ENTRADA =================
                # SINAL DE COMPRA (CALL): RSI < 35, EMA9 > EMA21 e MACD Histograma > 0
                if rsi < 35 and ema9 > ema21 and macd_hist > 0:
                    mensagem = (
                        f"🟢 *ENTRADA PERFEITA - COMPRA (CALL)*\n\n"
                        f"📊 Ativo: `{nome_ativo}`\n"
                        f"💵 Preço de Entrada: `$ {preco:.5f}`\n"
                        f"📈 RSI: `{rsi:.2f}` | Hist. MACD: `{macd_hist:.5f}`\n"
                        f"⏳ *Aguardando resultado da vela seguinte...*"
                    )
                    enviar_telegram(mensagem)
                    
                    # Esperar 65 segundos para a vela seguinte fechar e validar
                    time.sleep(65)
                    
                    # Verificar preço após 1 minuto
                    dados_pos = yf.download(par, period="1d", interval="1m", progress=False)
                    if isinstance(dados_pos.columns, pd.MultiIndex):
                        dados_pos.columns = dados_pos.columns.get_level_values(0)
                    
                    preco_final = float(dados_pos.iloc[-2]['Close'])
                    
                    if preco_final > preco:
                        enviar_telegram(f"✅ *RESULTADO: WIN (GREEN)* em `{nome_ativo}`!\nEntrada: `{preco:.5f}` -> Fecho: `{preco_final:.5f}`")
                    else:
                        enviar_telegram(f"❌ *RESULTADO: LOSS (RED)* em `{nome_ativo}`\nEntrada: `{preco:.5f}` -> Fecho: `{preco_final:.5f}`")

                # SINAL DE VENDA (PUT): RSI > 65, EMA9 < EMA21 e MACD Histograma < 0
                elif rsi > 65 and ema9 < ema21 and macd_hist < 0:
                    mensagem = (
                        f"🔴 *ENTRADA PERFEITA - VENDA (PUT)*\n\n"
                        f"📊 Ativo: `{nome_ativo}`\n"
                        f"💵 Preço de Entrada: `$ {preco:.5f}`\n"
                        f"📉 RSI: `{rsi:.2f}` | Hist. MACD: `{macd_hist:.5f}`\n"
                        f"⏳ *Aguardando resultado da vela seguinte...*"
                    )
                    enviar_telegram(mensagem)
                    
                    # Esperar 65 segundos para a vela seguinte fechar e validar
                    time.sleep(65)
                    
                    # Verificar preço após 1 minuto
                    dados_pos = yf.download(par, period="1d", interval="1m", progress=False)
                    if isinstance(dados_pos.columns, pd.MultiIndex):
                        dados_pos.columns = dados_pos.columns.get_level_values(0)
                    
                    preco_final = float(dados_pos.iloc[-2]['Close'])
                    
                    if preco_final < preco:
                        enviar_telegram(f"✅ *RESULTADO: WIN (GREEN)* em `{nome_ativo}`!\nEntrada: `{preco:.5f}` -> Fecho: `{preco_final:.5f}`")
                    else:
                        enviar_telegram(f"❌ *RESULTADO: LOSS (RED)* em `{nome_ativo}`\nEntrada: `{preco:.5f}` -> Fecho: `{preco_final:.5f}`")
                
                # Pausa pequena entre ativos para não sobrecarregar a API
                time.sleep(2)
                
            except Exception as e:
                print(f"Erro ao analisar {par}: {e}")
                continue
        
        # Pausa antes de reiniciar a varredura completa do mercado
        time.sleep(10)

if __name__ == "__main__":
    monitorizar_mercado()
