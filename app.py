import streamlit as st
from utils import load_all_sites

st.set_page_config(page_title="Network Quality Dashboard", layout="wide", page_icon="📡")

st.title("📡 Network Quality Dashboard")
st.caption("Real-time network quality prediction system")

sites = load_all_sites()

if not sites:
    st.warning("No monitoring data found in data/. Go to **Predict** to start collecting data.")
    st.stop()

total = len(sites)
good_count = sum(1 for s in sites if s["band"] in ("Excellent", "Good"))
bad_count = sum(1 for s in sites if s["band"] == "Bad")
poor_count = sum(1 for s in sites if s["band"] == "Poor")

c1, c2, c3, c4 = st.columns(4)
c1.metric("Sites Monitored", total)
c2.metric("Excellent / Good", good_count)
c3.metric("Bad", bad_count)
c4.metric("Poor", poor_count)

st.divider()

cols = st.columns(3)
for i, site in enumerate(sorted(sites, key=lambda s: s["quality_score"])):
    with cols[i % 3]:
        score = site["quality_score"]
        band = site["band"]
        color = site["color"]
        st.markdown(
            f"""
            <div style="border-left:4px solid {color}; background:#1e1e2e;
                        padding:14px; border-radius:8px; margin-bottom:12px;">
              <div style="display:flex; justify-content:space-between; align-items:center;">
                <strong style="font-size:15px;">{site['display_name']}</strong>
                <span style="background:{color}22; color:{color}; font-size:12px;
                             padding:2px 10px; border-radius:20px;">{band}</span>
              </div>
              <div style="font-size:36px; font-weight:bold; color:{color}; margin:6px 0;">{score}</div>
              <div style="font-size:12px; color:#888;">
                RTT: {site['avg_rtt']:.0f}ms &nbsp;·&nbsp; Loss: {site['avg_loss']:.1f}%
                &nbsp;·&nbsp; {site['sample_count']:,} samples
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if st.button("▶ Predict Live", key=f"predict_{site['site_key']}"):
            st.session_state["prefill_site"] = site["display_name"]
            st.switch_page("pages/1_Predict.py")
