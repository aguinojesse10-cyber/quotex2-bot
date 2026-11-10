import time
import requests
import pandas as pd
import yfinance as yf

# Configurações do Telegram
TOKEN = "9253894531:AAH5aGX58RSiblErf_dRrll5zxCoq3FXdv0"
CHAT_ID = "9005778571"

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

todos_ativos = [
    "EURUSD=X", "GBPUSD=X", "USDJPY=X", "AUDUSD=X", "USDCAD=X", 
    "NZDUSD=X", "EURGBP=X", "EURJPY=X", "GBPJPY=X", "AUDJPY=X", 
    "CHFJPY=X", "EURCHF=X", "AUDCAD=X", "EURAUD=X", "GBPCAD=X",
    "BTC-USD", "ETH-USD", "SOL-USD", "XRP-USD"
]

def carregar_dados(ticker):
    try:
        df = yf.download(ticker, period="1d", interval="1m", progress=False)
        if df.empty or len(df) < 30:
            return None
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        df = df.reset_index()
        df = df.rename(columns={
            'Open': 'open', 'High': 'high', 'Low': 'low', 
            'Close': 'close', 'Volume': 'volume'
        })
        return df[['open', 'high', 'low', 'close', 'volume']]
    except:
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

print("Bot de Alertas Quotex iniciado...")
enviar_telegram("🤖 *Bot Quotex 1M Online!* A monitorizar o mercado em segundo plano.")

# Registo para evitar enviar repetidamente o mesmo sinal na mesma vela
sinais_enviados = {}

while True:
    for ticker in todos_ativos:
        df = carregar_dados(ticker)
        if df is None:
            continue
            
        df = calcular_indicadores(df)
        ultimo = df.iloc[-1]
        
        preco = float(ultimo['close'])
        rsi = float(ultimo['RSI'])
        ema9 = float(ultimo['EMA_9'])
        ema21 = float(ultimo['EMA_21'])
        macd_hist = float(ultimo['MACD_Hist'])
        
        casas = 5 if "=X" in ticker else 2
        nome_quotex = ticker.replace("-USD", "/USD").replace("=X", "")
        if len(nome_quotex) == 6 and "/" not in nome_quotex:
            nome_quotex = nome_quotex[:3] + "/" + nome_quotex[3:]

        # Lógica de oportunidade perfeita
        estado_atual = None
        if rsi <= 46 and ema9 > ema21 and macd_hist > 0:
            estado_atual = "🟢 COMPRA (CALL)"
        elif rsi >= 54 and ema9 < ema21 and macd_hist < 0:
            estado_atual = "🔴 VENDA (PUT)"

        # Se encontrou sinal e ainda não notificou para este ativo recentemente
        if estado_atual:
            chave_sinal = f"{nome_quotex}_{estado_atual}"
            if sinais_enviados.get(nome_quotex) != estado_atual:
                sinais_enviados[nome_quotex] = estado_atual
                
                mensagem = (
                    f"🚨 *OPORTUNIDADE PERFEITA (1M)* 🚨\n\n"
                    f"📊 Ativo: *{nome_quotex}*\n"
                    f"🎯 Sinal: *{estado_atual}*\n"
                    f"💵 Preço: `{preco:.{casas}f}`\n"
                    f"📈 RSI: `{rsi:.1f}` | MACD: `{macd_hist:.{casas}f}`\n\n"
                    f"⏰ *Expiração sugerida:* 1 a 3 minutos"
                )
                enviar_telegram(mensagem)
        else:
            # Reseta se o mercado voltar a ficar neutro
            sinais_enviados[nome_quotex] = None

    # Aguarda 60 segundos antes de fazer uma nova varredura global
    time.sleep(60)
