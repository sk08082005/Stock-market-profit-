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


def backtest_strategy(data, starting_capital=100000):
    """
    Strategy: Jab MA50, MA200 ke upar cross kare -> BUY (position = 1)
              Jab MA50, MA200 ke neeche cross kare -> SELL (position = 0)
    Isse compare karte hain agar tum sirf shuru mein khareed ke
    rakh dete (Buy & Hold) toh kya hota.
    """
    df = data.copy().dropna(subset=["MA50", "MA200"])

    # Position: 1 matlab stock hold kar rahe hain, 0 matlab cash mein baithe hain
    df["Position"] = 0
    df.loc[df["MA50"] > df["MA200"], "Position"] = 1

    # Daily return (stock kitna % badla/ghata roz)
    df["DailyReturn"] = df["Close"].pct_change()

    # Strategy return = sirf tab milta hai jab Position=1 (hold kar rahe the)
    # Position ko 1 din shift karte hain kyunki signal aaj mila,
    # trade kal execute hoga (real trading mein aisa hi hota hai)
    df["StrategyReturn"] = df["DailyReturn"] * df["Position"].shift(1)

    # Cumulative growth nikaalna (100000 se shuru karke)
    df["StrategyEquity"] = starting_capital * (1 + df["StrategyReturn"].fillna(0)).cumprod()
    df["BuyHoldEquity"] = starting_capital * (1 + df["DailyReturn"].fillna(0)).cumprod()

    # Trades kitni baar hui (position change hua)
    trades = df["Position"].diff().fillna(0)
    num_trades = int((trades != 0).sum())

    # Max Drawdown = sabse bada gira hua % peak se (risk samajhne ke liye)
    running_max = df["StrategyEquity"].cummax()
    drawdown = (df["StrategyEquity"] - running_max) / running_max
    max_drawdown = drawdown.min() * 100

    final_strategy = df["StrategyEquity"].iloc[-1]
    final_buyhold = df["BuyHoldEquity"].iloc[-1]

    strategy_return_pct = (final_strategy / starting_capital - 1) * 100
    buyhold_return_pct = (final_buyhold / starting_capital - 1) * 100

    results = {
        "strategy_final": final_strategy,
        "buyhold_final": final_buyhold,
        "strategy_return_pct": strategy_return_pct,
        "buyhold_return_pct": buyhold_return_pct,
        "num_trades": num_trades,
        "max_drawdown": max_drawdown,
    }
    return df, results


def find_last_crossovers(data):
    """Find last Golden Cross (MA50 > MA200) and Death Cross (MA50 < MA200) dates."""
    df = data.copy().dropna(subset=["MA50", "MA200"])
    if df.empty:
        return None, None
    cross_up = (df["MA50"] > df["MA200"]) & (df["MA50"].shift(1) <= df["MA200"].shift(1))
    cross_down = (df["MA50"] < df["MA200"]) & (df["MA50"].shift(1) >= df["MA200"].shift(1))
    up_df = df[cross_up]
    down_df = df[cross_down]
    last_g = up_df.index[-1] if len(up_df) > 0 else None
    last_d = down_df.index[-1] if len(down_df) > 0 else None
    return last_g, last_d


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

            # ---- Backtesting section ----
            st.subheader("📊 Backtest: Strategy vs Buy & Hold")
            st.caption(
                "Ye dikhata hai ki agar tum is strategy (MA50/MA200 crossover) ko "
                "follow karte pichle data mein, toh kitna paisa banta/ghatta — "
                "compare karke Buy & Hold (sirf khareed ke rakhna) se."
            )

            bt_data, results = backtest_strategy(data)

            b1, b2 = st.columns(2)
            b1.metric(
                "Strategy Return",
                f"{results['strategy_return_pct']:.2f}%",
                delta=f"₹{results['strategy_final']:,.0f} final value",
            )
            b2.metric(
                "Buy & Hold Return",
                f"{results['buyhold_return_pct']:.2f}%",
                delta=f"₹{results['buyhold_final']:,.0f} final value",
            )

            b3, b4 = st.columns(2)
            b3.metric("Total Trades", results["num_trades"])
            b4.metric("Max Drawdown", f"{results['max_drawdown']:.2f}%")

            st.caption(
                "**Max Drawdown** = sabse bada % jitna paisa peak se neeche gira beech mein. "
                "Ye batata hai strategy kitni 'risky' hai — jitna zyada negative, utna zyada dard "
                "beech mein sehna padta."
            )

            st.line_chart(bt_data[["StrategyEquity", "BuyHoldEquity"]])

            if results["strategy_return_pct"] > results["buyhold_return_pct"]:
                st.success(
                    "Is period mein strategy ne Buy & Hold se better perform kiya. "
                    "Lekin ek hi stock/period ke result se pura bharosa mat karo — "
                    "alag stocks aur alag time periods pe bhi test karo."
                )
            else:
                st.info(
                    "Is period mein sirf khareed ke rakhna (Buy & Hold) strategy se "
                    "better raha. Har strategy har stock/period mein kaam nahi karti."
                )

            # ---- Holding Plan: Kab tak rakhna hai? Kab exit/buy more? ----
            st.subheader("📆 Holding Plan: Kab tak rakhna hai | Exit kab? | Buy More kab?")
            last_g, last_d = find_last_crossovers(data)
            trend_up = latest["MA50"] > latest["MA200"]

            if trend_up:
                st.markdown("**Trend:** :green[Uptrend (Bullish)] — MA50 > MA200")
                if last_g is not None:
                    try:
                        days_since_g = (data.index[-1] - last_g).days
                        st.write(f"**Last Golden Cross:** {last_g.date()} ({days_since_g} din pehle)")
                        if days_since_g < 60:
                            st.write("**Holding Suggestion:** Abhi trend fresh hai. Multi-week hold consider kar sakte ho. Dips pe **Buy More** karne ka soch sakte ho jab RSI 40–50 range mein aaye.")
                        elif 60 <= days_since_g < 180:
                            st.write("**Holding Suggestion:** Mid-trend hai. Hold kar lo, lekin partial booking (thoda exit) ka plan rakho agar strong pullback aaye.")
                        else:
                            st.write("**Holding Suggestion:** Trend mature ho chuka hai. Tight stop-loss rakho. Zyada dip pe hi **Buy More** consider karo, fresh breakout nahi hua toh cautious raho.")
                    except Exception:
                        st.write(f"**Last Golden Cross:** {last_g}")
                else:
                    st.write("Pichle period mein clearly Golden Cross nahi mila.")

                if latest["RSI"] < 40:
                    st.write("**Buy More Opportunity:** :blue[RSI < 40] — Oversold zone ka hint, dip pe averaging consider kar lo (risk manage karke).")
                if latest["RSI"] > 70:
                    st.write("**Caution/Partial Exit:** :orange[RSI > 70] — Overbought. Thoda book profit karne ya trailing stop laga lo.")
                st.write("**Exit Plan:** Jab MA50 < MA200 ho jaye (Death Cross) ya RSI > 80 aur momentum girne lage — tab exit ka seriously soch lo.")
            else:
                st.markdown("**Trend:** :red[Downtrend (Bearish)] — MA50 < MA200")
                if last_d is not None:
                    try:
                        days_since_d = (data.index[-1] - last_d).days
                        st.write(f"**Last Death Cross:** {last_d.date()} ({days_since_d} din pehle)")
                        if days_since_d < 40:
                            st.write("**Holding Suggestion:** Abhi downtrend fresh hai. Naya buy avoid karo. Jo hold hain unke liye strict stop-loss rakho ya partial exit lo.")
                        else:
                            st.write("**Holding Suggestion:** Kabhi-kabhi downtrend bounce deta hai. Sirf reversal confirmation (MA50 > MA200 wapas) ke baad hi fresh entry socho.")
                    except Exception:
                        st.write(f"**Last Death Cross:** {last_d}")
                if latest["RSI"] < 30:
                    st.write("**Watch for Reversal:** :blue[RSI < 30] — Extreme oversold. Bounce aa sakta hai, lekin confirmation bina **Buy More** mat karo.")
                st.write("**Exit Plan:** Agar pehle se hold hain, trailing stop use karo. Fresh long entry tabhi lo jab MA50 wapas MA200 ke upar cross kare.")


            # ---- Data Source & Methodology ----
            st.subheader("ℹ️ Data Source & Methodology")
            st.write(
                "**Data Source:** [Yahoo Finance](https://finance.yahoo.com/) via [yfinance](https://github.com/ranaroussi/yfinance) library. "
                "Hum real historical OHLCV data use karte hain jo publicly available hai."
            )
            st.write(
                "**Indicators used:** Simple Moving Averages (MA50, MA200) + Relative Strength Index (RSI 14). "
                "**Strategy tested:** MA50/MA200 crossover (Golden/Death Cross) vs Buy & Hold. "
                "Backtest equity curve starting capital ₹100000 par calculate kiya gaya hai."
            )
            st.write(
                "**Holding/Exit logic:** Crossovers, trend (MA50 vs MA200), RSI levels aur days-since-last-crossover pe based simple rules diye gaye hain."
            )
            st.caption(
                "⚠️ **Disclaimer:** Ye tool educational purpose ke liye banaya gaya hai. "
                "Koi investment advice nahi hai. Past performance future results ka guarantee nahi hota. "
                "Real trading mein risk management (stop-loss, position sizing) zaroor use karo. "
                "Paisa lagane se pehle apni research aur financial advisor se consult karo."
            )

            # ---- Raw data (optional dekhne ke liye) ----
            with st.expander("Raw data dekhna ho toh yahan click karo"):
                st.dataframe(data.tail(20))
