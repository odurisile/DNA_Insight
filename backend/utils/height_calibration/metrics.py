from typing import Dict, Iterable, List, Tuple


def r2_score(y_true: Iterable[float], y_pred: Iterable[float]) -> float:
    y_true = list(y_true)
    y_pred = list(y_pred)
    if not y_true:
        return 0.0
    mean = sum(y_true) / len(y_true)
    ss_tot = sum((y - mean) ** 2 for y in y_true)
    ss_res = sum((y - y_hat) ** 2 for y, y_hat in zip(y_true, y_pred))
    return 1.0 - ss_res / ss_tot if ss_tot else 0.0


def mae(y_true: Iterable[float], y_pred: Iterable[float]) -> float:
    y_true = list(y_true)
    y_pred = list(y_pred)
    if not y_true:
        return 0.0
    return sum(abs(y - y_hat) for y, y_hat in zip(y_true, y_pred)) / len(y_true)


def stratified_errors(
    rows: List[Dict[str, float]],
    ancestry_keys: Tuple[str, ...] = ("AFR", "EUR", "NAT", "EAS", "SAS"),
    threshold: float = 0.5,
) -> Dict[str, Dict[str, float]]:
    results = {}
    for ancestry in ancestry_keys:
        subset = [r for r in rows if r.get(ancestry, 0.0) >= threshold]
        if not subset:
            continue
        y_true = [r["height_cm"] for r in subset]
        y_pred = [r["predicted_height_cm"] for r in subset]
        results[ancestry] = {
            "n": len(subset),
            "mae": mae(y_true, y_pred),
        }
    return results
