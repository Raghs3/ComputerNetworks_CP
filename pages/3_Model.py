import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from network_quality_ml import DEFAULT_MODEL_PATH, load_model_bundle
from train_network_quality_model import train_once
from utils import force_single_threaded_model

st.set_page_config(page_title="Model", layout="wide", page_icon="🤖")
st.title("🤖 Model — Performance & Parameters")

MODEL_PATH = DEFAULT_MODEL_PATH
DATA_DIR = Path(__file__).resolve().parent.parent / "data"


@st.cache_resource
def load_model():
    return load_model_bundle(MODEL_PATH)


bundle = load_model()
model = force_single_threaded_model(bundle["model"])

# --- model info + R² + retrain ---
c1, c2, c3 = st.columns([3, 1, 1])

with c1:
    st.subheader("Active Model")
    info = {
        "Algorithm": bundle.get("model_name", type(model).__name__),
        "Trees": str(getattr(model, "n_estimators", "—")),
        "Lookback": f"{bundle.get('lookback', '—')}s",
        "Horizon": f"{bundle.get('horizon', '—')}s",
        "Trained At": bundle.get("trained_at", "—"),
        "Sites": str(len(bundle.get("site_keys", []))),
    }
    metric_cols = st.columns(3)
    for i, (k, v) in enumerate(info.items()):
        metric_cols[i % 3].metric(k, v)

with c2:
    qs_r2 = bundle.get("metrics", {}).get("Future Quality Score R2", 0.0)
    st.subheader("Quality Score R²")
    st.markdown(
        f"<div style='font-size:52px; font-weight:bold; color:#4fc97f;"
        f"text-align:center;'>{qs_r2:.2f}</div>",
        unsafe_allow_html=True,
    )
    st.progress(float(max(0.0, min(1.0, qs_r2))))
    st.caption("1.0 = perfect fit")

with c3:
    st.subheader("Retrain")
    model_mtime = os.path.getmtime(MODEL_PATH) if MODEL_PATH.exists() else 0
    new_csvs = [f for f in DATA_DIR.glob("network_data_*.csv") if f.stat().st_mtime > model_mtime]
    if new_csvs:
        st.info(f"{len(new_csvs)} new CSV(s) detected")
    if st.button("🔄 Retrain Now", width="stretch"):
        with st.spinner("Retraining... this may take a minute."):
            try:
                train_once(
                    data_dir=DATA_DIR,
                    model_path=MODEL_PATH,
                    lookback=int(bundle.get("lookback", 30)),
                    horizon=int(bundle.get("horizon", 15)),
                    test_ratio=0.2,
                    n_estimators=300,
                    n_jobs=1,
                )
                st.cache_resource.clear()
                st.success("Model retrained successfully!")
                st.rerun()
            except Exception as e:
                st.error(f"Retraining failed: {e}")

st.divider()

# --- per-target accuracy table ---
st.subheader("Accuracy per Target — Test Set")
metrics = bundle.get("metrics", {})
targets = [
    ("RTT (ms)", "RTT (ms)"),
    ("Jitter (ms)", "Jitter (ms)"),
    ("Packet Loss (%)", "Packet Loss (%)"),
    ("Throughput (Kbps)", "Throughput (Kbps)"),
    ("Future Quality Score", "Quality Score"),
]

header = st.columns([3, 2, 2, 2, 4])
for col, label in zip(header, ["Target", "MAE", "RMSE", "R²", "Fit"]):
    col.markdown(f"**{label}**")

for target_key, display_name in targets:
    mae = metrics.get(f"{target_key} MAE", 0.0)
    rmse = metrics.get(f"{target_key} RMSE", 0.0)
    r2 = metrics.get(f"{target_key} R2", 0.0)
    r2_color = "#4fc97f" if r2 >= 0.85 else "#f7a54f" if r2 >= 0.7 else "#e05c5c"
    row = st.columns([3, 2, 2, 2, 4])
    row[0].write(display_name)
    row[1].write(f"{mae:.3f}")
    row[2].write(f"{rmse:.3f}")
    row[3].markdown(
        f"<span style='color:{r2_color}; font-weight:bold;'>{r2:.3f}</span>",
        unsafe_allow_html=True,
    )
    row[4].progress(float(max(0.0, min(1.0, r2))))

st.caption("MAE = Mean Absolute Error · RMSE = Root Mean Squared Error · R² = 1.0 means perfect fit")

st.divider()

# --- feature importance ---
st.subheader("Top Features by Importance")
try:
    importances = getattr(model, "feature_importances_")
except Exception as error:
    st.warning(f"Feature importances are unavailable for this model in the current environment: {error}")
else:
    feature_names = list(bundle.get("feature_names", []))
    named_count = min(len(feature_names), len(importances))
    idx = np.argsort(importances[:named_count])[::-1][:8]
    top_names = [feature_names[i] for i in idx]
    top_vals = [float(importances[i]) for i in idx]

    bar_colors = ["#4f8ef7", "#4f8ef7", "#a78bfa", "#a78bfa",
                  "#f7a54f", "#f7a54f", "#e05c5c", "#e05c5c"][:len(top_vals)]

    fig = go.Figure(go.Bar(
        x=top_vals, y=top_names, orientation="h",
        marker_color=bar_colors,
        text=[f"{v:.3f}" for v in top_vals],
        textposition="inside",
    ))
    fig.update_layout(
        height=320, margin=dict(l=220, r=40, t=20, b=40),
        paper_bgcolor="#0e1117", plot_bgcolor="#0e1117",
        font=dict(color="#ccc", size=13),
        xaxis=dict(title="Importance", gridcolor="#2a2a3a"),
        yaxis=dict(autorange="reversed"),
    )
    st.plotly_chart(fig, width="stretch")
