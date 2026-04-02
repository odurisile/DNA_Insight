import os
import math
from typing import Dict, List, Tuple


def load_pcs(eigenvec_path: str, pcs: int) -> List[Dict]:
    """
    Load PLINK .eigenvec output.

    Expected format per line:
        FID IID PC1 PC2 ... PCn
    """
    rows: List[Dict] = []

    with open(eigenvec_path, "r", encoding="utf-8") as f:
        for line in f:
            parts = line.strip().split()

            if len(parts) < pcs + 2:
                continue

            sample_id = parts[1].strip()

            try:
                pc_values = [float(parts[i + 2]) for i in range(pcs)]
            except ValueError:
                continue

            rows.append({
                "sample_id": sample_id,
                "pcs": pc_values,
            })

    return rows


def cache_reference_pcs(cache_path: str, pcs_rows: List[Dict]) -> None:
    """
    Save reference PCs to a simple tab-delimited cache file.
    """
    parent = os.path.dirname(cache_path)
    if parent:
        os.makedirs(parent, exist_ok=True)

    with open(cache_path, "w", encoding="utf-8") as f:
        for row in pcs_rows:
            line = row["sample_id"] + "\t" + "\t".join(str(v) for v in row["pcs"])
            f.write(line + "\n")


def load_cached_reference_pcs(cache_path: str) -> List[Dict]:
    """
    Load cached reference PCs written by cache_reference_pcs().
    """
    if not os.path.exists(cache_path):
        return []

    pcs_rows: List[Dict] = []

    with open(cache_path, "r", encoding="utf-8") as f:
        for line in f:
            parts = line.strip().split("\t")
            if len(parts) < 2:
                continue

            sample_id = parts[0].strip()

            try:
                pc_values = [float(v) for v in parts[1:]]
            except ValueError:
                continue

            pcs_rows.append({
                "sample_id": sample_id,
                "pcs": pc_values,
            })

    return pcs_rows


def attach_labels_to_reference_pcs(
    reference_pcs: List[Dict],
    sample_to_cont: Dict[str, str],
) -> List[Dict]:
    """
    Join PCA rows with continent labels.

    Output rows look like:
        {
            "sample_id": "...",
            "pcs": [...],
            "continent": "EUR"
        }
    """
    labeled_rows: List[Dict] = []

    for row in reference_pcs:
        sample_id = row["sample_id"]
        continent = sample_to_cont.get(sample_id)

        if not continent:
            continue

        labeled_rows.append({
            "sample_id": sample_id,
            "pcs": row["pcs"],
            "continent": continent,
        })

    return labeled_rows


def build_training_data(labeled_pcs: List[Dict]) -> Tuple[List[List[float]], List[str], List[str]]:
    """
    Convert labeled PCA rows into ML-ready X, y, sample_ids.
    """
    X: List[List[float]] = []
    y: List[str] = []
    sample_ids: List[str] = []

    for row in labeled_pcs:
        X.append(row["pcs"])
        y.append(row["continent"])
        sample_ids.append(row["sample_id"])

    return X, y, sample_ids


def nearest_reference_distance(user_pcs: List[float], reference_pcs: List[Dict]) -> float:
    """
    Return Euclidean distance from a user PC vector to the nearest
    reference sample PC vector.

    Useful as a debug/confidence heuristic.
    """
    if not reference_pcs:
        return 0.0

    best = None

    for row in reference_pcs:
        ref = row["pcs"]
        if len(ref) != len(user_pcs):
            continue

        dist = math.sqrt(sum((u - r) ** 2 for u, r in zip(user_pcs, ref)))

        if best is None or dist < best:
            best = dist

    return best if best is not None else 0.0


def summarize_label_counts(labels: List[str]) -> Dict[str, int]:
    """
    Count class sizes for quick sanity checks.
    """
    counts: Dict[str, int] = {}

    for label in labels:
        counts[label] = counts.get(label, 0) + 1

    return counts


if __name__ == "__main__":
    # Example usage:
    # Adjust paths if you run this file directly from a different folder.
    from utils.ancestry_inference.reference import load_reference_metadata

    metadata_samples, sample_to_cont = load_reference_metadata("nih/igsr_samples.tsv")
    reference_pcs = load_pcs("nih/chr22_pca.eigenvec", pcs=20)

    labeled_pcs = attach_labels_to_reference_pcs(reference_pcs, sample_to_cont)
    X, y, sample_ids = build_training_data(labeled_pcs)

    print("Loaded PCA rows:", len(reference_pcs))
    print("Labeled PCA rows:", len(labeled_pcs))
    print("Feature rows:", len(X))
    print("PC count:", len(X[0]) if X else 0)
    print("Label counts:", summarize_label_counts(y))
    print("First 3 sample IDs:", sample_ids[:3])