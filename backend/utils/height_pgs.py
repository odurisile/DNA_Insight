from typing import Dict, Optional, Tuple

from .height_pipeline import compute_height_pgs_v2, harmonize_and_dosage, normalize_genome
from .height_pipeline.qc import percentile_from_z


def compute_height_pgs(
    genome: Dict[str, Dict],
    weights_path: Optional[str] = None,
    sex: str = "unspecified",
    global_ancestry: Optional[Dict[str, float]] = None,
    local_ancestry_map: Optional[Dict[str, str]] = None,
    calibration_config_path: Optional[str] = None,
    calibration_model_path: Optional[str] = None,
    observed_height_cm: Optional[float] = None,
):
    return compute_height_pgs_v2(
        genome=genome,
        sex=sex,
        global_ancestry=global_ancestry,
        local_ancestry_map=local_ancestry_map,
        weights_path=weights_path,
        calibration_config_path=calibration_config_path,
        calibration_model_path=calibration_model_path,
        observed_height_cm=observed_height_cm,
    )
