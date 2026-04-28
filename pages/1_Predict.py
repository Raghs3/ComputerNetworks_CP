import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from streamlit_autorefresh import st_autorefresh

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from network_quality_ml import (
    DEFAULT_MODEL_PATH,
    compute_quality_score,
    load_model_bundle,
    make_prediction_features,
    quality_band,
)
from utils import band_color, csv_path_for_site

st.set_page_config(page_title="Predict", layout="wide", page_icon="📡")
st.title("📡 Predict — Real-Time Network Quality")


@st.cache_resource
def load_model():
    return load_model_bundle(DEFAULT_MODEL_PATH)


model_bundle = load_model()

if "monitor_proc" not in st.session_state:
    st.session_state.monitor_proc = None
if "monitor_site" not in st.session_state:
    st.session_state.monitor_site = ""
if "monitoring" not in st.session_state:
    st.session_state.monitoring = False

prefill = st.session_state.pop("prefill_site", "")

col_input, col_start, col_stop = st.columns([4, 1, 1])
with col_input:
    site = st.text_input("Website", value=prefill or st.session_state.monitor_site,
                         placeholder="e.g. netflix.com")
with col_start:
    st.write("")
    start_clicked = st.button("▶ Start", use_container_width=True, type="primary")
with col_stop:
    st.write("")
    stop_clicked = st.button("■ Stop", use_container_width=True)

if start_clicked and site:
    if st.session_state.monitor_proc is not None:
        try:
            st.session_state.monitor_proc.terminate()
        except Exception:
            pass
    csv_path = csv_path_for_site(site)
    python_exe = sys.executable
    wrapper = str(Path(__file__).resolve().parent.parent / "run_monitor.py")
    proc = subprocess.Popen([python_exe, wrapper, site, str(csv_path)])
    st.session_state.monitor_proc = proc
    st.session_state.monitor_site = site
    st.session_state.monitoring = True

if stop_clicked:
    if st.session_state.monitor_proc is not None:
        try:
            st.session_state.monitor_proc.terminate()
        except Exception:
            pass
    st.session_state.monitor_proc = None
    st.session_state.monitoring = False

if st.session_state.monitoring:
    st_autorefresh(interval=1000, key="monitor_refresh")

active_site = st.session_state.monitor_site
if not active_site:
    st.info("Enter a website above and click Start to begin monitoring.")
    st.stop()

csv_path = csv_path_for_site(active_site)
if not csv_path.exists():
    st.info(f"Waiting for data from {active_site}...")
    st.stop()

df = pd.read_csv(csv_path)
for col in ["RTT (ms)", "Jitter (ms)", "Packet Loss (%)", "Throughput (Kbps)"]:
    if col not in df.columns:
        df[col] = 0.0
    df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0.0)

rows = len(df)
lookback = int(model_bundle["lookback"])

if rows < lookback:
    st.subheader(f"Collecting warm-up data for {active_site}...")
    st.progress(rows / lookback, text=f"{rows} / {lookback} samples — prediction starts at {lookback}")
    st.stop()

last = df.iloc[-1]
c1, c2, c3, c4 = st.columns(4)
c1.metric("RTT", f"{last['RTT (ms)']:.0f} ms")
c2.metric("Jitter", f"{last['Jitter (ms)']:.0f} ms")
c3.metric("Packet Loss", f"{last['Packet Loss (%)']:.1f} %")
c4.metric("Throughput", f"{last['Throughput (Kbps)']:.2f} Kbps")

recent = df.tail(30).copy()
if "Timestamp" in recent.columns:
    recent["Timestamp"] = pd.to_datetime(recent["Timestamp"], errors="coerce")
    x = recent["Timestamp"]
else:
    x = list(range(len(recent)))


def make_chart(y_series, title, color, y_label):
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=x, y=y_series, mode="lines+markers",
                             line=dict(color=color, width=2), marker=dict(size=4)))
    fig.update_layout(
        title=title, height=220, margin=dict(l=40, r=20, t=40, b=40),
        paper_bgcolor="#0e1117", plot_bgcolor="#0e1117", font=dict(color="#ccc"),
        xaxis=dict(title="Time", gridcolor="#2a2a3a", showgrid=True),
        yaxis=dict(title=y_label, gridcolor="#2a2a3a", showgrid=True),
    )
    st.plotly_chart(fig, use_container_width=True)
    st.caption(f"Min: {y_series.min():.1f} · Max: {y_series.max():.1f} · Avg: {y_series.mean():.1f} {y_label}")


col_a, col_b = st.columns(2)
with col_a:
    make_chart(recent["RTT (ms)"], "RTT (ms)", "#4f8ef7", "ms")
    make_chart(recent["Packet Loss (%)"], "Packet Loss (%)", "#4fc97f", "%")
with col_b:
    make_chart(recent["Jitter (ms)"], "Jitter (ms)", "#a78bfa", "ms")
    make_chart(recent["Throughput (Kbps)"], "Throughput (Kbps)", "#f7a54f", "Kbps")

st.divider()
features = make_prediction_features(csv_path, model_bundle)
if features.size == 0:
    st.warning("Not enough data for prediction yet.")
    st.stop()

predicted = model_bundle["model"].predict(features.reshape(1, -1))[0]
pred_rtt = float(predicted[0])
pred_jitter = float(predicted[1])
pred_loss = float(predicted[2])
pred_throughput = float(predicted[3])
pred_quality = float(np.clip(predicted[4], 0.0, 100.0))
band = quality_band(pred_quality)
color = band_color(band)
is_working = pred_loss < 2.0 and pred_rtt < 300.0
horizon = int(model_bundle["horizon"])

st.subheader(f"Prediction — Next {horizon} seconds")
pc1, pc2 = st.columns([1, 2])
with pc1:
    st.markdown(
        f"""
        <div style="text-align:center; padding:20px; background:#1e1e2e;
                    border:1px solid {color}; border-radius:8px;">
          <div style="font-size:60px; font-weight:bold; color:{color};">{pred_quality:.0f}</div>
          <div style="color:#aaa; font-size:13px;">Quality Score / 100</div>
          <div style="margin-top:10px; background:{color}; color:#000; font-weight:bold;
                      padding:5px 18px; border-radius:20px; display:inline-block;">{band}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
with pc2:
    st.markdown(
        f"""
        | Metric | Predicted |
        |--------|-----------|
        | RTT | {pred_rtt:.1f} ms |
        | Jitter | {pred_jitter:.1f} ms |
        | Packet Loss | {pred_loss:.2f} % |
        | Throughput | {pred_throughput:.2f} Kbps |
        | Availability | {'✅ Likely Working' if is_working else '⚠️ Likely Degraded'} |
        """
    )
