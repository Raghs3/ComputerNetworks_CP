from __future__ import annotations

from pathlib import Path

import pandas as pd

from network_quality_ml import compute_quality_score, quality_band

DATA_DIR = Path(__file__).parent / "data"

BAND_COLORS = {
    "Excellent": "#4fc97f",
    "Good": "#a8d86e",
    "Bad": "#f7a54f",
    "Poor": "#e05c5c",
}


def band_color(band: str) -> str:
    return BAND_COLORS.get(band, "#888888")


def quality_band_from_score(score: float) -> str:
    return quality_band(float(score))


def format_site_name(site_key: str) -> str:
    return site_key.replace("_", ".")


def load_site_summary(csv_path: Path) -> dict:
    stem = csv_path.stem
    site_key = stem.removeprefix("network_data_") if stem.startswith("network_data_") else stem

    df = pd.read_csv(csv_path)
    for col in ["RTT (ms)", "Jitter (ms)", "Packet Loss (%)", "Throughput (Kbps)"]:
        if col not in df.columns:
            df[col] = 0.0
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0.0)

    avg_rtt = float(df["RTT (ms)"].mean())
    avg_jitter = float(df["Jitter (ms)"].mean())
    avg_loss = float(df["Packet Loss (%)"].mean())
    avg_throughput = float(df["Throughput (Kbps)"].mean())
    score = compute_quality_score(avg_rtt, avg_jitter, avg_loss, avg_throughput)
    band = quality_band(score)

    return {
        "site_key": site_key,
        "display_name": format_site_name(site_key),
        "avg_rtt": avg_rtt,
        "avg_jitter": avg_jitter,
        "avg_loss": avg_loss,
        "avg_throughput": avg_throughput,
        "quality_score": round(score, 1),
        "band": band,
        "color": band_color(band),
        "sample_count": len(df),
        "csv_path": csv_path,
    }


def load_all_sites(data_dir: Path | None = None) -> list[dict]:
    base = data_dir or DATA_DIR
    summaries = []
    for csv_path in sorted(base.glob("network_data_*.csv")):
        try:
            summaries.append(load_site_summary(csv_path))
        except Exception:
            continue
    return summaries


def csv_path_for_site(site: str) -> Path:
    target = site
    if target.startswith("http://"):
        target = target[7:]
    elif target.startswith("https://"):
        target = target[8:]
    target = target.rstrip("/")
    safe = target.replace(".", "_").replace("/", "_").replace(":", "_")
    return DATA_DIR / f"network_data_{safe}.csv"
