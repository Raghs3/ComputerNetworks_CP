import pandas as pd
import numpy as np
import pytest
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from utils import band_color, quality_band_from_score, load_site_summary, format_site_name, csv_path_for_site


def test_band_color_excellent():
    assert band_color("Excellent") == "#4fc97f"


def test_band_color_good():
    assert band_color("Good") == "#a8d86e"


def test_band_color_bad():
    assert band_color("Bad") == "#f7a54f"


def test_band_color_poor():
    assert band_color("Poor") == "#e05c5c"


def test_band_color_unknown():
    assert band_color("Unknown") == "#888888"


def test_quality_band_from_score_excellent():
    assert quality_band_from_score(90) == "Excellent"
    assert quality_band_from_score(85) == "Excellent"


def test_quality_band_from_score_good():
    assert quality_band_from_score(75) == "Good"
    assert quality_band_from_score(70) == "Good"


def test_quality_band_from_score_bad():
    assert quality_band_from_score(60) == "Bad"
    assert quality_band_from_score(45) == "Bad"


def test_quality_band_from_score_poor():
    assert quality_band_from_score(44) == "Poor"
    assert quality_band_from_score(0) == "Poor"


def test_format_site_name():
    assert format_site_name("google_com") == "google.com"
    assert format_site_name("linkedIn_com") == "linkedIn.com"


def test_load_site_summary(tmp_path):
    csv_path = tmp_path / "network_data_test_com.csv"
    df = pd.DataFrame({
        "Timestamp": ["2026-04-26 18:00:00"] * 5,
        "RTT (ms)": [100.0, 110.0, 90.0, 120.0, 100.0],
        "Jitter (ms)": [10.0, 12.0, 8.0, 15.0, 10.0],
        "Packet Loss (%)": [0.0, 0.0, 0.0, 0.0, 0.0],
        "Throughput (Kbps)": [2.5, 2.3, 2.8, 2.1, 2.5],
    })
    df.to_csv(csv_path, index=False)

    summary = load_site_summary(csv_path)

    assert summary["site_key"] == "test_com"
    assert summary["display_name"] == "test.com"
    assert abs(summary["avg_rtt"] - 104.0) < 0.1
    assert summary["avg_loss"] == 0.0
    assert summary["sample_count"] == 5
    assert "quality_score" in summary
    assert "band" in summary
    assert "color" in summary


def test_csv_path_for_site():
    assert csv_path_for_site("https://google.com").name == "network_data_google_com.csv"
    assert csv_path_for_site("http://google.com").name == "network_data_google_com.csv"
    assert csv_path_for_site("google.com").name == "network_data_google_com.csv"
    assert csv_path_for_site("github.com/").name == "network_data_github_com.csv"
