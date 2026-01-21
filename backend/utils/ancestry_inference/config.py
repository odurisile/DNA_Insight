import json
from typing import Dict


def _load_simple_yaml(path: str) -> Dict:
    data: Dict = {}
    stack = [(0, data)]
    with open(path, "r", encoding="utf-8") as f:
        for raw in f:
            if "#" in raw:
                raw = raw.split("#", 1)[0]
            if not raw.strip():
                continue
            indent = len(raw) - len(raw.lstrip(" "))
            key, sep, value = raw.strip().partition(":")
            if sep == "":
                continue
            while stack and indent < stack[-1][0]:
                stack.pop()
            if not stack:
                stack = [(0, data)]
            current = stack[-1][1]
            value = value.strip()
            if value == "":
                current[key] = {}
                stack.append((indent + 2, current[key]))
            else:
                current[key] = _parse_scalar(value)
    return data


def _parse_scalar(value: str):
    lower = value.lower()
    if lower in ("true", "false"):
        return lower == "true"
    if lower in ("null", "none"):
        return None
    try:
        if "." in value or "e" in value.lower():
            return float(value)
        return int(value)
    except ValueError:
        return value


def load_config(path: str) -> Dict:
    if path.lower().endswith(".json"):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    try:
        import yaml  # type: ignore
    except Exception:
        yaml = None
    if yaml is not None:
        with open(path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)
    return _load_simple_yaml(path)
