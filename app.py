import streamlit as st
import pandas as pd
import yfinance as yf

# Configuração da página para ficar otimizada no telemóvel
st.set_page_config(page_title="Painel Quotex 1M", layout="centered")

st.title("⚡ Painel de Sinais 1M - Quotex")
st.markdown("Monitorização em tempo real de Cripto e Forex para velas de 1 minuto.")

# Lista de ativos
ativos = [
    "BTC-USD", "ETH-USD", "SOL-USD", "XRP-USD",
    "EURUSD=X", "GBPUSD=X", "USDJPY=X", "AUDUSD=X"
]

@st.cache_data(ttl=30) # Atualiza os dados a cada 30 segundos automaticamente
def carregar_dados(ticker):
    try:
        df = yf.download(ticker, period="1d", interval="1m", progress=False)
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

# Botão para forçar a atualização manual do mercado
if st.button("🔄 Atualizar Mercado Agora"):
    st.cache_data.clear()

st.markdown("---")

# Varre e mostra o painel de cada ativo em tempo real
for ticker in ativos:
    df = carregar_dados(ticker)
    if df is None or len(df) < 30:
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

    # Analisa a tendência para velas de 1 minuto
    if rsi < 48 and ema9 > ema21 and macd_hist > 0:
        status = "🟢 COMPRA (CALL)"
    elif rsi > 52 and ema9 < ema21 and macd_hist < 0:
        status = "🔴 VENDA (PUT)"
    else:
        status = "⚪ NEUTRO / AGUARDAR"

    # Exibe o card visual limpo para o telemóvel
    st.subheader(f"📊 {nome_quotex}")
    st.markdown(f"""
    * **Preço:** `{preco:.{casas}f}`
    * **Sinal 1M:** **{status}**
    * **RSI:** `{rsi:.2f}` | **MACD:** `{macd_hist:.{casas}f}`
    * **Expiração Sugerida:** `1 a 3 minutos`
    """)
    st.markdown("---")
