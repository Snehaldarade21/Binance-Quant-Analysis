import streamlit as st
import pandas as pd
import numpy as np
import sqlite3
import threading
import json
import time
import websocket
from datetime import datetime
import base64
import streamlit as st

# =============================
# STREAMLIT PAGE CONFIG
# =============================
st.set_page_config(
    page_title="Binance Quant Analytics",
    layout="wide"
)

# =============================
# GLOBAL STYLES (READABLE UI)
# =============================
import base64
import streamlit as st

def set_background(image_path):
    with open(image_path, "rb") as f:
        encoded = base64.b64encode(f.read()).decode()

    st.markdown(
        f"""
        <style>
        .stApp {{
            background-image: url("data:image/jpeg;base64,{encoded}");
            background-size: cover;
            background-position: center;
            background-repeat: no-repeat;
            background-attachment: fixed;
        }}

        /* Sidebar stays readable */
        section[data-testid="stSidebar"] {{
            background-color: rgba(255, 255, 255, 0.95);
        }}

        /* Force black text everywhere */
        html, body, [class*="css"] {{
            color: black !important;
        }}

        /* Cards readable */
        div[data-testid="stMetric"] {{
            background-color: rgba(255, 255, 255, 0.9);
            border-radius: 10px;
            padding: 15px;
        }}
        </style>
        """,
        unsafe_allow_html=True
    )

# CALL ONCE
set_background("image.png")


# =============================
# DATABASE
# =============================
conn = sqlite3.connect("market.db", check_same_thread=False)
cursor = conn.cursor()
cursor.execute("""
CREATE TABLE IF NOT EXISTS trades (
    ts TEXT,
    symbol TEXT,
    price REAL
)
""")
conn.commit()

# =============================
# SESSION STATE
# =============================
if "prices" not in st.session_state:
    st.session_state.prices = pd.DataFrame()

if "streaming" not in st.session_state:
    st.session_state.streaming = False

# =============================
# WEBSOCKET INGESTION
# =============================
def on_message(ws, message):
    msg = json.loads(message)
    data = msg["data"]

    ts = datetime.utcnow().isoformat()
    symbol = data["s"]
    price = float(data["p"])

    cursor.execute(
        "INSERT INTO trades VALUES (?,?,?)",
        (ts, symbol, price)
    )
    conn.commit()

def start_stream(symbols):
    streams = "/".join([f"{s.lower()}@trade" for s in symbols])
    url = f"wss://fstream.binance.com/stream?streams={streams}"

    ws = websocket.WebSocketApp(url, on_message=on_message)
    ws.run_forever()

# =============================
# DATA LOADER (SAFE)
# =============================
def load_prices(symbols):
    df = pd.read_sql(
        "SELECT * FROM trades ORDER BY ts",
        conn,
        parse_dates=["ts"]
    )

    if df.empty:
        idx = pd.date_range(end=pd.Timestamp.utcnow(), periods=50, freq="S")
        return pd.DataFrame(
            np.random.normal(100, 0.1, (50, len(symbols))),
            index=idx,
            columns=symbols
        )

    df = df.drop_duplicates(subset=["ts", "symbol"])
    prices = df.pivot(index="ts", columns="symbol", values="price")
    prices = prices.ffill().bfill()

    return prices[symbols]

# =============================
# ANALYTICS (SAFE)
# =============================
def compute_spread_z(prices):
    s1, s2 = prices.iloc[:, 0], prices.iloc[:, 1]
    spread = s1 - s2
    z = (spread - spread.mean()) / (spread.std() + 1e-6)
    return spread, z

# =============================
# SIDEBAR
# =============================
st.sidebar.title("⚙️ Controls")

symbols_input = st.sidebar.text_input(
    "Symbols (comma separated)",
    "BTCUSDT,ETHUSDT"
)
symbols = [s.strip().upper() for s in symbols_input.split(",")]

if st.sidebar.button("▶ Start Stream"):
    if not st.session_state.streaming:
        threading.Thread(
            target=start_stream,
            args=(symbols,),
            daemon=True
        ).start()
        st.session_state.streaming = True

page = st.sidebar.radio(
    "Navigation",
    [
        "Market Overview",
        "Pair Analytics",
        "Alerts",
        "Backtesting",
        "Kalman Hedge Ratio"
    ]
)

# =============================
# LOAD DATA ONCE PER RUN
# =============================
prices = load_prices(symbols)
spread, z = compute_spread_z(prices)

# =============================
# MARKET OVERVIEW
# =============================
if page == "Market Overview":
    st.title("📈 Live Market Overview")
    st.line_chart(prices)

# =============================
# PAIR ANALYTICS
# =============================
elif page == "Pair Analytics":
    st.title("🔗 Pair Analytics")

    col1, col2 = st.columns(2)
    col1.metric("Latest Spread", round(spread.iloc[-1], 4))
    col2.metric("Latest Z-Score", round(z.iloc[-1], 2))

    st.subheader("Spread & Z-Score")
    st.line_chart(pd.DataFrame({
        "Spread": spread,
        "Z-Score": z
    }))

# =============================
# ALERTS
# =============================
elif page == "Alerts":
    st.title("🚨 Alerts")

    threshold = st.slider("Z-Score Threshold", 0.5, 5.0, 2.0)
    z_val = float(z.iloc[-1])

    st.metric("Current Z-Score", round(z_val, 2))

    if abs(z_val) >= threshold:
        st.error("⚠️ ALERT TRIGGERED")
    else:
        st.success("✅ No Alert")

    st.line_chart(z)

# =============================
# BACKTESTING
# =============================
elif page == "Backtesting":
    st.title("📉 Backtesting")

    pnl = -z.shift(1).fillna(0) * spread.diff().fillna(0)
    cum_pnl = pnl.cumsum()

    st.metric("Total PnL", round(cum_pnl.iloc[-1], 2))
    st.line_chart(cum_pnl)

# =============================
# KALMAN HEDGE RATIO
# =============================
elif page == "Kalman Hedge Ratio":
    st.title("📐 Kalman Hedge Ratio")

    y = prices.iloc[:, 0].values
    x = prices.iloc[:, 1].values

    beta = np.cumsum(x * y) / (np.cumsum(x**2) + 1e-6)
    beta_series = pd.Series(beta, index=prices.index)

    st.metric("Latest Hedge Ratio", round(beta_series.iloc[-1], 3))
    st.line_chart(beta_series)
