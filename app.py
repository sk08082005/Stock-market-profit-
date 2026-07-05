"""
STOCK ANALYZER - WEB VERSION (Stage 1)
----------------------------------------
Ye ek website jaisa page banata hai (browser mein khulta hai) jahan
tum koi bhi stock ka naam type karke uska analysis dekh sakte ho.
Code edit karne ki zaroorat nahi hai.

Kaise chalayein:
1. Terminal mein likho: pip install streamlit yfinance pandas
2. Fir likho: streamlit run app.py
3. Browser automatically khul jayega (ya link terminal mein milega)

Agle steps mein hum isme add karenge:
- Backtesting (purani strategy test karna)
- Risk management (stop-loss, position sizing)
- Aur indicators (Volume, MACD)
"""

import streamlit as st
import yfinance as yf
import pandas as pd

# ---------- PAGE SETUP ----------
st.set_page_config(page_title="Stock Analyzer", layout="centered")
st.title("📈 Stock Analyzer")
st.write("Kisi bhi stock ka naam daalo aur uska basic analysis dekho.")

# ---------- USER INPUT (search box) ----------
stock_input = st.text_input(
    "Stock symbol daalo (Indian stocks ke liye .NS lagao)",
    value="RELIANCE.NS",
    help="Example: RELIANCE.NS, TCS.NS, INFY.NS, TATASTEEL.NS",
)

col1, col2 = st.columns(2)
with col1:
    start_date = st.date_input("Start Date", value=pd.to_datetime("2023-01-01"))
with col2:
    end_date = st.date_input("End Date", value=pd.to_datetime("2024-12-31"))

analyze_button = st.button("Analyze Karo")


# ---------- CALCULATION FUNCTIONS ----------
def calculate_moving_averages(data):
    data["MA50"] = data["Close"].rolling(window=50).mean()
    data["MA200"] = data["Close"].rolling(window=200).mean()
    return data


def calculate_rsi(data, period=14):
    delta = data["Close"].diff()
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)
    avg_gain = gain.rolling(window=period).mean()
    avg_loss = loss.rolling(window=period).mean()
    rs = avg_gain / avg_loss
    data["RSI"] = 100 - (100 / (1 + rs))
    return data


def get_signal(latest):
    ma50 = latest["MA50"]
    ma200 = latest["MA200"]
    rsi = latest["RSI"]

    if ma50 > ma200 and rsi < 70:
        return "BUY", "Uptrend hai aur abhi overbought nahi", "green"
    elif ma50 < ma200 and rsi > 30:
        return "SELL / AVOID", "Downtrend dikh raha hai", "red"
    elif rsi > 70:
        return "CAUTION", "Overbought - abhi mehenga ho chuka hai", "orange"
    elif rsi < 30:
        return "WATCH", "Oversold - sasta ho chuka, dhyan se dekho", "blue"
    else:
        return "HOLD", "Koi strong signal nahi abhi", "gray"


# ---------- MAIN LOGIC (jab button dabaya jaye) ----------
if analyze_button:
    if not stock_input:
        st.error("Pehle stock ka naam daalo.")
    else:
        with st.spinner(f"{stock_input} ka data laaya ja raha hai..."):
            data = yf.download(stock_input, start=start_date, end=end_date, progress=False)

        if data.empty:
            st.error("Data nahi mila. Stock symbol check karo (jaise 'RELIANCE.NS').")
        else:
            # Naye yfinance version mein columns kabhi-kabhi
            # MultiIndex format mein aate hain, unhe simple bana rahe hain
            if isinstance(data.columns, pd.MultiIndex):
                data.columns = data.columns.get_level_values(0)

            data = calculate_moving_averages(data)
            data = calculate_rsi(data)
            latest = data.iloc[-1]

            # ---- Metrics dikhana ----
            st.subheader("Latest Analysis")
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Current Price", f"{latest['Close']:.2f}")
            m2.metric("50-Day Avg", f"{latest['MA50']:.2f}")
            m3.metric("200-Day Avg", f"{latest['MA200']:.2f}")
            m4.metric("RSI", f"{latest['RSI']:.2f}")

            # ---- Signal dikhana ----
            signal, reason, color = get_signal(latest)
            st.markdown(f"### Signal: :{color}[{signal}]")
            st.write(reason)
            st.warning(
                "Ye sirf basic indicators (MA + RSI) pe based signal hai. "
                "Real paisa lagane se pehle apni research zaroor karo — "
                "koi bhi tool guaranteed profit nahi de sakta."
            )

            # ---- Chart dikhana ----
            st.subheader("Price Chart")
            chart_data = data[["Close", "MA50", "MA200"]].dropna()
            st.line_chart(chart_data)

            # ---- Raw data (optional dekhne ke liye) ----
            with st.expander("Raw data dekhna ho toh yahan click karo"):
                st.dataframe(data.tail(20))
