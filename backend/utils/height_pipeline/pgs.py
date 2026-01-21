import csv
import os
from typing import Dict, List, Optional, Tuple

from .qc import harmonize_and_dosage

DEFAULT_WEIGHTS_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "nih", "height_demo_weights.csv")
)


def load_ancestry_weights(path: Optional[str] = None) -> List[Dict]:
    """
    Load PGS weights with optional ancestry-specific betas.
    Expected columns:
      rsid, effect_allele, other_allele, beta, eaf, beta_eur, beta_afr, beta_eas, ...
    """
    filepath = path or DEFAULT_WEIGHTS_PATH
    weights = []
    with open(filepath, "r", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rsid = row.get("rsid")
            if not rsid:
                continue
            betas = {}
            for key, value in row.items():
                if not key:
                    continue
                key_lower = key.lower()
                if key_lower.startswith("beta_") and value not in (None, ""):
                    ancestry = key_lower.replace("beta_", "").upper()
                    try:
                        betas[ancestry] = float(value)
                    except Exception:
                        continue
            beta_fallback = None
            if row.get("beta"):
                try:
                    beta_fallback = float(row["beta"])
                except Exception:
                    beta_fallback = None
            weights.append(
                {
                    "rsid": rsid,
                    "effect": row.get("effect_allele", "").upper(),
                    "other": row.get("other_allele", "").upper(),
                    "beta_fallback": beta_fallback,
                    "betas": betas,
                    "eaf": float(row["eaf"]) if row.get("eaf") else None,
                }
            )
    if not weights:
        raise ValueError(f"No weights loaded from {filepath}")
    return weights


def _select_beta(betas: Dict[str, float], ancestry: str, fallback: Optional[float]) -> Optional[float]:
    if ancestry and ancestry in betas:
        return betas[ancestry]
    return fallback


def compute_weighted_pgs(
    genotype_map: Dict[str, str],
    weights: List[Dict],
    local_ancestry: Dict[str, str],
) -> Tuple[float, Dict[str, float], Dict[str, int], List[Dict]]:
    snps_total = len(weights)
    snps_found = 0
    snps_used = 0
    ambiguous_removed = 0
    imputed_count = 0

    pgs_raw = 0.0
    ancestry_scores: Dict[str, float] = {}
    ancestry_counts: Dict[str, int] = {}
    snp_details = []

    for w in weights:
        rsid = w["rsid"]
        effect = w["effect"]
        other = w["other"]
        geno = genotype_map.get(rsid)
        ancestry = local_ancestry.get(rsid, "UNK")

        detail = {"rsid": rsid, "ancestry": ancestry}

        if geno:
            snps_found += 1
            detail["genotype"] = geno
            status, dosage = harmonize_and_dosage(geno, effect, other)
            if status == "ambiguous":
                ambiguous_removed += 1
                detail["status"] = "ambiguous"
                continue
            if status == "skip" or dosage is None:
                detail["status"] = "skipped"
                continue
            detail["status"] = "used"
        else:
            if w["eaf"] is not None:
                dosage = 2 * w["eaf"]
                detail["status"] = "imputed"
                detail["genotype"] = None
                imputed_count += 1
            else:
                detail["status"] = "missing"
                continue

        beta = _select_beta(w["betas"], ancestry, w["beta_fallback"])
        if beta is None:
            detail["status"] = "missing_beta"
            continue

        snps_used += 1
        score = beta * dosage
        pgs_raw += score
        ancestry_scores[ancestry] = ancestry_scores.get(ancestry, 0.0) + score
        ancestry_counts[ancestry] = ancestry_counts.get(ancestry, 0) + 1
        detail["dosage"] = dosage
        detail["beta"] = beta
        detail["effect"] = effect
        snp_details.append(detail)

    coverage = snps_used / snps_total if snps_total > 0 else 0
    missing_rate = 1 - coverage if snps_total > 0 else 1
    imputed_rate = imputed_count / snps_total if snps_total > 0 else 0

    qc = {
        "snps_total": snps_total,
        "snps_found": snps_found,
        "snps_used": snps_used,
        "missing_rate": missing_rate,
        "ambiguous_removed": ambiguous_removed,
        "imputed_rate": imputed_rate,
    }

    return pgs_raw, ancestry_scores, qc, snp_details
