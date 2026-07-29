import json
import os
from typing import Dict, Optional

from .admixture import load_admixture_cache, parse_q_matrix, run_admixture, save_admixture_cache
from .config import load_config
from .pca import load_pcs, load_cached_reference_pcs
from .plink import (
    build_plink_convert_command,
    build_plink_extract_command,
    build_plink_ld_prune_command,
    build_plink_merge_command,
    build_plink_pca_command,
    build_plink_qc_command,
    run_command,
)
from .reference import load_reference_metadata
from .torch_model import predict_ancestry_from_pcs_torch
from .visuals import plot_ancestry_bar, plot_pca_scatter


def detect_genome_build(raw_path: str) -> str:
    if raw_path.lower().endswith((".vcf", ".vcf.gz")):
        with open(raw_path, "r", encoding="utf-8", errors="ignore") as f:
            for _ in range(20):
                line = f.readline()
                if "GRCh38" in line or "hg38" in line:
                    return "GRCh38"
                if "GRCh37" in line or "hg19" in line:
                    return "GRCh37"
    return "unknown"


def infer_global_ancestry_from_file(
    raw_path: str,
    output_dir: str,
    config_path: str,
    method: Optional[str] = None,
) -> Dict:
    config = load_config(config_path)
    ref_cfg = config["reference"]
    tools = config["tools"]
    qc = config["qc"]
    inference = config["inference"]

    os.makedirs(output_dir, exist_ok=True)
    build = detect_genome_build(raw_path)

    user_prefix = os.path.join(output_dir, "user")
    user_qc_prefix = os.path.join(output_dir, "user_qc")
    user_prune_prefix = os.path.join(output_dir, "user_prune")
    merge_prefix = os.path.join(output_dir, "merged")
    pca_prefix = os.path.join(output_dir, "pca")

    run_command(build_plink_convert_command(tools["plink2"], raw_path, user_prefix))
    run_command(
        build_plink_qc_command(
            tools["plink2"], user_prefix, user_qc_prefix, qc["max_missing_rate"], qc["min_maf"]
        )
    )
    run_command(
        build_plink_ld_prune_command(
            tools["plink2"],
            user_qc_prefix,
            user_prune_prefix,
            qc["ld_window_kb"],
            qc["ld_step"],
            qc["ld_r2"],
        )
    )
    prune_in = user_prune_prefix + ".prune.in"
    run_command(build_plink_extract_command(tools["plink2"], user_qc_prefix, prune_in, user_prune_prefix))
    run_command(build_plink_merge_command(tools["plink2"], user_prune_prefix, ref_cfg["plink_prefix"], merge_prefix))

    run_command(build_plink_pca_command(tools["plink2"], merge_prefix, pca_prefix, inference["pcs"]))
    pcs = load_pcs(pca_prefix + ".eigenvec", inference["pcs"])

    samples, pop_map = load_reference_metadata(ref_cfg["metadata_tsv"], ref_cfg["population_map"])
    sample_map = {s["sample_id"]: s for s in samples}
    reference_rows = []
    user_row = None
    for row in pcs:
        if row["sample_id"] in sample_map:
            ref = sample_map[row["sample_id"]]
            reference_rows.append({**row, **ref})
        else:
            user_row = row

    if user_row is None:
        user_row = pcs[-1] if pcs else {"sample_id": "user", "pcs": []}

    method = method or inference.get("method", "admixture_pca")
    proportions = {"AFR": 0.0, "EUR": 0.0, "EAS": 0.0, "SAS": 0.0, "AMR": 0.0}
    closest_populations = []
    ancestry_embedding = []

    if method.startswith("admixture"):
        cache = load_admixture_cache(config["cache"]["admixture_cache"])
        if cache and cache.get("k") == inference["k"]:
            proportions.update(cache.get("user_proportions", {}))
        else:
            run_admixture(tools["admixture"], merge_prefix + ".bed", inference["k"], tools["threads"], output_dir)
            q_path = merge_prefix + f".{inference['k']}.Q"
            labels = list(proportions.keys())
            q_rows = parse_q_matrix(q_path, [r["sample_id"] for r in pcs], labels)
            for row in q_rows:
                if row["sample_id"] == user_row["sample_id"]:
                    proportions = {k: row[k] for k in labels}
                    break
            save_admixture_cache(
                config["cache"]["admixture_cache"],
                {"k": inference["k"], "user_proportions": proportions},
            )
    elif method.startswith("torch"):
        torch_model_path = inference.get("torch_model_path", "nih/ancestry_torch_model.pt")
        torch_result = predict_ancestry_from_pcs_torch(user_row.get("pcs", []), model_path=torch_model_path)
        proportions.update(torch_result["probabilities"])
        ancestry_embedding = torch_result.get("embedding", [])

    if method.endswith("pca"):
        reference_cache = load_cached_reference_pcs(config["cache"]["pca_cache"])
        ref_for_plot = reference_cache or reference_rows
        if ref_for_plot and user_row.get("pcs"):
            distances = []
            for row in reference_rows:
                if len(row.get("pcs", [])) < 2:
                    continue
                dist = sum((u - r) ** 2 for u, r in zip(user_row["pcs"], row["pcs"])) ** 0.5
                distances.append((row["population"], dist))
            distances.sort(key=lambda x: x[1])
            closest_populations = [p for p, _ in distances[:5]]

    if config.get("output", {}).get("plots", False):
        plot_ancestry_bar(os.path.join(output_dir, "ancestry_bar.png"), proportions)
        plot_pca_scatter(os.path.join(output_dir, "pca_scatter.png"), reference_rows, user_row)

    confidence = max(proportions.values()) if proportions else 0.0
    if confidence < inference.get("confidence_floor", 0.5):
        closest_populations = closest_populations[:3]

    return {
        "global_ancestry": proportions,
        "closest_populations": closest_populations,
        "pcs": user_row.get("pcs", []),
        "embedding": ancestry_embedding,
        "confidence": confidence,
        "method": "ADMIXTURE+PCA" if method.startswith("admixture") else "TORCH+PCA",
        "reference": ref_cfg.get("name", "1000G"),
        "build": build,
    }
