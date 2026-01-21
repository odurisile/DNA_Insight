import os
from typing import Dict, Optional

from .ancestry import assign_local_ancestry, ancestry_proportions_from_map, infer_global_ancestry
from .pgs import compute_weighted_pgs, load_ancestry_weights
from .qc import normalize_genome
from ..height_calibration import HeightCalibrator


def compute_height_pgs_v2(
    genome: Dict,
    sex: str = "unspecified",
    global_ancestry: Optional[Dict[str, float]] = None,
    local_ancestry_map: Optional[Dict[str, str]] = None,
    weights_path: Optional[str] = None,
    calibration_config_path: Optional[str] = None,
    calibration_model_path: Optional[str] = None,
    observed_height_cm: Optional[float] = None,
):
    weights = load_ancestry_weights(weights_path)
    genotype_map = normalize_genome(genome)

    ancestry_inference = None
    if not global_ancestry:
        global_ancestry, ancestry_inference = infer_global_ancestry(genotype_map)

    local_ancestry = assign_local_ancestry(
        genotype_map.keys(), global_ancestry=global_ancestry, local_ancestry_map=local_ancestry_map
    )
    if not global_ancestry or "UNK" in global_ancestry:
        global_ancestry = ancestry_proportions_from_map(local_ancestry)

    raw_pgs, ancestry_scores, qc_metrics, snp_details = compute_weighted_pgs(
        genotype_map, weights, local_ancestry
    )

    if not calibration_config_path:
        calibration_config_path = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "..", "height_calibration", "config.yaml")
        )
    ancestry_pgs_components = {f"{k}_score": v for k, v in ancestry_scores.items()}
    calibrator = HeightCalibrator(
        config_path=calibration_config_path, model_path=calibration_model_path
    )
    calibration = calibrator.calibrate(
        raw_pgs=raw_pgs,
        sex=sex if sex in ("male", "female") else "male",
        global_ancestry=global_ancestry or {},
        ancestry_pgs_components=ancestry_pgs_components or None,
        imputation_rate=qc_metrics.get("imputed_rate", 0.0),
    )
    height_cm_cal = calibration.predicted_height_cm
    pgs_z = calibration.z_score
    percentile = calibration.percentile

    ci90 = {
        "low": calibration.confidence_intervals["ci90"][0],
        "high": calibration.confidence_intervals["ci90"][1],
    }
    ci95 = {
        "low": calibration.confidence_intervals["ci95"][0],
        "high": calibration.confidence_intervals["ci95"][1],
    }

    tier = "high"
    reason_parts = []
    warnings = []
    coverage = 1 - qc_metrics.get("missing_rate", 1)
    if coverage < 0.85:
        tier = "moderate"
        reason_parts.append(f"Coverage {coverage:.2f}")
    if coverage < 0.60:
        tier = "low"
        reason_parts.append(f"Low coverage {coverage:.2f}")
    if qc_metrics.get("ambiguous_removed", 0) > 0:
        warnings.append(
            f"Removed {qc_metrics.get('ambiguous_removed')} ambiguous SNPs (A/T or C/G)."
        )
    if ancestry_inference and ancestry_inference.get("status") != "ok":
        warnings.append(
            f"Ancestry inference {ancestry_inference.get('status')} (markers used {ancestry_inference.get('markers_used')})."
        )
    if tier == "high" and (not global_ancestry or "UNK" in global_ancestry):
        tier = "moderate"
        reason_parts.append("Ancestry unknown; default reference used.")

    ancestry_confidence = {
        "tier": tier,
        "reason": ", ".join(reason_parts) or f"Coverage {coverage:.2f}",
        "calibration_note": calibration.ancestry_adjustment.get("mode", "unknown"),
    }

    ancestry_height_components = ancestry_scores

    debug_tools = {}
    if observed_height_cm is not None:
        delta = height_cm_cal - observed_height_cm
        debug_tools = {
            "observed_height_cm": observed_height_cm,
            "prediction_error_cm": delta,
            "abs_error_cm": abs(delta),
            "bias_flag": abs(delta) >= 8.0,
        }
        if abs(delta) >= 8.0:
            warnings.append("Prediction error >= 8 cm; review ancestry calibration or weights.")

    return {
        "pgs_raw": raw_pgs,
        "pgs_z": pgs_z,
        "percentile": percentile,
        "predicted_height_cm": height_cm_cal,
        "predicted_height_cm_mean": height_cm_cal,
        "predicted_height_cm_sd_total": ci95["high"] - ci95["low"],
        "predicted_height_cm_ci90": ci90,
        "predicted_height_cm_ci95": ci95,
        "coverage": qc_metrics,
        "ancestry_confidence": ancestry_confidence,
        "warnings": warnings,
        "snp_details": snp_details,
        "ancestry_breakdown": global_ancestry,
        "ancestry_height_components": ancestry_height_components,
        "qc_report": {
            "missing_rate": qc_metrics.get("missing_rate"),
            "imputed_rate": qc_metrics.get("imputed_rate"),
            "ambiguous_removed": qc_metrics.get("ambiguous_removed"),
            "ancestry_inference": ancestry_inference,
        },
        "calibration": {
            "sex": sex,
            "admixed": calibration.ancestry_adjustment,
            "model_version": calibration.model_version,
        },
        "confidence_intervals": {
            "ci90": ci90,
            "ci95": ci95,
        },
        "sex_baseline": calibration.sex_baseline,
        "bias_flags": list(calibration.bias_flags),
        "debug_tools": debug_tools,
    }
