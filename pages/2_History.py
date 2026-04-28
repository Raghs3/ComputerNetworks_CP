import sys
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from network_quality_ml import compute_quality_score
from utils import band_color, load_all_sites

st.set_page_config(page_title="History", layout="wide", page_icon="📊")
st.title("📊 History — Website Network Trends")

sites = load_all_sites()
if not sites:
    st.warning("No data found. Go to Predict to start monitoring.")
    st.stop()

sort_opt = st.radio("Sort by", ["Worst First", "Best First", "A–Z"], horizontal=True)
if sort_opt == "Worst First":
    sites = sorted(sites, key=lambda s: s["quality_score"])
elif sort_opt == "Best First":
    sites = sorted(sites, key=lambda s: s["quality_score"], reverse=True)
else:
    sites = sorted(sites, key=lambda s: s["display_name"])

if "history_selected" not in st.session_state:
    st.session_state.history_selected = None

for site in sites:
    color = site["color"]
    band = site["band"]
    score = site["quality_score"]

    col_score, col_info, col_btn = st.columns([1, 5, 1])
    with col_score:
        st.markdown(
            f"<div style='text-align:center; padding:8px;'>"
            f"<div style='font-size:28px; font-weight:bold; color:{color};'>{score:.0f}</div>"
            f"<div style='font-size:11px; color:#888;'>score</div></div>",
            unsafe_allow_html=True,
        )
    with col_info:
        st.markdown(
            f"<div style='border-left:4px solid {color}; padding:8px 12px;"
            f"background:#1e1e2e; border-radius:4px;'>"
            f"<strong style='font-size:15px;'>{site['display_name']}</strong> "
            f"<span style='background:{color}22; color:{color}; font-size:11px;"
            f"padding:2px 8px; border-radius:20px;'>{band}</span><br>"
            f"<span style='color:#888; font-size:12px;'>Avg RTT: {site['avg_rtt']:.0f}ms · "
            f"Jitter: {site['avg_jitter']:.0f}ms · Loss: {site['avg_loss']:.1f}% · "
            f"{site['sample_count']:,} samples</span></div>",
            unsafe_allow_html=True,
        )
    with col_btn:
        if st.button("Details ›", key=f"hist_{site['site_key']}"):
            st.session_state.history_selected = site["site_key"]

    st.markdown(
        "<hr style='border:none; border-top:1px solid #2a2a3a; margin:4px 0;'>",
        unsafe_allow_html=True,
    )

selected_key = st.session_state.history_selected
if selected_key:
    match = next((s for s in sites if s["site_key"] == selected_key), None)
    if match:
        st.divider()
        st.subheader(f"↳ {match['display_name']} — Full Detail")

        df = pd.read_csv(match["csv_path"])
        if "Timestamp" in df.columns:
            df["Timestamp"] = pd.to_datetime(df["Timestamp"], errors="coerce")
            x = df["Timestamp"]
        else:
            x = list(range(len(df)))

        for col in ["RTT (ms)", "Jitter (ms)", "Packet Loss (%)", "Throughput (Kbps)"]:
            if col not in df.columns:
                df[col] = 0.0
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0.0)

        df["Quality Score"] = df.apply(
            lambda r: compute_quality_score(
                r["RTT (ms)"], r["Jitter (ms)"], r["Packet Loss (%)"], r["Throughput (Kbps)"]
            ),
            axis=1,
        )

        def detail_chart(y_col, color, y_label):
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=x, y=df[y_col], mode="lines",
                                     line=dict(color=color, width=1.5)))
            fig.update_layout(
                title=y_col, height=220,
                margin=dict(l=40, r=20, t=40, b=40),
                paper_bgcolor="#0e1117", plot_bgcolor="#0e1117",
                font=dict(color="#ccc"),
                xaxis=dict(title="Time", gridcolor="#2a2a3a"),
                yaxis=dict(title=y_label, gridcolor="#2a2a3a"),
            )
            st.plotly_chart(fig, use_container_width=True)
            mn, mx, avg = df[y_col].min(), df[y_col].max(), df[y_col].mean()
            st.caption(f"Min: {mn:.1f} · Max: {mx:.1f} · Avg: {avg:.1f} {y_label}")

        ca, cb = st.columns(2)
        with ca:
            detail_chart("RTT (ms)", "#4f8ef7", "ms")
            detail_chart("Jitter (ms)", "#a78bfa", "ms")
        with cb:
            detail_chart("Packet Loss (%)", "#4fc97f", "%")
            detail_chart("Quality Score", "#f7a54f", "score")
