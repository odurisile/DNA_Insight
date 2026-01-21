import argparse
import csv
import json
from typing import Dict, List

from .calibrator import load_config
from .metrics import mae, r2_score, stratified_errors


def _sex_baseline(raw_pgs: float, sex: str, config: Dict) -> float:
    stats = config["sex_stats"][sex]
    z = (raw_pgs - stats["mean_pgs"]) / (stats["sd_pgs"] or 1.0)
    return z * stats["sd_height_cm"] + stats["mean_height_cm"]


def _build_features(row: Dict[str, float], height_base: float, include_components: bool) -> List[float]:
    features = [height_base, 1.0 if row["sex"] == "male" else 0.0]
    for key in ("AFR", "EUR", "NAT", "EAS", "SAS"):
        features.append(float(row.get(key, 0.0)))
    if include_components:
        component_keys = sorted([k for k in row if k.endswith("_score")])
        for key in component_keys:
            features.append(float(row.get(key, 0.0)))
    return features


def _load_rows(path: str) -> List[Dict]:
    with open(path, "r", newline="") as f:
        reader = csv.DictReader(f)
        rows = []
        for row in reader:
            rows.append({k: (float(v) if k not in ("sex",) else v) for k, v in row.items()})
        return rows


def main():
    parser = argparse.ArgumentParser(description="Train height calibration model.")
    parser.add_argument("--input", required=True, help="CSV with raw_pgs, sex, height_cm, ancestry proportions.")
    parser.add_argument("--config", required=True, help="Calibration config YAML/JSON.")
    parser.add_argument("--output-model", required=True, help="Path to save joblib model.")
    parser.add_argument("--model-type", choices=("linear", "ridge", "isotonic"), default="linear")
    parser.add_argument("--output-metrics", required=True, help="Path to save JSON metrics.")
    args = parser.parse_args()

    config = load_config(args.config)
    rows = _load_rows(args.input)

    include_components = any(k.endswith("_score") for k in rows[0].keys())
    X = []
    y = []
    for row in rows:
        height_base = _sex_baseline(row["raw_pgs"], row["sex"], config)
        X.append(_build_features(row, height_base, include_components))
        y.append(row["height_cm"])

    if args.model_type in ("linear", "ridge"):
        try:
            from sklearn.linear_model import LinearRegression, Ridge  # type: ignore
        except Exception as exc:
            raise ImportError("scikit-learn is required for linear/ridge training.") from exc
        model = LinearRegression() if args.model_type == "linear" else Ridge(alpha=1.0)
        model.fit(X, y)
        y_pred = model.predict(X)
    else:
        try:
            from sklearn.isotonic import IsotonicRegression  # type: ignore
        except Exception as exc:
            raise ImportError("scikit-learn is required for isotonic training.") from exc
        model = IsotonicRegression(out_of_bounds="clip")
        model.fit([row[0] for row in X], y)
        y_pred = model.predict([row[0] for row in X])

    try:
        import joblib  # type: ignore
    except Exception as exc:
        raise ImportError("joblib is required to save calibration models.") from exc
    joblib.dump(model, args.output_model)

    metrics = {
        "r2": r2_score(y, y_pred),
        "mae": mae(y, y_pred),
        "ancestry_stratified": stratified_errors(
            [
                {**rows[idx], "height_cm": y[idx], "predicted_height_cm": float(y_pred[idx])}
                for idx in range(len(rows))
            ]
        ),
    }
    with open(args.output_metrics, "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2)


if __name__ == "__main__":
    main()
