import os
from typing import Dict, List, Tuple


def load_pcs(eigenvec_path: str, pcs: int) -> List[Dict]:
    rows = []
    with open(eigenvec_path, "r", encoding="utf-8") as f:
        for line in f:
            parts = line.strip().split()
            if len(parts) < pcs + 2:
                continue
            sample_id = parts[1]
            pc_values = [float(parts[i + 2]) for i in range(pcs)]
            rows.append({"sample_id": sample_id, "pcs": pc_values})
    return rows


def cache_reference_pcs(cache_path: str, pcs: List[Dict]):
    os.makedirs(os.path.dirname(cache_path), exist_ok=True)
    with open(cache_path, "w", encoding="utf-8") as f:
        for row in pcs:
            line = row["sample_id"] + "\t" + "\t".join(str(v) for v in row["pcs"])
            f.write(line + "\n")


def load_cached_reference_pcs(cache_path: str) -> List[Dict]:
    if not os.path.exists(cache_path):
        return []
    pcs = []
    with open(cache_path, "r", encoding="utf-8") as f:
        for line in f:
            parts = line.strip().split("\t")
            if len(parts) < 2:
                continue
            pcs.append({"sample_id": parts[0], "pcs": [float(v) for v in parts[1:]]})
    return pcs


def project_user_on_reference(user_pcs: List[float], reference_pcs: List[Dict]) -> Tuple[List[float], float]:
    if not reference_pcs:
        return user_pcs, 0.0
    distances = []
    for row in reference_pcs:
        ref = row["pcs"]
        dist = sum((u - r) ** 2 for u, r in zip(user_pcs, ref)) ** 0.5
        distances.append(dist)
    min_dist = min(distances) if distances else 0.0
    return user_pcs, min_dist
