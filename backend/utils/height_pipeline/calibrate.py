from typing import Dict, Optional, Tuple


DEFAULT_SEX_PGS_STATS = {
    "male": {"mu": 0.0, "sigma": 1.0},
    "female": {"mu": 0.0, "sigma": 1.0},
    "unspecified": {"mu": 0.0, "sigma": 1.0},
}

DEFAULT_HEIGHT_STATS = {
    "male": {"mean_cm": 176.0, "sd_cm": 7.0},
    "female": {"mean_cm": 162.0, "sd_cm": 6.5},
    "unspecified": {"mean_cm": 169.0, "sd_cm": 7.0},
}

DEFAULT_ADMIXED_CALIBRATION = {"a": 1.0, "b": 0.0}


def sex_specific_z(
    raw_pgs: float,
    sex: str,
    sex_pgs_stats: Optional[Dict[str, Dict[str, float]]] = None,
) -> float:
    stats = (sex_pgs_stats or DEFAULT_SEX_PGS_STATS).get(sex, DEFAULT_SEX_PGS_STATS["unspecified"])
    mu = stats.get("mu", 0.0)
    sigma = stats.get("sigma", 1.0) or 1.0
    return (raw_pgs - mu) / sigma


def rescale_to_height_cm(
    z: float,
    sex: str,
    height_stats: Optional[Dict[str, Dict[str, float]]] = None,
) -> float:
    stats = (height_stats or DEFAULT_HEIGHT_STATS).get(sex, DEFAULT_HEIGHT_STATS["unspecified"])
    return stats.get("mean_cm", 169.0) + z * stats.get("sd_cm", 7.0)


def admixed_linear_calibration(
    height_cm: float,
    ancestry_props: Optional[Dict[str, float]],
    calibration_by_ancestry: Optional[Dict[str, Dict[str, float]]] = None,
) -> Tuple[float, Dict[str, float]]:
    calibration_by_ancestry = calibration_by_ancestry or {}
    if not ancestry_props:
        a = DEFAULT_ADMIXED_CALIBRATION["a"]
        b = DEFAULT_ADMIXED_CALIBRATION["b"]
        return a * height_cm + b, {"a": a, "b": b, "source": "default"}

    total = sum(v for v in ancestry_props.values() if v is not None and v > 0)
    if total <= 0:
        a = DEFAULT_ADMIXED_CALIBRATION["a"]
        b = DEFAULT_ADMIXED_CALIBRATION["b"]
        return a * height_cm + b, {"a": a, "b": b, "source": "default"}

    a_mix = 0.0
    b_mix = 0.0
    for ancestry, prop in ancestry_props.items():
        if prop is None or prop <= 0:
            continue
        calib = calibration_by_ancestry.get(ancestry, DEFAULT_ADMIXED_CALIBRATION)
        a_mix += prop * calib.get("a", 1.0)
        b_mix += prop * calib.get("b", 0.0)

    a_mix = a_mix / total
    b_mix = b_mix / total
    return a_mix * height_cm + b_mix, {"a": a_mix, "b": b_mix, "source": "ancestry_weighted"}
