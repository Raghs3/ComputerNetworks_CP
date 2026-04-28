from __future__ import annotations

import argparse
import os
import time
from pathlib import Path

import numpy as np

from network_quality_ml import (
    DATA_DIR,
    DEFAULT_MODEL_PATH,
    compute_quality_score,
    load_model_bundle,
    make_prediction_features,
    quality_band,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Predict next 10-15 seconds of network quality in real time.")
    parser.add_argument("--csv", type=Path, required=True, help="CSV file that network_monitor.py is writing")
    parser.add_argument("--model-path", type=Path, default=DEFAULT_MODEL_PATH, help="Trained model bundle")
    parser.add_argument("--poll-interval", type=float, default=1.0, help="Seconds between prediction updates")
    parser.add_argument("--auto-reload", action="store_true", help="Reload the model file when it changes; does not change the CSV file")
    return parser.parse_args()


def load_model(model_path: Path, cached_mtime: float | None = None) -> tuple[dict, float]:
    model_bundle = load_model_bundle(model_path)
    model_mtime = os.path.getmtime(model_path)
    if cached_mtime is not None and model_mtime == cached_mtime:
        return model_bundle, cached_mtime
    return model_bundle, model_mtime


def predict_once(csv_path: Path, model_bundle: dict) -> bool:
    lookback = int(model_bundle["lookback"])
    horizon = int(model_bundle["horizon"])
    model = model_bundle["model"]

    features = make_prediction_features(csv_path, model_bundle)
    if features.size == 0:
        recent_rows = 0
        try:
            with csv_path.open("r", encoding="utf-8") as handle:
                recent_rows = sum(1 for _ in handle) - 1
        except Exception:
            recent_rows = 0
        print(f"Collecting warm-up data from {csv_path.name}: {recent_rows}/{lookback} rows available")
        return False

    predicted = model.predict(features.reshape(1, -1))[0]

    predicted_rtt = float(predicted[0])
    predicted_jitter = float(predicted[1])
    predicted_loss = float(predicted[2])
    predicted_throughput = float(predicted[3])
    predicted_quality = float(np.clip(predicted[4], 0.0, 100.0))

    derived_quality = compute_quality_score(predicted_rtt, predicted_jitter, predicted_loss, predicted_throughput)
    band = quality_band(predicted_quality)
    is_good_next_window = band in {"Excellent", "Good"}
    good_text = "Yes" if is_good_next_window else "No"
    is_likely_working = predicted_loss < 2.0 and predicted_rtt < 300.0
    working_text = "Likely Working" if is_likely_working else "Likely Degraded"

    print("\n" + "=" * 72)
    print(f"Next {horizon} second forecast for {csv_path.name}")
    print("=" * 72)
    print(f"Predicted RTT:            {predicted_rtt:.2f} ms")
    print(f"Predicted Jitter:         {predicted_jitter:.2f} ms")
    print(f"Predicted Packet Loss:    {predicted_loss:.2f} %")
    print(f"Predicted Throughput:     {predicted_throughput:.2f} Kbps")
    print(f"Predicted Quality Score:  {predicted_quality:.2f} / 100 ({band})")
    print(f"Network Quality Status:   {band}")
    print(f"Network Good Next {horizon}s: {good_text}")
    print(f"Website Availability:     {working_text}")
    print(f"Derived Quality Check:    {derived_quality:.2f} / 100")
    print("=" * 72)
    return True


def main() -> None:
    args = parse_args()

    if not args.csv.exists():
        raise FileNotFoundError(f"CSV file not found: {args.csv}")

    model_bundle, model_mtime = load_model(args.model_path)
    print(f"Loaded model: {args.model_path}")
    print(f"Watching CSV:  {args.csv}")
    print("Press Ctrl+C to stop.")

    last_prediction_count = -1
    while True:
        try:
            if args.auto_reload:
                refreshed_bundle, refreshed_mtime = load_model(args.model_path, model_mtime)
                if refreshed_mtime != model_mtime:
                    model_bundle = refreshed_bundle
                    model_mtime = refreshed_mtime
                    print(f"Reloaded model at {time.strftime('%H:%M:%S')}")

            current_rows = 0
            try:
                with args.csv.open("r", encoding="utf-8") as handle:
                    current_rows = sum(1 for _ in handle) - 1
            except Exception:
                current_rows = 0

            if current_rows != last_prediction_count:
                predict_once(args.csv, model_bundle)
                last_prediction_count = current_rows

            time.sleep(max(args.poll_interval, 0.5))
        except KeyboardInterrupt:
            print("\nStopped.")
            return


if __name__ == "__main__":
    main()
