import json
import logging
from dataclasses import dataclass
from typing import Dict, Optional, Tuple

from ..height_pipeline.qc import percentile_from_z

LOGGER = logging.getLogger(__name__)


def _parse_scalar(value: str):
    if value is None:
        return None
    raw = value.strip()
    if raw == "":
        return ""
    lower = raw.lower()
    if lower in ("null", "none"):
        return None
    if lower in ("true", "false"):
        return lower == "true"
    try:
        if "." in raw or "e" in raw.lower():
            return float(raw)
        return int(raw)
    except ValueError:
        return raw


def _load_simple_yaml(path: str) -> Dict:
    """
    Minimal YAML loader for simple dict structures (no lists).
    """
    with open(path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    root: Dict = {}
    stack = [(0, root)]

    for line in lines:
        if "#" in line:
            line = line.split("#", 1)[0]
        if not line.strip():
            continue
        indent = len(line) - len(line.lstrip(" "))
        key_part, sep, value_part = line.strip().partition(":")
        if sep == "":
            continue
        key = key_part.strip()
        value = value_part.strip()

        while stack and indent < stack[-1][0]:
            stack.pop()
        if not stack:
            stack = [(0, root)]
        current = stack[-1][1]

        if value == "":
            current[key] = {}
            stack.append((indent + 2, current[key]))
        else:
            current[key] = _parse_scalar(value)

    return root


def _load_json(path: str) -> Dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_config(path: str) -> Dict:
    if path.lower().endswith(".json"):
        return _load_json(path)
    try:
        import yaml  # type: ignore
    except Exception:
        yaml = None
    if yaml is not None:
        with open(path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)
    return _load_simple_yaml(path)


@dataclass
class CalibrationOutput:
    predicted_height_cm: float
    z_score: float
    percentile: float
    sex_baseline: Dict[str, float]
    ancestry_adjustment: Dict[str, float]
    confidence_intervals: Dict[str, Tuple[float, float]]
    model_version: str
    bias_flags: Tuple[str, ...]


class HeightCalibrator:
    def __init__(
        self,
        config_path: str,
        model_path: Optional[str] = None,
    ):
        self.config = load_config(config_path)
        self.model_path = model_path
        self.model = None
        if model_path:
            self.model = self._load_model(model_path)

    def _load_model(self, path: str):
        try:
            import joblib  # type: ignore
        except Exception as exc:
            raise ImportError("joblib is required to load calibration models.") from exc
        return joblib.load(path)

    def _get_sex_stats(self, sex: str) -> Dict[str, float]:
        stats = self.config.get("sex_stats", {})
        if sex not in stats:
            raise ValueError(f"Missing sex stats for '{sex}'.")
        return stats[sex]

    def _get_ancestry_coeffs(self) -> Dict[str, float]:
        coeffs = self.config.get("ancestry_coefficients")
        if coeffs is None:
            raise ValueError("Missing ancestry_coefficients in calibration config.")
        return coeffs

    def _compute_sex_baseline(self, raw_pgs: float, sex: str) -> Dict[str, float]:
        stats = self._get_sex_stats(sex)
        mu = stats.get("mean_pgs")
        sd = stats.get("sd_pgs")
        mean_height = stats.get("mean_height_cm")
        sd_height = stats.get("sd_height_cm")
        if mu is None or sd is None or mean_height is None or sd_height is None:
            raise ValueError("Sex stats must include mean_pgs, sd_pgs, mean_height_cm, sd_height_cm.")
        z = (raw_pgs - mu) / (sd or 1.0)
        height_base = (z * sd_height) + mean_height
        return {
            "z_score": z,
            "height_base_cm": height_base,
            "mean_pgs": mu,
            "sd_pgs": sd,
            "mean_height_cm": mean_height,
            "sd_height_cm": sd_height,
        }

    def _compute_component_adjustment(
        self,
        height_base: float,
        sex: str,
        global_ancestry: Dict[str, float],
        ancestry_components: Optional[Dict[str, float]],
    ) -> Tuple[float, Dict[str, float]]:
        model_cfg = self.config.get("component_model")
        if not model_cfg:
            raise ValueError("component_model section required for component adjustment.")

        intercept = model_cfg.get("intercept", 0.0)
        height_coef = model_cfg.get("height_base_coef", 1.0)
        sex_binary = 1.0 if sex == "male" else 0.0

        total = intercept + height_coef * height_base + model_cfg.get("sex_binary_coef", 0.0) * sex_binary

        component_coefs = model_cfg.get("component_coefs", {})
        ancestry_coefs = model_cfg.get("ancestry_coefs", {})
        used = {}

        for key, coef in component_coefs.items():
            if ancestry_components and key in ancestry_components:
                total += coef * ancestry_components[key]
                used[key] = coef

        for key, coef in ancestry_coefs.items():
            if key in global_ancestry:
                total += coef * global_ancestry[key]
                used[key] = coef

        return total, {"mode": "component_linear", "coefficients": used}

    def _compute_ancestry_adjustment(
        self, height_base: float, global_ancestry: Dict[str, float]
    ) -> Tuple[float, Dict[str, float]]:
        coeffs = self._get_ancestry_coeffs()
        delta = 0.0
        for ancestry, coef in coeffs.items():
            prop = global_ancestry.get(ancestry, 0.0)
            delta += coef * prop
        return height_base + delta, {"mode": "ancestry_linear", "coefficients": coeffs, "delta_cm": delta}

    def _compute_confidence_intervals(
        self,
        predicted_height_cm: float,
        global_ancestry: Dict[str, float],
        imputation_rate: float = 0.0,
        residual_sd_cm: Optional[float] = None,
    ) -> Dict[str, Tuple[float, float]]:
        residual_sd_cm = residual_sd_cm or self.config.get("residual_sd_cm", 5.0)
        ancestry_penalty = sum(global_ancestry.values()) * self.config.get("ancestry_penalty", 0.0)
        total_sd = residual_sd_cm * (1.0 + ancestry_penalty + imputation_rate * 0.5)
        ci90 = 1.645 * total_sd
        ci95 = 1.96 * total_sd
        return {
            "ci90": (predicted_height_cm - ci90, predicted_height_cm + ci90),
            "ci95": (predicted_height_cm - ci95, predicted_height_cm + ci95),
        }

    def _bias_flags(
        self,
        height_base: float,
        predicted_height_cm: float,
        sex: str,
        global_ancestry: Dict[str, float],
    ) -> Tuple[str, ...]:
        flags = []
        afr = global_ancestry.get("AFR", 0.0)
        if afr >= 0.5 and predicted_height_cm - height_base < 2.0:
            flags.append("afr_under_correction")
        if sex == "male" and predicted_height_cm < 170.0:
            flags.append("male_underprediction_risk")
        return tuple(flags)

    def _log_drift(self, global_ancestry: Dict[str, float]):
        baseline = self.config.get("baseline_ancestry")
        if not baseline:
            return
        drift = {}
        for key, value in baseline.items():
            drift[key] = abs(global_ancestry.get(key, 0.0) - value)
        if drift and max(drift.values()) > 0.25:
            LOGGER.warning("Ancestry drift detected: %s", drift)

    def calibrate(
        self,
        raw_pgs: float,
        sex: str,
        global_ancestry: Dict[str, float],
        ancestry_pgs_components: Optional[Dict[str, float]] = None,
        imputation_rate: float = 0.0,
    ) -> CalibrationOutput:
        if sex not in ("male", "female"):
            raise ValueError("sex must be 'male' or 'female'")

        self._log_drift(global_ancestry)

        baseline = self._compute_sex_baseline(raw_pgs, sex)
        height_base = baseline["height_base_cm"]

        if self.model is not None:
            features = self._build_model_features(
                height_base=height_base,
                sex=sex,
                global_ancestry=global_ancestry,
                ancestry_components=ancestry_pgs_components,
            )
            predicted_height = float(self.model.predict([features])[0])
            adjustment_info = {"mode": "trained_model", "features": features}
        else:
            component_mode = self.config.get("component_model") and ancestry_pgs_components
            if component_mode:
                predicted_height, adjustment_info = self._compute_component_adjustment(
                    height_base, sex, global_ancestry, ancestry_pgs_components
                )
            else:
                predicted_height, adjustment_info = self._compute_ancestry_adjustment(
                    height_base, global_ancestry
                )

        z_score = baseline["z_score"]
        percentile = percentile_from_z(z_score)
        ci = self._compute_confidence_intervals(
            predicted_height, global_ancestry, imputation_rate=imputation_rate
        )
        flags = self._bias_flags(height_base, predicted_height, sex, global_ancestry)
        if flags:
            LOGGER.warning("Bias flags triggered: %s", ",".join(flags))

        return CalibrationOutput(
            predicted_height_cm=predicted_height,
            z_score=z_score,
            percentile=percentile,
            sex_baseline=baseline,
            ancestry_adjustment=adjustment_info,
            confidence_intervals=ci,
            model_version=str(self.config.get("model_version", "unknown")),
            bias_flags=flags,
        )

    def _build_model_features(
        self,
        height_base: float,
        sex: str,
        global_ancestry: Dict[str, float],
        ancestry_components: Optional[Dict[str, float]],
    ):
        features = [height_base]
        sex_binary = 1.0 if sex == "male" else 0.0
        features.append(sex_binary)
        for key in ("AFR", "EUR", "NAT", "EAS", "SAS"):
            features.append(float(global_ancestry.get(key, 0.0)))
        if ancestry_components:
            for key in sorted(ancestry_components.keys()):
                features.append(float(ancestry_components[key]))
        return features

    @staticmethod
    def components_from_local_ancestry(
        local_ancestry_segments: Dict[str, str],
        per_snp_scores: Dict[str, float],
    ) -> Dict[str, float]:
        """
        Aggregate per-SNP scores into ancestry-specific components.
        local_ancestry_segments: {rsid: ancestry_label}
        per_snp_scores: {rsid: score}
        """
        components: Dict[str, float] = {}
        for rsid, ancestry in local_ancestry_segments.items():
            if rsid not in per_snp_scores:
                continue
            key = f"{ancestry}_score"
            components[key] = components.get(key, 0.0) + per_snp_scores[rsid]
        return components
