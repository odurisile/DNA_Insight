import os
from typing import Dict, List, Tuple

import joblib
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
from sklearn.model_selection import train_test_split

from reference import load_reference_metadata
from pca import load_pcs, attach_labels_to_reference_pcs, build_training_data


VALID_CONTINENTS = {"AFR", "EUR", "EAS", "SAS", "AMR"}


def filter_valid_labels(labeled_pcs: List[Dict]) -> List[Dict]:
    """
    Keep only rows with one clean broad ancestry label.
    """
    filtered = []

    for row in labeled_pcs:
        continent = row["continent"].strip().upper()
        if continent in VALID_CONTINENTS:
            filtered.append({
                "sample_id": row["sample_id"],
                "pcs": row["pcs"],
                "continent": continent,
            })

    return filtered


def train_ancestry_model(
    metadata_path: str,
    eigenvec_path: str,
    pcs: int = 20,
    model_out: str = "nih/ancestry_model.joblib",
):
    """
    Train a multinomial ancestry classifier from reference PCA coordinates.
    """
    metadata_samples, sample_to_cont = load_reference_metadata(metadata_path)
    reference_pcs = load_pcs(eigenvec_path, pcs=pcs)

    labeled_pcs = attach_labels_to_reference_pcs(reference_pcs, sample_to_cont)
    labeled_pcs = filter_valid_labels(labeled_pcs)

    X, y, sample_ids = build_training_data(labeled_pcs)

    if not X:
        raise ValueError("No training data available after filtering labels.")

    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=0.2,
        random_state=42,
        stratify=y,
    )

    model = LogisticRegression(
       max_iter=2000,
       class_weight="balanced", 
    )

    model.fit(X_train, y_train)

    y_pred = model.predict(X_test)
    acc = accuracy_score(y_test, y_pred)

    print("Training samples:", len(X_train))
    print("Test samples:", len(X_test))
    print("Accuracy:", round(acc, 4))
    print("\nClassification report:")
    print(classification_report(y_test, y_pred))
    print("Confusion matrix:")
    print(confusion_matrix(y_test, y_pred))

    os.makedirs(os.path.dirname(model_out), exist_ok=True)
    joblib.dump(
        {
            "model": model,
            "pcs": pcs,
            "valid_continents": sorted(VALID_CONTINENTS),
        },
        model_out,
    )

    print(f"\nSaved model to: {model_out}")

    return model


def load_trained_model(model_path: str = "nih/ancestry_model.joblib"):
    payload = joblib.load(model_path)
    return payload["model"], payload["pcs"], payload["valid_continents"]


def predict_ancestry_from_pcs(user_pcs: List[float], model_path: str = "nih/ancestry_model.joblib") -> Dict[str, float]:
    """
    Predict ancestry probabilities from a user PC vector.
    """
    model, expected_pcs, valid_continents = load_trained_model(model_path)

    if len(user_pcs) != expected_pcs:
        raise ValueError(f"Expected {expected_pcs} PCs, got {len(user_pcs)}")

    probs = model.predict_proba([user_pcs])[0]
    classes = model.classes_

    result = {label: 0.0 for label in valid_continents}
    for label, prob in zip(classes, probs):
        result[label] = float(prob)

    return result


if __name__ == "__main__":
    train_ancestry_model(
        metadata_path="nih/igsr_samples.tsv",
        eigenvec_path="nih/chr22_pca.eigenvec",
        pcs=20,
        model_out="nih/ancestry_model.joblib",
    )