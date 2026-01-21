import math
from typing import Dict


def estimate_uncertainty(
    genetic_sd_cm: float,
    residual_sd_cm: float,
    qc_metrics: Dict[str, float],
    ancestry_variance: float = 0.0,
) -> Dict[str, float]:
    base_sd = math.sqrt(genetic_sd_cm ** 2 + residual_sd_cm ** 2)
    missing_rate = qc_metrics.get("missing_rate", 0.0)
    imputed_rate = qc_metrics.get("imputed_rate", 0.0)

    penalty = 1.0 + (missing_rate * 0.5) + (imputed_rate * 0.2) + (ancestry_variance * 0.1)
    total_sd = base_sd * penalty

    ci90 = 1.645 * total_sd
    ci95 = 1.96 * total_sd

    return {
        "total_sd_cm": total_sd,
        "ci90": ci90,
        "ci95": ci95,
        "penalty_factor": penalty,
    }
