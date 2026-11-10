import streamlit as st
import pandas as pd
import yfinance as yf

# Configuração da página otimizada para telemóvel
st.set_page_config(page_title="Scanner Perfeito Quotex 1M", layout="centered")

# Atualização automática a cada 30 segundos
st.markdown(
    """
    <meta http-equiv="refresh" content="30">
    """,
    unsafe_allow_html=True
)

st.sidebar.title("⚙️ Configurações")
st.sidebar.markdown("🔄 **Auto-Refresh:** A cada 30s")
modo_compacto = st.sidebar.checkbox("Modo Flutuante / Compacto", value=True)

if modo_compacto:
    st.markdown("""
        <style>
            .block-container { padding-top: 1rem; padding-bottom: 1rem; padding-left: 0.5rem; padding-right: 0.5rem; }
            h1 { font-size: 1.3rem !important; }
            h3 { font-size: 1rem !important; }
        </style>
    """, unsafe_allow_html=True)

st.title("⚡ Scanner de Oportunidades 1M")
st.caption("A varrer o mercado em tempo real em busca de entradas perfeitas.")

# Lista abrangente de pares Forex globais e Cripto
todos_ativos = [
    "EURUSD=X", "GBPUSD=X", "USDJPY=X", "AUDUSD=X", "USDCAD=X", 
    "NZDUSD=X", "EURGBP=X", "EURJPY=X", "GBPJPY=X", "AUDJPY=X", 
    "CHFJPY=X", "EURCHF=X", "AUDCAD=X", "EURAUD=X", "GBPCAD=X",
    "BTC-USD", "ETH-USD", "SOL-USD", "XRP-USD"
]

@st.cache_data(ttl=20)
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

# Listas para separar os ativos encontrados
oportunidades = []
outros_analisados = []

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

    # Critério de Entrada Perfeita (Filtro Rigoroso de Tendência e Momentum)
    # Compra: RSI < 45 (sobrevendido leve / zona de arranque), EMA9 > EMA21, MACD positivo forte
    if rsi <= 46 and ema9 > ema21 and macd_hist > 0:
        status = "🟢 ENTRADA PERFEITA - COMPRA (CALL)"
        oportunidades.append((nome_quotex, preco, rsi, macd_hist, casas, status))
    # Venda: RSI > 54 (sobrecomprado leve / zona de queda), EMA9 < EMA21, MACD negativo forte
    elif rsi >= 54 and ema9 < ema21 and macd_hist < 0:
        status = "🔴 ENTRADA PERFEITA - VENDA (PUT)"
        oportunidades.append((nome_quotex, preco, rsi, macd_hist, casas, status))
    else:
        outros_analisados.append((nome_quotex, preco, rsi, macd_hist, casas, "⚪ Neutro / Aguardar"))

# SECÇÃO DE DESTAQUE: Oportunidades Perfeitas
st.subheader("🎯 Oportunidades Perfeitas (1M)")
if len(oportunidades) == 0:
    st.info("🔍 A varrer o mercado... Nenhum par atingiu o gatilho perfeito neste exato minuto. Aguarde a próxima atualização (30s).")
else:
    for item in oportunidades:
        nome, preco, rsi, macd_hist, casas, status = item
        st.markdown(f"""
        ### {nome}
        * **Sinal:** **{status}**
        * **Preço Atual:** `{preco:.{casas}f}`
        * **RSI:** `{rsi:.1f}` | **MACD Hist:** `{macd_hist:.{casas}f}`
        """)
        st.markdown("---")

# SECÇÃO SECUNDÁRIA: Restantes Pares Monitorizados
st.subheader("📊 Demais Pares Analisados")
for item in outros_analisados:
    nome, preco, rsi, macd_hist, casas, status = item
    st.markdown(f"""
    * **{nome}** — Preço: `{preco:.{casas}f}` | RSI: `{rsi:.1f}` | *{status}*
    """)
