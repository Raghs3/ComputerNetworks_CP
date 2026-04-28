from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import math

import joblib
import numpy as np
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
MODEL_DIR = BASE_DIR / "models"
DEFAULT_MODEL_PATH = MODEL_DIR / "network_quality_model.joblib"

TARGET_COLUMNS = [
    "RTT (ms)",
    "Jitter (ms)",
    "Packet Loss (%)",
    "Throughput (Kbps)",
]

TIME_OF_DAY_MAP = {
    "Night": 0,
    "Morning": 1,
    "Afternoon": 2,
    "Evening": 3,
}

ROW_FEATURE_COLUMNS = [
    "Hour of Day",
    "hour_sin",
    "hour_cos",
    "day_sin",
    "day_cos",
    "is_weekend",
    "time_of_day_code",
    "RTT (ms)",
    "Latency (ms)",
    "Jitter (ms)",
    "Packet Loss (%)",
    "Throughput (Kbps)",
    "Bandwidth Utilization (%)",
    "Moving Avg RTT",
    "Moving Avg Jitter",
    "Moving Avg Loss",
    "RTT Std Dev",
    "Jitter Std Dev",
    "RTT Trend Slope",
    "Throughput Trend Slope",
    "Timeout Streak",
    "Timeout Count (Last 30s)",
    "Time Since Last Timeout (s)",
    "RTT P90",
    "Normalized RTT",
    "Normalized Jitter",
    "Normalized Loss",
    "Normalized Throughput",
]


def site_key_from_path(csv_path: Path) -> str:
    stem = csv_path.stem
    if stem.startswith("network_data_"):
        return stem.removeprefix("network_data_")
    return stem


def build_site_feature_names(site_keys: list[str]) -> list[str]:
    return [f"site__{site_key}" for site_key in site_keys]


def build_site_feature_vector(site_key: str, site_keys: list[str]) -> np.ndarray:
    vector = np.zeros(len(site_keys), dtype=float)
    try:
        vector[site_keys.index(site_key)] = 1.0
    except ValueError:
        pass
    return vector


@dataclass
class DatasetBundle:
    features: np.ndarray
    targets: np.ndarray
    target_times: np.ndarray
    feature_names: list[str]


def ensure_directories() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    MODEL_DIR.mkdir(parents=True, exist_ok=True)


def compute_quality_score(rtt: float, jitter: float, loss: float, throughput: float) -> float:
    """Convert predicted metrics into a 0-100 quality score."""
    rtt_score = 1.0 - np.clip(rtt / 200.0, 0.0, 1.0)
    jitter_score = 1.0 - np.clip(jitter / 100.0, 0.0, 1.0)
    loss_score = 1.0 - np.clip(loss / 100.0, 0.0, 1.0)
    throughput_score = np.clip(throughput / 10000.0, 0.0, 1.0)

    score = 100.0 * (
        0.35 * rtt_score
        + 0.25 * jitter_score
        + 0.25 * loss_score
        + 0.15 * throughput_score
    )
    return float(np.clip(score, 0.0, 100.0))


def quality_band(score: float) -> str:
    if score >= 85:
        return "Excellent"
    if score >= 70:
        return "Good"
    if score >= 45:
        return "Bad"
    return "Poor"


def _coerce_numeric(series: pd.Series, default: float = 0.0) -> pd.Series:
    return pd.to_numeric(series, errors="coerce").fillna(default)


def _derive_time_features(df: pd.DataFrame) -> pd.DataFrame:
    frame = df.copy()

    frame["Timestamp"] = pd.to_datetime(frame.get("Timestamp"), errors="coerce")
    if frame["Timestamp"].isna().all():
        frame["Timestamp"] = pd.Timestamp.now()
    else:
        frame["Timestamp"] = frame["Timestamp"].ffill().bfill()

    if "Hour of Day" in frame.columns:
        hour_values = _coerce_numeric(frame["Hour of Day"]).astype(int)
    else:
        hour_values = frame["Timestamp"].dt.hour.fillna(0).astype(int)
        frame["Hour of Day"] = hour_values

    if "Time of Day" in frame.columns:
        time_of_day = frame["Time of Day"].fillna("Night")
    else:
        time_of_day = hour_values.map(
            lambda hour: "Morning"
            if 5 <= hour < 12
            else "Afternoon"
            if 12 <= hour < 17
            else "Evening"
            if 17 <= hour < 21
            else "Night"
        )
        frame["Time of Day"] = time_of_day

    frame["hour_sin"] = np.sin(2 * np.pi * hour_values / 24.0)
    frame["hour_cos"] = np.cos(2 * np.pi * hour_values / 24.0)

    day_of_week = frame["Timestamp"].dt.dayofweek.fillna(0).astype(int)
    frame["day_sin"] = np.sin(2 * np.pi * day_of_week / 7.0)
    frame["day_cos"] = np.cos(2 * np.pi * day_of_week / 7.0)
    frame["is_weekend"] = (day_of_week >= 5).astype(int)
    frame["time_of_day_code"] = frame["Time of Day"].map(TIME_OF_DAY_MAP).fillna(0).astype(int)

    return frame


def prepare_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    frame = _derive_time_features(df)

    if "Latency (ms)" not in frame.columns:
        frame["Latency (ms)"] = frame.get("RTT (ms)", 0.0)

    required_numeric_columns = ROW_FEATURE_COLUMNS + TARGET_COLUMNS
    for column in required_numeric_columns:
        if column not in frame.columns:
            frame[column] = 0.0
        frame[column] = _coerce_numeric(frame[column])

    frame = frame.sort_values("Timestamp").reset_index(drop=True)
    return frame


def build_feature_names(lookback: int, site_feature_names: list[str] | None = None) -> list[str]:
    names: list[str] = []
    for offset in range(lookback):
        lag = lookback - 1 - offset
        for column in ROW_FEATURE_COLUMNS:
            names.append(f"{column}_t-{lag}")
    if site_feature_names:
        names.extend(site_feature_names)
    return names


def build_window_samples(
    df: pd.DataFrame,
    lookback: int = 30,
    horizon: int = 15,
    site_feature_vector: np.ndarray | None = None,
    site_feature_names: list[str] | None = None,
) -> DatasetBundle:
    frame = prepare_dataframe(df)
    site_vector = site_feature_vector if site_feature_vector is not None else np.empty((0,), dtype=float)
    site_names = site_feature_names or []

    if len(frame) < lookback + horizon:
        return DatasetBundle(
            features=np.empty((0, lookback * len(ROW_FEATURE_COLUMNS) + len(site_vector))),
            targets=np.empty((0, 5)),
            target_times=np.empty((0,), dtype="datetime64[ns]"),
            feature_names=build_feature_names(lookback, site_names),
        )

    feature_matrix = frame[ROW_FEATURE_COLUMNS].to_numpy(dtype=float)
    target_matrix = frame[TARGET_COLUMNS].to_numpy(dtype=float)
    timestamps = frame["Timestamp"].to_numpy(dtype="datetime64[ns]")

    features: list[np.ndarray] = []
    targets: list[np.ndarray] = []
    target_times: list[np.datetime64] = []

    for end_index in range(lookback - 1, len(frame) - horizon):
        window_features = feature_matrix[end_index - lookback + 1 : end_index + 1]
        future_window = target_matrix[end_index + 1 : end_index + 1 + horizon]
        future_mean = future_window.mean(axis=0)
        future_quality = compute_quality_score(*future_mean)

        features.append(np.concatenate([window_features.reshape(-1), site_vector]))
        targets.append(np.array([*future_mean.tolist(), future_quality], dtype=float))
        target_times.append(timestamps[end_index + horizon])

    return DatasetBundle(
        features=np.vstack(features),
        targets=np.vstack(targets),
        target_times=np.array(target_times, dtype="datetime64[ns]"),
        feature_names=build_feature_names(lookback, site_names),
    )


def load_csv_file(csv_path: Path) -> pd.DataFrame:
    return pd.read_csv(csv_path)


def discover_csv_files(data_dir: Path | None = None) -> list[Path]:
    base_dir = data_dir or DATA_DIR
    if not base_dir.exists():
        return []
    return sorted(base_dir.glob("network_data*.csv"))


def load_training_data(data_dir: Path | None = None, lookback: int = 30, horizon: int = 15) -> tuple[DatasetBundle, list[str], list[str]]:
    csv_files = discover_csv_files(data_dir)
    if not csv_files:
        return DatasetBundle(
            features=np.empty((0, lookback * len(ROW_FEATURE_COLUMNS))),
            targets=np.empty((0, 5)),
            target_times=np.empty((0,), dtype="datetime64[ns]"),
            feature_names=build_feature_names(lookback),
        ), [], []

    site_keys = [site_key_from_path(csv_file) for csv_file in csv_files]
    site_feature_names = build_site_feature_names(site_keys)

    feature_parts: list[np.ndarray] = []
    target_parts: list[np.ndarray] = []
    time_parts: list[np.ndarray] = []
    used_files: list[str] = []

    for csv_file in csv_files:
        try:
            raw_frame = load_csv_file(csv_file)
            site_key = site_key_from_path(csv_file)
            site_vector = build_site_feature_vector(site_key, site_keys)
            bundle = build_window_samples(
                raw_frame,
                lookback=lookback,
                horizon=horizon,
                site_feature_vector=site_vector,
                site_feature_names=site_feature_names,
            )
            if bundle.features.size == 0:
                continue

            feature_parts.append(bundle.features)
            target_parts.append(bundle.targets)
            time_parts.append(bundle.target_times)
            used_files.append(csv_file.name)
        except Exception:
            continue

    if not feature_parts:
        return DatasetBundle(
            features=np.empty((0, lookback * len(ROW_FEATURE_COLUMNS) + len(site_feature_names))),
            targets=np.empty((0, 5)),
            target_times=np.empty((0,), dtype="datetime64[ns]"),
            feature_names=build_feature_names(lookback, site_feature_names),
        ), [], site_feature_names

    return (
        DatasetBundle(
            features=np.vstack(feature_parts),
            targets=np.vstack(target_parts),
            target_times=np.concatenate(time_parts),
            feature_names=build_feature_names(lookback, site_feature_names),
        ),
        used_files,
        site_feature_names,
    )


def save_model_bundle(model_path: Path, bundle: dict[str, Any]) -> None:
    ensure_directories()
    joblib.dump(bundle, model_path)


def load_model_bundle(model_path: Path) -> dict[str, Any]:
    return joblib.load(model_path)


def make_prediction_frame(csv_path: Path, lookback: int) -> pd.DataFrame:
    raw_frame = load_csv_file(csv_path)
    prepared = prepare_dataframe(raw_frame)
    if len(prepared) < lookback:
        return pd.DataFrame()
    return prepared.tail(lookback).reset_index(drop=True)


def make_prediction_features(csv_path: Path, model_bundle: dict[str, Any]) -> np.ndarray:
    lookback = int(model_bundle["lookback"])
    recent_frame = make_prediction_frame(csv_path, lookback=lookback)
    if recent_frame.empty or len(recent_frame) < lookback:
        return np.empty((0,), dtype=float)

    row_features = recent_frame[model_bundle["row_feature_columns"]].to_numpy(dtype=float).reshape(-1)
    site_feature_names = model_bundle.get("site_feature_names", [])
    site_keys = model_bundle.get("site_keys", [])
    site_vector = build_site_feature_vector(site_key_from_path(csv_path), list(site_keys)) if site_feature_names else np.empty((0,), dtype=float)
    return np.concatenate([row_features, site_vector])
