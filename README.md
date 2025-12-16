📊 Live Binance Quant Analytics Dashboard
🎯 Objective

Build a real-time quantitative analytics dashboard that ingests live Binance market data, performs statistical analysis, and visualizes results interactively — all using pure Python and Streamlit.

🔌 Data Ingestion

Live WebSocket connection to Binance Futures
Real-time tick data: price, quantity, timestamp
No Docker, Node.js, or external backend 🚫

🗄️ Storage & Sampling

Runtime-created SQLite database
Continuous tick storage
Resampling: 1s / 1m / 5m

📈 Analytics

Price statistics 📉
OLS hedge ratio
Spread & Z-score
ADF stationarity test
Rolling correlation

🔄 Kalman filter hedge ratio
📊 Mean-reversion backtesting
🚨 Rule-based alerts (e.g. Z > 2)

🖥️ Dashboard Pages

🧭 Market Overview – live prices & volume
🔬 Pair Analytics – spread, Z-score, correlation
🚨 Alerts – statistical signal triggers
📊 Backtesting – strategy performance
📐 Kalman Filter – dynamic hedge estimation

🧱 Architecture
Binance WebSocket → Ingestion → SQLite → Analytics → Streamlit UI


Modular & extensible design
Easy to add new data sources or analytics

🚀 Run the App
pip install -r requirements.txt
streamlit run app.py

🛠 Tech Stack

🐍 Python
📊 Streamlit + Plotly
🧮 Pandas, NumPy, Statsmodels
🗄️ SQLite
