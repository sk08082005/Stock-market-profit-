"""
BASIC STOCK ANALYZER
---------------------
Ye script kisi bhi stock ka data laata hai, uske upar 2 basic
indicators (Moving Average aur RSI) calculate karta hai, aur
ek simple BUY/SELL/HOLD signal deta hai.

Kaise chalayein:
1. Neeche "STOCK_NAME" wali line mein apna stock symbol daalo
2. Terminal mein likho: python stock_analyzer.py
3. Result terminal mein dikhega aur ek graph khulega
"""

import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt

# ---------- STEP 1: YAHAN APNA STOCK NAME DAALO ----------
# NSE (India) stocks ke liye symbol ke aage ".NS" lagana zaroori hai
# Example: Reliance -> "RELIANCE.NS", TCS -> "TCS.NS", Infosys -> "INFY.NS"
STOCK_NAME = "RELIANCE.NS"

# Kitne purane data se analysis karni hai
START_DATE = "2023-01-01"
END_DATE = "2024-12-31"


def get_stock_data(symbol, start, end):
    """Yahoo Finance se stock ka historical data laata hai"""
    print(f"\n{symbol} ka data download ho raha hai...")
    data = yf.download(symbol, start=start, end=end, progress=False)
    return data


def calculate_moving_averages(data):
    """50-din aur 200-din ka moving average (trend) nikaalta hai"""
    data["MA50"] = data["Close"].rolling(window=50).mean()
    data["MA200"] = data["Close"].rolling(window=200).mean()
    return data


def calculate_rsi(data, period=14):
    """
    RSI (Relative Strength Index) nikaalta hai.
    RSI batata hai ki stock 'overbought' (mehenga ho chuka) hai
    ya 'oversold' (sasta ho chuka) hai.
    - RSI 70 se upar = Overbought (girne ke chances)
    - RSI 30 se neeche = Oversold (badhne ke chances)
    """
    delta = data["Close"].diff()
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)

    avg_gain = gain.rolling(window=period).mean()
    avg_loss = loss.rolling(window=period).mean()

    rs = avg_gain / avg_loss
    data["RSI"] = 100 - (100 / (1 + rs))
    return data


def generate_signal(data):
    """
    Sabse latest din ke data ke basis pe ek simple signal deta hai.
    Ye ek BASIC logic hai, isse real trading ke liye 100% mat maano —
    isse sirf seekhne aur test karne ke liye use karo.
    """
    latest = data.iloc[-1]
    ma50 = latest["MA50"]
    ma200 = latest["MA200"]
    rsi = latest["RSI"]
    price = latest["Close"]

    print("\n----- LATEST ANALYSIS -----")
    print(f"Current Price   : {price:.2f}")
    print(f"50-Day Average  : {ma50:.2f}")
    print(f"200-Day Average : {ma200:.2f}")
    print(f"RSI             : {rsi:.2f}")

    signal = "HOLD"
    if ma50 > ma200 and rsi < 70:
        signal = "BUY (uptrend hai aur abhi overbought nahi)"
    elif ma50 < ma200 and rsi > 30:
        signal = "SELL / AVOID (downtrend dikh raha hai)"
    elif rsi > 70:
        signal = "CAUTION (overbought — abhi mehenga ho chuka hai)"
    elif rsi < 30:
        signal = "WATCH (oversold — sasta ho chuka, dhyan se dekho)"

    print(f"\n>>> SIGNAL: {signal}")
    print("\n(Yaad rakho: ye sirf ek basic indicator-based signal hai,")
    print(" koi guarantee nahi hai. Apni research bhi zaroor karo.)")


def plot_chart(data, symbol):
    """Price aur moving averages ka graph banata hai"""
    plt.figure(figsize=(12, 6))
    plt.plot(data.index, data["Close"], label="Price", linewidth=1.5)
    plt.plot(data.index, data["MA50"], label="50-Day Average", linestyle="--")
    plt.plot(data.index, data["MA200"], label="200-Day Average", linestyle="--")
    plt.title(f"{symbol} - Price aur Moving Averages")
    plt.xlabel("Date")
    plt.ylabel("Price")
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig("stock_chart.png")
    print("\nGraph 'stock_chart.png' naam ki file mein save ho gaya hai.")


# ---------- MAIN PROGRAM (Yahan se chalna shuru hota hai) ----------
if __name__ == "__main__":
    df = get_stock_data(STOCK_NAME, START_DATE, END_DATE)

    if df.empty:
        print("Data nahi mila. Stock symbol check karo (jaise 'RELIANCE.NS').")
    else:
        # Naye yfinance version mein columns kabhi-kabhi
        # MultiIndex format mein aate hain, unhe simple bana rahe hain
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)

        df = calculate_moving_averages(df)
        df = calculate_rsi(df)
        generate_signal(df)
        plot_chart(df, STOCK_NAME)
