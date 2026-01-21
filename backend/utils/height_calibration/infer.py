import argparse
import json

from .calibrator import HeightCalibrator


def main():
    parser = argparse.ArgumentParser(description="Run height calibration inference.")
    parser.add_argument("--config", required=True, help="Calibration config YAML/JSON.")
    parser.add_argument("--model", help="Optional joblib model path.")
    parser.add_argument("--input-json", required=True, help="JSON with raw_PGS, sex, global_ancestry, ancestry_PGS_components.")
    args = parser.parse_args()

    with open(args.input_json, "r", encoding="utf-8") as f:
        payload = json.load(f)

    calibrator = HeightCalibrator(config_path=args.config, model_path=args.model)
    result = calibrator.calibrate(
        raw_pgs=float(payload["raw_PGS"]),
        sex=payload["sex"],
        global_ancestry=payload.get("global_ancestry", {}),
        ancestry_pgs_components=payload.get("ancestry_PGS_components"),
        imputation_rate=float(payload.get("imputation_rate", 0.0)),
    )

    output = {
        "predicted_height_cm": result.predicted_height_cm,
        "z_score": result.z_score,
        "percentile": result.percentile,
        "sex_baseline": result.sex_baseline,
        "ancestry_adjustment": result.ancestry_adjustment,
        "confidence_intervals": {
            "ci90": list(result.confidence_intervals["ci90"]),
            "ci95": list(result.confidence_intervals["ci95"]),
        },
        "model_version": result.model_version,
        "bias_flags": list(result.bias_flags),
    }
    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()
