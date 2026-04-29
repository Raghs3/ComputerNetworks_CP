# 🌐 Real-Time Network Quality Prediction System

A 4-page Streamlit dashboard that monitors any website's network quality in real time, predicts future quality using a trained Random Forest model, and visualises historical trends and model performance.

---

## 🚀 Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Launch the dashboard
.venv\Scripts\streamlit run app.py
```

Open `http://localhost:8501` in your browser.

---

## 📋 Dashboard Pages

### 🏠 Dashboard (home)
Overview of all monitored sites — stat tiles (total / good / bad / poor) and a colour-coded site card grid. Click **Predict Live** on any card to jump straight to monitoring.

### 📡 Predict
Live monitoring and real-time ML prediction for any website.
1. Enter a URL and click **Start** — monitoring begins in a background process.
2. A warm-up progress bar counts 0 → 30 samples.
3. Once warmed up: 4 live charts (RTT, Jitter, Packet Loss, Throughput) update every second alongside a prediction card showing quality score, band, and forecast metrics for the next 15 seconds.
4. Click **Stop** to terminate the monitoring process.

### 📊 History
Historical trends per site. Sort by Worst / Best / A–Z. Click **Details ›** on any row to expand 4 full Plotly charts (RTT, Jitter, Packet Loss, Quality Score over time) with min/max/avg summaries.

### 🤖 Model
Model metadata (algorithm, trees, lookback, horizon, training date, site count), Quality Score R² gauge, per-target accuracy table (MAE / RMSE / R²), feature importance bar chart, and a **Retrain** button that detects new CSVs and retrains on demand.

---

## ⚙️ How It Works

```
User enters site
      │
      ▼
run_monitor.py (subprocess, non-interactive)
      │  pings every second → appends rows to CSV
      ▼
data/network_data_<site>.csv
      │
      ├──► Predict page  → last 30 rows → model.predict() → Quality Score
      ├──► History page  → all rows    → trend charts
      └──► Dashboard     → avg metrics → site cards

models/network_quality_model.joblib
      │  loaded once at startup (st.cache_resource)
      ├──► Predict page  → predictions
      └──► Model page    → metadata + metrics
```

### ML Model
- **Algorithm:** Random Forest (multi-output regressor)
- **Targets:** Future RTT, Jitter, Packet Loss, Throughput, Quality Score
- **Lookback:** 30 seconds of rolling features
- **Horizon:** 15-second forecast
- **Training:** `python train_network_quality_model.py --once`

### Quality Score Colour Bands

| Band      | Score  | Colour      |
|-----------|--------|-------------|
| Excellent | 85–100 | Green       |
| Good      | 70–84  | Yellow-green|
| Bad       | 45–69  | Orange      |
| Poor      | 0–44   | Red         |

---

## 📈 Metrics

| Metric | Unit | Good value |
|--------|------|------------|
| RTT (Round-Trip Time) | ms | < 50 ms |
| Jitter | ms | < 10 ms |
| Packet Loss | % | 0 % |
| Throughput (estimated) | Kbps | higher = better |

---

## 🖥️ CLI Usage (without dashboard)

**Monitor a site directly:**
```bash
python run_monitor.py google.com data/network_data_google_com.csv
```

**Train the model:**
```bash
python train_network_quality_model.py --once
```

**Real-time prediction from CSV:**
```bash
python predict_network_quality_realtime.py --csv data/network_data_google_com.csv
```

---

## 🗂️ Project Structure

```
CN-project/
├── app.py                          # Dashboard home page
├── pages/
│   ├── 1_Predict.py                # Live monitoring + prediction
│   ├── 2_History.py                # Per-site historical trends
│   └── 3_Model.py                  # Model info + retraining
├── utils.py                        # Shared helpers (CSV loading, colour bands)
├── run_monitor.py                  # Non-interactive monitor wrapper
├── network_monitor.py              # Core monitoring backend
├── network_quality_ml.py           # ML utilities (features, scoring, loading)
├── train_network_quality_model.py  # Model training script
├── predict_network_quality_realtime.py
├── data/                           # Per-site CSVs (network_data_*.csv)
├── models/                         # Trained model (network_quality_model.joblib)
├── .streamlit/config.toml          # Dark theme
├── requirements.txt
└── tests/
    └── test_utils.py               # 12 unit tests
```

---

## 🧪 Tests

```bash
.venv\Scripts\pytest tests/ -v
```

Expected: 12 passed.
