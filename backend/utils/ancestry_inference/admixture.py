import json
import os
from typing import Dict, List, Optional

from .plink import run_command


def run_admixture(admixture_bin: str, bed_path: str, k: int, threads: int, workdir: str) -> str:
    cmd = [admixture_bin, "--cv", "-j", str(threads), bed_path, str(k)]
    return run_command(cmd, workdir=workdir)


def parse_q_matrix(q_path: str, sample_ids: List[str], labels: List[str]) -> List[Dict[str, float]]:
    rows = []
    with open(q_path, "r", encoding="utf-8") as f:
        for idx, line in enumerate(f):
            parts = [float(p) for p in line.strip().split()]
            entry = {"sample_id": sample_ids[idx]}
            for j, label in enumerate(labels):
                entry[label] = parts[j]
            rows.append(entry)
    return rows


def save_admixture_cache(path: str, data: Dict):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def load_admixture_cache(path: str) -> Optional[Dict]:
    if not os.path.exists(path):
        return None
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)
