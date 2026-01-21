from typing import Dict, List, Set

AMBIGUOUS_PAIRS = {frozenset({"A", "T"}), frozenset({"C", "G"})}


def is_ambiguous(effect: str, other: str) -> bool:
    return frozenset({effect.upper(), other.upper()}) in AMBIGUOUS_PAIRS


def filter_ambiguous_variants(variants: List[Dict]) -> List[Dict]:
    out = []
    for row in variants:
        if not row.get("effect_allele") or not row.get("other_allele"):
            continue
        if is_ambiguous(row["effect_allele"], row["other_allele"]):
            continue
        out.append(row)
    return out


def intersect_snps(user_snps: Set[str], ref_snps: Set[str]) -> Set[str]:
    return user_snps.intersection(ref_snps)
