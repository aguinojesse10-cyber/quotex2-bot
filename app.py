import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import time
from datetime import datetime

# Configuração da Página Streamlit
st.set_page_config(
    page_title="Scanner de Oportunidades 1M",
    page_icon="⚡",
    layout="centered"
)

st.markdown("""
    <style>
    .main { background-color: #0f172a; color: #f8fafc; }
    .stApp { background-color: #0f172a; }
    </style>
""", unsafe_allow_html=True)

st.title("⚡ Scanner de Oportunidades 1M")
st.write("A varrer o mercado em tempo real em busca de entradas perfeitas.")

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

st.subheader("🎯 Oportunidades Perfeitas (1M)")
placeholder_oportunidades = st.empty()

st.subheader("📊 Demais Pares Analisados")
placeholder_pares = st.empty()

# Loop de atualização contínua no Streamlit
while True:
    oportunidades_encontradas = []
    estado_pares = []
    
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
            
            nome_quotex = ticker.replace("-USD", "/USD").replace("=X", "")
            if len(nome_quotex) == 6 and "/" not in nome_quotex:
                nome_quotex = nome_quotex[:3] + "/" + nome_quotex[3:]
            
            casas = 5 if "=X" in ticker else 2
            
            # Verificar tendência/estado para a lista geral
            if rsi <= 46 and ema9 > ema21 and macd_hist > 0:
                sinal_tipo = "🟢 COMPRA (CALL)"
                oportunidades_encontradas.append({
                    'ativo': nome_quotex,
                    'tipo': sinal_tipo,
                    'preco': f"{preco:.{casas}f}",
                    'rsi': f"{rsi:.1f}",
                    'entrada': "Próxima Vela (Abertura)",
                    'expiracao': "1 Minuto (M1)"
                })
            elif rsi >= 54 and ema9 < ema21 and macd_hist < 0:
                sinal_tipo = "🔴 VENDA (PUT)"
                oportunidades_encontradas.append({
                    'ativo': nome_quotex,
                    'tipo': sinal_tipo,
                    'preco': f"{preco:.{casas}f}",
                    'rsi': f"{rsi:.1f}",
                    'entrada': "Próxima Vela (Abertura)",
                    'expiracao': "1 Minuto (M1)"
                })
            else:
                estado_pares.append(f"• **{nome_quotex}** — Preço: `{preco:.{casas}f}` | RSI: `{rsi:.1f}` | ⚪ Neutro / Aguardar")
                
        except Exception as e:
            continue

    # Atualizar o painel de Oportunidades no Streamlit
    with placeholder_oportunidades.container():
        if oportunidades_encontradas:
            for op in oportunidades_encontradas:
                st.success(
                    f"**{op['tipo']}** em **{op['ativo']}**\n\n"
                    f"⏰ **Momento da Entrada:** {op['entrada']}\n"
                    f"⏳ **Tempo de Expiração:** {op['expiracao']}\n"
                    f"💵 Preço de Referência: `{op['preco']}` | RSI: `{op['rsi']}`"
                )
        else:
            st.info("🔍 A varrer o mercado... Nenhum par atingiu o gatilho perfeito neste exato minuto. Aguarde a próxima atualização (30s).")

    # Atualizar o painel de Demais Pares no Streamlit
    with placeholder_pares.container():
        for linha in estado_pares:
            st.markdown(linha)
            
    time.sleep(30)
    
