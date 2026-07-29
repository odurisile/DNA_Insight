import os
import random
from typing import Dict, List, Sequence, Tuple

from .pca import attach_labels_to_reference_pcs, build_training_data, load_pcs
from .reference import load_reference_metadata

try:
    import torch
    import torch.nn as nn
except Exception:  # pragma: no cover - exercised when torch is unavailable
    torch = None
    nn = None


VALID_CONTINENTS = ("AFR", "AMR", "EAS", "EUR", "SAS")


def _require_torch():
    if torch is None or nn is None:
        raise RuntimeError(
            "PyTorch is not installed. Install `torch` in the backend environment to use the "
            "torch ancestry model."
        )


def filter_valid_labels(labeled_pcs: List[Dict]) -> List[Dict]:
    filtered = []
    for row in labeled_pcs:
        continent = str(row.get("continent", "")).strip().upper()
        if continent in VALID_CONTINENTS:
            filtered.append(
                {
                    "sample_id": row["sample_id"],
                    "pcs": row["pcs"],
                    "continent": continent,
                }
            )
    return filtered


def _stratified_split(
    features: Sequence[Sequence[float]],
    labels: Sequence[str],
    test_size: float = 0.2,
    seed: int = 42,
) -> Tuple[List[int], List[int]]:
    grouped: Dict[str, List[int]] = {}
    for idx, label in enumerate(labels):
        grouped.setdefault(label, []).append(idx)

    rng = random.Random(seed)
    train_idx: List[int] = []
    test_idx: List[int] = []

    for label_indices in grouped.values():
        shuffled = list(label_indices)
        rng.shuffle(shuffled)
        n_test = max(1, int(round(len(shuffled) * test_size))) if len(shuffled) > 1 else 0
        if n_test >= len(shuffled):
            n_test = len(shuffled) - 1
        test_idx.extend(shuffled[:n_test])
        train_idx.extend(shuffled[n_test:])

    if not train_idx:
        train_idx = list(range(len(features)))
        test_idx = []

    return train_idx, test_idx


def _column_stats(rows: Sequence[Sequence[float]]) -> Tuple[List[float], List[float]]:
    if not rows:
        return [], []
    width = len(rows[0])
    means: List[float] = []
    stds: List[float] = []
    for col in range(width):
        values = [float(row[col]) for row in rows]
        mean = sum(values) / len(values)
        variance = sum((value - mean) ** 2 for value in values) / max(1, len(values))
        std = variance ** 0.5
        means.append(mean)
        stds.append(std if std > 1e-8 else 1.0)
    return means, stds


def _normalize_rows(rows: Sequence[Sequence[float]], means: Sequence[float], stds: Sequence[float]) -> List[List[float]]:
    normalized: List[List[float]] = []
    for row in rows:
        normalized.append([(float(value) - mean) / std for value, mean, std in zip(row, means, stds)])
    return normalized


if nn is not None:
    class AncestryMLP(nn.Module):
        def __init__(self, input_dim: int, hidden_dims: Sequence[int] = (64, 32), embedding_dim: int = 16, num_classes: int = 5):
            super().__init__()
            dims = [input_dim, *hidden_dims]
            layers = []
            for in_dim, out_dim in zip(dims, dims[1:]):
                layers.append(nn.Linear(in_dim, out_dim))
                layers.append(nn.ReLU())
            self.backbone = nn.Sequential(*layers)
            last_dim = dims[-1]
            self.embedding = nn.Linear(last_dim, embedding_dim)
            self.classifier = nn.Linear(embedding_dim, num_classes)

        def encode(self, x):
            features = self.backbone(x)
            embedding = self.embedding(features)
            return embedding

        def forward(self, x):
            embedding = self.encode(x)
            logits = self.classifier(embedding)
            return logits, embedding
else:  # pragma: no cover - only used when torch is unavailable
    class AncestryMLP:  # type: ignore[no-redef]
        def __init__(self, *args, **kwargs):
            _require_torch()


def train_ancestry_torch_model(
    metadata_path: str,
    eigenvec_path: str,
    pcs: int = 20,
    model_out: str = "nih/ancestry_torch_model.pt",
    hidden_dims: Sequence[int] = (64, 32),
    embedding_dim: int = 16,
    epochs: int = 250,
    learning_rate: float = 1e-3,
    weight_decay: float = 1e-4,
    test_size: float = 0.2,
    seed: int = 42,
) -> Dict:
    _require_torch()
    torch.manual_seed(seed)

    metadata_samples, sample_to_cont = load_reference_metadata(metadata_path)
    reference_pcs = load_pcs(eigenvec_path, pcs=pcs)
    labeled_pcs = attach_labels_to_reference_pcs(reference_pcs, sample_to_cont)
    labeled_pcs = filter_valid_labels(labeled_pcs)

    X, y, _sample_ids = build_training_data(labeled_pcs)
    if not X:
        raise ValueError("No training data available after filtering labels.")

    train_idx, test_idx = _stratified_split(X, y, test_size=test_size, seed=seed)
    X_train = [X[idx] for idx in train_idx]
    y_train = [y[idx] for idx in train_idx]
    X_test = [X[idx] for idx in test_idx]
    y_test = [y[idx] for idx in test_idx]

    classes = sorted({label for label in y})
    class_to_idx = {label: idx for idx, label in enumerate(classes)}

    means, stds = _column_stats(X_train)
    X_train_norm = _normalize_rows(X_train, means, stds)
    X_test_norm = _normalize_rows(X_test, means, stds) if X_test else []

    x_train = torch.tensor(X_train_norm, dtype=torch.float32)
    y_train_tensor = torch.tensor([class_to_idx[label] for label in y_train], dtype=torch.long)

    model = AncestryMLP(
        input_dim=pcs,
        hidden_dims=hidden_dims,
        embedding_dim=embedding_dim,
        num_classes=len(classes),
    )
    optimizer = torch.optim.AdamW(model.parameters(), lr=learning_rate, weight_decay=weight_decay)
    criterion = nn.CrossEntropyLoss()

    model.train()
    for _ in range(epochs):
        optimizer.zero_grad()
        logits, _embedding = model(x_train)
        loss = criterion(logits, y_train_tensor)
        loss.backward()
        optimizer.step()

    model.eval()
    with torch.no_grad():
        train_logits, _ = model(x_train)
        train_predictions = train_logits.argmax(dim=1).tolist()
        train_accuracy = sum(
            int(pred == actual) for pred, actual in zip(train_predictions, y_train_tensor.tolist())
        ) / max(1, len(y_train))

        test_accuracy = None
        if X_test_norm:
            x_test = torch.tensor(X_test_norm, dtype=torch.float32)
            y_test_tensor = torch.tensor([class_to_idx[label] for label in y_test], dtype=torch.long)
            test_logits, _ = model(x_test)
            test_predictions = test_logits.argmax(dim=1).tolist()
            test_accuracy = sum(
                int(pred == actual) for pred, actual in zip(test_predictions, y_test_tensor.tolist())
            ) / max(1, len(y_test))

    parent = os.path.dirname(model_out)
    if parent:
        os.makedirs(parent, exist_ok=True)

    payload = {
        "state_dict": model.state_dict(),
        "pcs": pcs,
        "classes": classes,
        "means": means,
        "stds": stds,
        "hidden_dims": list(hidden_dims),
        "embedding_dim": embedding_dim,
        "train_accuracy": train_accuracy,
        "test_accuracy": test_accuracy,
        "metadata_rows": len(metadata_samples),
    }
    torch.save(payload, model_out)

    return payload


def load_trained_torch_model(model_path: str = "nih/ancestry_torch_model.pt"):
    _require_torch()
    payload = torch.load(model_path, map_location="cpu")
    model = AncestryMLP(
        input_dim=payload["pcs"],
        hidden_dims=payload.get("hidden_dims", (64, 32)),
        embedding_dim=payload.get("embedding_dim", 16),
        num_classes=len(payload["classes"]),
    )
    model.load_state_dict(payload["state_dict"])
    model.eval()
    return model, payload


def predict_ancestry_from_pcs_torch(
    user_pcs: List[float],
    model_path: str = "nih/ancestry_torch_model.pt",
) -> Dict:
    model, payload = load_trained_torch_model(model_path)
    expected_pcs = payload["pcs"]
    if len(user_pcs) != expected_pcs:
        raise ValueError(f"Expected {expected_pcs} PCs, got {len(user_pcs)}")

    means = payload["means"]
    stds = payload["stds"]
    normalized = [(float(value) - mean) / std for value, mean, std in zip(user_pcs, means, stds)]
    x = torch.tensor([normalized], dtype=torch.float32)

    with torch.no_grad():
        logits, embedding = model(x)
        probs = torch.softmax(logits, dim=1)[0].tolist()

    result = {label: 0.0 for label in VALID_CONTINENTS}
    for label, prob in zip(payload["classes"], probs):
        result[label] = float(prob)

    return {
        "probabilities": result,
        "embedding": [float(value) for value in embedding[0].tolist()],
        "model_path": model_path,
    }


if __name__ == "__main__":
    train_ancestry_torch_model(
        metadata_path="nih/igsr_samples.tsv",
        eigenvec_path="nih/chr22_pca.eigenvec",
        pcs=20,
        model_out="nih/ancestry_torch_model.pt",
    )
