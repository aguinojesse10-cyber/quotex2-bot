import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np

# Configuração da página do Streamlit
st.set_page_config(page_title="Scanner de Oportunidades 1M", page_icon="⚡", layout="centered")

st.markdown("## ⚡ Scanner de Oportunidades 1M")
st.write("A varrer o mercado em tempo real em busca de entradas perfeitas.")

# Lista exata de ativos monitorizados pelo bot
PARES = [
    "EURUSD=X", "GBPUSD=X", "USDJPY=X", "AUDUSD=X", "USDCAD=X", 
    "USDCHF=X", "NZDUSD=X", "EURGBP=X", "EURJPY=X", "GBPJPY=X",
    "AUDJPY=X", "EURAUD=X", "EURNZD=X", "GBPAUD=X", "GBPNZD=X",
    "CHFJPY=X", "CADJPY=X", "AUDNZD=X", "BTC-USD", "ETH-USD"
]

def calcular_indicadores(df):
    df['EMA9'] = df['Close'].ewm(span=9, adjust=False).mean()
    df['EMA21'] = df['Close'].ewm(span=21, adjust=False).mean()
    
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    df['RSI'] = 100 - (100 / (1 + rs))
    
    exp1 = df['Close'].ewm(span=12, adjust=False).mean()
    exp2 = df['Close'].ewm(span=26, adjust=False).mean()
    df['MACD'] = exp1 - exp2
    df['MACD_Signal'] = df['MACD'].ewm(span=9, adjust=False).mean()
    df['MACD_Hist'] = df['MACD'] - df['MACD_Signal']
    
    return df

# Botão para atualizar a análise manualmente no painel
if st.button("🔄 Atualizar Análise Agora"):
    st.rerun()

st.markdown("---")
st.markdown("### 🎯 Oportunidades Perfeitas (1M)")

tem_oportunidade = False

for par in PARES:
    try:
        dados = yf.download(par, period="1d", interval="1m", progress=False)
        if dados.empty or len(dados) < 30:
            continue
            
        if isinstance(dados.columns, pd.MultiIndex):
            dados.columns = dados.columns.get_level_values(0)
            
        df = calcular_indicadores(dados)
        atual = df.iloc[-2]
        
        preco = float(atual['Close'])
        rsi = float(atual['RSI'])
        ema9 = float(atual['EMA9'])
        ema21 = float(atual['EMA21'])
        macd_hist = float(atual['MACD_Hist'])
        
        nome_ativo = par.replace("=X", "").replace("-USD", "/USD")
        
        # Verifica se cumpre a estratégia de Compra (CALL)
        if rsi < 35 and ema9 > ema21 and macd_hist > 0:
            tem_oportunidade = True
            st.success(f"**{nome_ativo}**\n\n"
                       f"• **Sinal:** 🟢 ENTRADA PERFEITA - COMPRA (CALL)\n"
                       f"• **Preço Atual:** `{preco:.5f}`\n"
                       f"• **RSI:** `{rsi:.1f}` | **MACD Hist:** `{macd_hist:.5f}`")
                       
        # Verifica se cumpre a estratégia de Venda (PUT)
        elif rsi > 65 and ema9 < ema21 and macd_hist < 0:
            tem_oportunidade = True
            st.error(f"**{nome_ativo}**\n\n"
                     f"• **Sinal:** 🔴 ENTRADA PERFEITA - VENDA (PUT)\n"
                     f"• **Preço Atual:** `{preco:.5f}`\n"
                     f"• **RSI:** `{rsi:.1f}` | **MACD Hist:** `{macd_hist:.5f}`")
                     
    except Exception:
        continue

if not tem_oportunidade:
    st.info("ℹ️ Sem alinhamento claro no momento. A monitorizar o mercado...")

st.markdown("---")
st.markdown("### 📊 Demais Pares Analisados")

# Secção resumida para mostrar que os outros pares estão a ser validados
for par in PARES:
    nome_ativo = par.replace("=X", "").replace("-USD", "/USD")
    st.write(f"• **{nome_ativo}** — Estado: A monitorizar")
