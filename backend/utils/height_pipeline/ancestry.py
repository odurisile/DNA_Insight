import csv
import hashlib
import math
import os
from typing import Dict, Iterable, Optional, Tuple

DEFAULT_ANCESTRIES = ("AFR", "EUR", "EAS", "SAS", "AMR", "NAT", "ADMIX", "UNK")
DEFAULT_AIMS_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "nih", "height_ancestry_aims.csv")
)


def _normalize_proportions(proportions: Dict[str, float]) -> Dict[str, float]:
    total = sum(v for v in proportions.values() if v is not None and v > 0)
    if total <= 0:
        return {}
    return {k: float(v) / total for k, v in proportions.items() if v is not None and v > 0}


def _stable_unit_interval(value: str) -> float:
    digest = hashlib.sha256(value.encode("utf-8")).hexdigest()
    return int(digest[:12], 16) / float(0xFFFFFFFFFFFF)


def assign_local_ancestry(
    rsids: Iterable[str],
    global_ancestry: Optional[Dict[str, float]] = None,
    local_ancestry_map: Optional[Dict[str, str]] = None,
) -> Dict[str, str]:
    """
    Returns per-SNP ancestry labels. If a local ancestry map is provided, it is used directly.
    Otherwise, a deterministic assignment is sampled from global proportions.
    """
    if local_ancestry_map:
        return {rsid: local_ancestry_map.get(rsid, "UNK") for rsid in rsids}

    weights = _normalize_proportions(global_ancestry or {})
    if not weights:
        return {rsid: "UNK" for rsid in rsids}

    labels = list(weights.keys())
    cumulative = []
    acc = 0.0
    for label in labels:
        acc += weights[label]
        cumulative.append(acc)

    ancestry_by_snp = {}
    for rsid in rsids:
        r = _stable_unit_interval(rsid)
        for idx, cutoff in enumerate(cumulative):
            if r <= cutoff:
                ancestry_by_snp[rsid] = labels[idx]
                break
        if rsid not in ancestry_by_snp:
            ancestry_by_snp[rsid] = labels[-1]
    return ancestry_by_snp


def ancestry_proportions_from_map(local_map: Dict[str, str]) -> Dict[str, float]:
    counts = {}
    for label in local_map.values():
        counts[label] = counts.get(label, 0) + 1
    total = sum(counts.values()) or 1
    return {k: v / total for k, v in counts.items()}


def _parse_float(value: Optional[str]) -> Optional[float]:
    if value is None or value == "":
        return None
    try:
        return float(value)
    except Exception:
        return None


def load_aims_panel(path: Optional[str] = None) -> Dict[str, Dict[str, float]]:
    filepath = path or DEFAULT_AIMS_PATH
    if not os.path.exists(filepath):
        return {}
    with open(filepath, "r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        panel = {}
        for row in reader:
            rsid = row.get("rsid")
            if not rsid:
                continue
            panel[rsid] = {
                "allele1": (row.get("allele1") or "").upper(),
                "allele2": (row.get("allele2") or "").upper(),
                "AFR": _parse_float(row.get("AFR")),
                "EUR": _parse_float(row.get("EUR")),
                "NAT": _parse_float(row.get("NAT")),
                "EAS": _parse_float(row.get("EAS")),
                "SAS": _parse_float(row.get("SAS")),
            }
        return panel


def _genotype_likelihood(geno: str, allele1: str, allele2: str, p: float) -> Optional[float]:
    if not geno or not allele1 or not allele2:
        return None
    alleles = list(geno.upper())
    if not set(alleles).issubset({allele1, allele2}):
        return None
    count1 = alleles.count(allele1)
    q = 1 - p
    if count1 == 2:
        return p * p
    if count1 == 1:
        return 2 * p * q
    return q * q


def infer_global_ancestry(
    genotype_map: Dict[str, str],
    aims_path: Optional[str] = None,
    min_snps: int = 25,
) -> Tuple[Dict[str, float], Dict[str, float]]:
    panel = load_aims_panel(aims_path)
    if not panel:
        return {"UNK": 1.0}, {"status": "missing_panel", "markers_used": 0}

    log_likelihoods = {"AFR": 0.0, "EUR": 0.0, "NAT": 0.0, "EAS": 0.0, "SAS": 0.0}
    markers_used = 0
    eps = 1e-6

    for rsid, meta in panel.items():
        geno = genotype_map.get(rsid)
        if not geno:
            continue
        allele1 = meta.get("allele1", "")
        allele2 = meta.get("allele2", "")
        if not allele1 or not allele2:
            continue
        usable = False
        for ancestry in log_likelihoods:
            p = meta.get(ancestry)
            if p is None:
                continue
            like = _genotype_likelihood(geno, allele1, allele2, p)
            if like is None:
                continue
            log_likelihoods[ancestry] += math.log(max(like, eps))
            usable = True
        if usable:
            markers_used += 1

    if markers_used < min_snps:
        return {"UNK": 1.0}, {"status": "insufficient_markers", "markers_used": markers_used}

    max_ll = max(log_likelihoods.values())
    weights = {k: math.exp(v - max_ll) for k, v in log_likelihoods.items()}
    total = sum(weights.values()) or 1.0
    proportions = {k: v / total for k, v in weights.items()}
    return proportions, {"status": "ok", "markers_used": markers_used}
