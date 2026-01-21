import json
from typing import Dict, List, Optional


def train_pcs_model(train_rows: List[Dict], label_key: str = "continent") -> Dict:
    try:
        from sklearn.linear_model import LogisticRegression  # type: ignore
    except Exception as exc:
        raise ImportError("scikit-learn is required for PCA model training.") from exc
    X = [row["pcs"] for row in train_rows]
    y = [row[label_key] for row in train_rows]
    model = LogisticRegression(max_iter=200)
    model.fit(X, y)
    return {"model": model, "classes": list(model.classes_)}


def predict_proportions(model_bundle: Dict, user_pcs: List[float]) -> Dict[str, float]:
    model = model_bundle["model"]
    classes = model_bundle["classes"]
    probs = model.predict_proba([user_pcs])[0]
    return {classes[i]: float(probs[i]) for i in range(len(classes))}


def save_model(path: str, model_bundle: Dict):
    try:
        import joblib  # type: ignore
    except Exception as exc:
        raise ImportError("joblib is required to save sklearn models.") from exc
    joblib.dump(model_bundle, path)


def load_model(path: str) -> Optional[Dict]:
    try:
        import joblib  # type: ignore
    except Exception as exc:
        raise ImportError("joblib is required to load sklearn models.") from exc
    return joblib.load(path)


def save_model_metadata(path: str, metadata: Dict):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)
