import streamlit as st
import pandas as pd
import yfinance as yf

# Configuração da página otimizada para telemóvel
st.set_page_config(page_title="Painel Quotex 1M", layout="centered")

# Script para recarregar a página automaticamente a cada 30 segundos
st.markdown(
    """
    <meta http-equiv="refresh" content="30">
    """,
    unsafe_allow_html=True
)

# Barra lateral para controlos e personalização dinâmica
st.sidebar.title("⚙️ Configurações")
st.sidebar.markdown("🔄 **Auto-Refresh:** A cada 30s")

# Lista completa de pares populares de Forex (Quotex) e Cripto
todos_ativos = [
    "EURUSD=X", "GBPUSD=X", "USDJPY=X", "AUDUSD=X", 
    "USDCAD=X", "NZDUSD=X", "EURGBP=X", "EURJPY=X", 
    "GBPJPY=X", "AUDJPY=X", "BTC-USD", "ETH-USD", 
    "SOL-USD", "XRP-USD", "ADA-USD", "DOGE-USD"
]

# Multiselect dinâmico para o utilizador escolher o que quer ver
ativos_selecionados = st.sidebar.multiselect(
    "Escolha os Ativos a Analisar:",
    options=todos_ativos,
    default=["EURUSD=X", "GBPUSD=X", "USDJPY=X", "BTC-USD", "ETH-USD"]
)

modo_compacto = st.sidebar.checkbox("Modo Flutuante / Compacto", value=True)

if modo_compacto:
    st.markdown("""
        <style>
            .block-container { padding-top: 1rem; padding-bottom: 1rem; padding-left: 0.5rem; padding-right: 0.5rem; }
            h1 { font-size: 1.4rem !important; }
            h3 { font-size: 1rem !important; }
        </style>
    """, unsafe_allow_html=True)

st.title("⚡ Painel Dinâmico 1M - Quotex")
st.caption("Análise técnica em tempo real para velas de 1 minuto.")

@st.cache_data(ttl=20)
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

st.markdown("---")

if not ativos_selecionados:
    st.warning("⚠️ Selecione pelo menos um ativo na barra lateral para ver as análises.")
else:
    for ticker in ativos_selecionados:
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

        # Lógica de sinais 1M
        if rsi < 48 and ema9 > ema21 and macd_hist > 0:
            status = "🟢 COMPRA (CALL)"
        elif rsi > 52 and ema9 < ema21 and macd_hist < 0:
            status = "🔴 VENDA (PUT)"
        else:
            status = "⚪ NEUTRO"

        st.subheader(f"📊 {nome_quotex}")
        st.markdown(f"""
        * Preço: `{preco:.{casas}f}` | Sinal: **{status}**
        * RSI: `{rsi:.1f}` | MACD: `{macd_hist:.{casas}f}`
        """)
        st.markdown("---")
