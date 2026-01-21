import os
from typing import Dict, List


def plot_ancestry_bar(output_path: str, proportions: Dict[str, float]):
    try:
        import matplotlib.pyplot as plt  # type: ignore
    except Exception:
        return
    labels = list(proportions.keys())
    values = [proportions[k] for k in labels]
    fig, ax = plt.subplots(figsize=(6, 2))
    ax.bar(labels, values, color="#4b6cb7")
    ax.set_ylim(0, 1)
    ax.set_ylabel("Proportion")
    ax.set_title("Global Ancestry")
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    fig.tight_layout()
    fig.savefig(output_path)
    plt.close(fig)


def plot_pca_scatter(output_path: str, reference_rows: List[Dict], user_row: Dict):
    try:
        import matplotlib.pyplot as plt  # type: ignore
    except Exception:
        return
    fig, ax = plt.subplots(figsize=(5, 4))
    for row in reference_rows:
        pcs = row.get("pcs", [])
        if len(pcs) < 2:
            continue
        ax.scatter(pcs[0], pcs[1], s=10, alpha=0.4, color="#94a3b8")
    user_pcs = user_row.get("pcs", [])
    if len(user_pcs) >= 2:
        ax.scatter(user_pcs[0], user_pcs[1], s=60, color="#d97706", label="User")
    ax.set_xlabel("PC1")
    ax.set_ylabel("PC2")
    ax.set_title("PCA Projection")
    ax.legend(loc="best")
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    fig.tight_layout()
    fig.savefig(output_path)
    plt.close(fig)
