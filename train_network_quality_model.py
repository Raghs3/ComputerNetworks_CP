from __future__ import annotations

import argparse
import time
from pathlib import Path

import numpy as np
from sklearn.ensemble import ExtraTreesRegressor, RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

from network_quality_ml import (
    DEFAULT_MODEL_PATH,
    DATA_DIR,
    DatasetBundle,
    ROW_FEATURE_COLUMNS,
    TARGET_COLUMNS,
    build_feature_names,
    compute_quality_score,
    ensure_directories,
    load_training_data,
    save_model_bundle,
)


def collect_data_state(data_dir: Path) -> tuple[tuple[str, int, int], ...]:
    state: list[tuple[str, int, int]] = []
    for csv_file in sorted(data_dir.glob("network_data*.csv")):
        if not csv_file.is_file():
            continue
        stat_result = csv_file.stat()
        state.append((csv_file.name, int(stat_result.st_size), int(stat_result.st_mtime_ns)))
    return tuple(state)


def evaluate_predictions(y_true: np.ndarray, y_pred: np.ndarray) -> dict[str, float]:
    metrics: dict[str, float] = {}
    target_names = [*TARGET_COLUMNS, "Future Quality Score"]

    for index, target_name in enumerate(target_names):
        actual = y_true[:, index]
        predicted = y_pred[:, index]
        metrics[f"{target_name} MAE"] = float(mean_absolute_error(actual, predicted))
        metrics[f"{target_name} RMSE"] = float(np.sqrt(mean_squared_error(actual, predicted)))
        metrics[f"{target_name} R2"] = float(r2_score(actual, predicted))

    metrics["Overall MAE"] = float(mean_absolute_error(y_true, y_pred))
    metrics["Overall RMSE"] = float(np.sqrt(mean_squared_error(y_true, y_pred)))
    return metrics


def build_candidates(n_estimators: int) -> list[tuple[str, object]]:
    return [
        (
            "RandomForestRegressor",
            RandomForestRegressor(
                n_estimators=n_estimators,
                random_state=42,
                n_jobs=-1,
                min_samples_leaf=2,
            ),
        ),
        (
            "ExtraTreesRegressor",
            ExtraTreesRegressor(
                n_estimators=n_estimators,
                random_state=42,
                n_jobs=-1,
                min_samples_leaf=1,
            ),
        ),
    ]


def train_once(data_dir: Path, model_path: Path, lookback: int, horizon: int, test_ratio: float, n_estimators: int) -> dict[str, float]:
    dataset, used_files, site_feature_names = load_training_data(data_dir=data_dir, lookback=lookback, horizon=horizon)
    if dataset.features.size == 0:
        raise RuntimeError(
            f"No training samples were found in {data_dir}. Collect more data with network_monitor.py first."
        )

    order = np.argsort(dataset.target_times)
    X = dataset.features[order]
    y = dataset.targets[order]

    split_index = max(int(len(X) * (1.0 - test_ratio)), 1)
    if split_index >= len(X):
        split_index = len(X) - 1

    X_train, X_test = X[:split_index], X[split_index:]
    y_train, y_test = y[:split_index], y[split_index:]

    if len(X_test) == 0:
        X_train, X_test = X[:-1], X[-1:]
        y_train, y_test = y[:-1], y[-1:]        

    best_model = None
    best_metrics: dict[str, float] | None = None
    best_name = ""

    for candidate_name, candidate_model in build_candidates(n_estimators):
        candidate_model.fit(X_train, y_train)
        y_pred = candidate_model.predict(X_test)
        candidate_metrics = evaluate_predictions(y_test, y_pred)

        if best_metrics is None or candidate_metrics["Overall RMSE"] < best_metrics["Overall RMSE"]:
            best_model = candidate_model
            best_metrics = candidate_metrics
            best_name = candidate_name

    assert best_model is not None
    assert best_metrics is not None

    bundle = {
        "model": best_model,
        "model_name": best_name,
        "lookback": lookback,
        "horizon": horizon,
        "row_feature_columns": ROW_FEATURE_COLUMNS,
        "feature_names": build_feature_names(lookback),
        "target_columns": [*TARGET_COLUMNS, "Future Quality Score"],
        "metrics": best_metrics,
        "trained_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "source_files": used_files,
        "data_dir": str(data_dir),
        "site_feature_names": site_feature_names,
        "site_keys": [name.removeprefix("site__") for name in site_feature_names],
    }
    save_model_bundle(model_path, bundle)

    print("\nTraining complete")
    print(f"Model saved to: {model_path}")
    print(f"Best model: {best_name}")
    print(f"Rows trained on: {len(X_train)}")
    print(f"Rows tested on:  {len(X_test)}")
    print("\nMetrics:")
    for key, value in best_metrics.items():
        print(f"  {key}: {value:.4f}")

    return best_metrics


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Train a network quality forecasting model from CSV data.")
    parser.add_argument("--data-dir", type=Path, default=DATA_DIR, help="Folder with network_data*.csv files")
    parser.add_argument("--model-path", type=Path, default=DEFAULT_MODEL_PATH, help="Where to save the trained model")
    parser.add_argument("--lookback", type=int, default=30, help="Seconds of history used as input")
    parser.add_argument("--horizon", type=int, default=15, help="Seconds ahead to predict")
    parser.add_argument("--test-ratio", type=float, default=0.2, help="Fraction of samples reserved for testing")
    parser.add_argument("--n-estimators", type=int, default=300, help="Number of trees in the random forest")
    parser.add_argument("--watch", action="store_true", help="Keep retraining as new CSV data arrives")
    parser.add_argument("--once", action="store_true", help="Train a single time and exit")
    parser.add_argument("--interval", type=int, default=60, help="Seconds between retraining cycles while watching")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    ensure_directories()
    watch_mode = args.watch or not args.once

    if watch_mode:
        print("Watching for new data. Press Ctrl+C to stop.")
        last_data_state: tuple[tuple[str, int, int], ...] | None = None
        while True:
            try:
                current_data_state = collect_data_state(args.data_dir)
                if current_data_state == last_data_state:
                    print(f"No dataset changes detected at {time.strftime('%H:%M:%S')}; skipping retrain.")
                    time.sleep(max(args.interval, 5))
                    continue

                train_once(
                    data_dir=args.data_dir,
                    model_path=args.model_path,
                    lookback=args.lookback,
                    horizon=args.horizon,
                    test_ratio=args.test_ratio,
                    n_estimators=args.n_estimators,
                )
                last_data_state = current_data_state
            except Exception as error:
                print(f"Training skipped: {error}")
            time.sleep(max(args.interval, 5))
    else:
        train_once(
            data_dir=args.data_dir,
            model_path=args.model_path,
            lookback=args.lookback,
            horizon=args.horizon,
            test_ratio=args.test_ratio,
            n_estimators=args.n_estimators,
        )


if __name__ == "__main__":
    main()
