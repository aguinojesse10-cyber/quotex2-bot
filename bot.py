import os
import pandas as pd
import yfinance as yf
import requests

# Lê as credenciais de forma segura a partir do GitHub
TOKEN = os.environ.get("TELEGRAM_TOKEN")
CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

def enviar_telegram(mensagem):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": mensagem,
        "parse_mode": "Markdown"
    }
    try:
        requests.post(url, json=payload)
    except Exception as e:
        print(f"Erro ao enviar: {e}")

def buscar_dados(ticker, interval="1h", period="5d"):
    try:
        df = yf.download(ticker, period=period, interval=interval, progress=False)
        if df.empty:
            return None
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        df = df.reset_index()
        df = df.rename(columns={
            'Open': 'open', 'High': 'high', 'Low': 'low', 
            'Close': 'close', 'Volume': 'volume'
        })
        return df[['open', 'high', 'low', 'close', 'volume']]
    except Exception as e:
        print(f"Erro em {ticker}: {e}")
        return None

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

ativos_totais = [
    "BTC-USD", "ETH-USD", "SOL-USD", "XRP-USD",
    "EURUSD=X", "GBPUSD=X", "USDJPY=X", "AUDUSD=X"
]

def analisar_para_quotex():
    for ticker in ativos_totais:
        df = buscar_dados(ticker)
        if df is None or len(df) < 30:
            continue

        df = calcular_indicadores(df)
        ultimo = df.iloc[-1]
        preco_atual = float(ultimo['close'])
        rsi_atual = float(ultimo['RSI'])
        ema9 = float(ultimo['EMA_9'])
        ema21 = float(ultimo['EMA_21'])
        macd_hist = float(ultimo['MACD_Hist'])
        
        casas = 5 if "=X" in ticker else 2
        ativo_quotex = ticker.replace("-USD", "/USD").replace("=X", "")
        if len(ativo_quotex) == 6 and "/" not in ativo_quotex:
            ativo_quotex = ativo_quotex[:3] + "/" + ativo_quotex[3:]

        if rsi_atual < 48 and ema9 > ema21 and macd_hist > 0:
            sinal = (
                f"🟢 *SINAL QUOTEX: COMPRA (CALL)* 🟢\n\n"
                f"🎯 **Ativo:** `{ativo_quotex}`\n"
                f"💵 **Preço Atual:** `{preco_atual:.{casas}f}`\n"
                f"⏱️ **Expiração Sugerida:** `15 a 30 minutos`\n\n"
                f"📈 RSI: `{rsi_atual:.2f}` | MACD: `{macd_hist:.{casas}f}`\n"
                f"📉 EMA9 (`{ema9:.{casas}f}`) > EMA21 (`{ema21:.{casas}f}`)\n"
                f"-----------------------------------\n"
                f"💡 *Ação:* Abrir posição de ALTA na Quotex!"
            )
            enviar_telegram(sinal)
            
        elif rsi_atual > 52 and ema9 < ema21 and macd_hist < 0:
            sinal = (
                f"🔴 *SINAL QUOTEX: VENDA (PUT)* 🔴\n\n"
                f"🎯 **Ativo:** `{ativo_quotex}`\n"
                f"💵 **Preço Atual:** `{preco_atual:.{casas}f}`\n"
                f"⏱️ **Expiração Sugerida:** `15 a 30 minutos`\n\n"
                f"📈 RSI: `{rsi_atual:.2f}` | MACD: `{macd_hist:.{casas}f}`\n"
                f"📉 EMA9 (`{ema9:.{casas}f}`) < EMA21 (`{ema21:.{casas}f}`)\n"
                f"-----------------------------------\n"
                f"💡 *Ação:* Abrir posição de BAIXA na Quotex!"
            )
            enviar_telegram(sinal)

if __name__ == "__main__":
    analisar_para_quotex()
