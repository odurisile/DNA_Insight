import math
from typing import Dict, Optional, Tuple

COMPLEMENT = {"A": "T", "T": "A", "C": "G", "G": "C"}
AMBIGUOUS_PAIRS = {frozenset({"A", "T"}), frozenset({"C", "G"})}


def normalize_genome(genome: Dict) -> Dict[str, str]:
    """
    Reduce parsed genome to {rsid: genotype_string} with uppercase letters.
    Accepts dict from parse_raw_dna_file.
    """
    out = {}
    for rsid, info in genome.items():
        geno = info.get("genotype") if isinstance(info, dict) else info
        if not geno:
            continue
        g = geno.replace("/", "").replace("|", "").upper()
        if len(g) >= 2:
            out[rsid] = g[:2]
    return out


def is_ambiguous(effect: str, other: str) -> bool:
    return frozenset({effect, other}) in AMBIGUOUS_PAIRS


def complement_allele(a: str) -> Optional[str]:
    return COMPLEMENT.get(a.upper())


def harmonize_and_dosage(geno: str, effect: str, other: str) -> Tuple[str, Optional[float]]:
    """
    Returns (status, dosage)
    status: "ok" | "ambiguous" | "skip"
    dosage: 0-2 or None if skipped.
    """
    if not geno or not effect or not other:
        return "skip", None

    effect = effect.upper()
    other = other.upper()
    if is_ambiguous(effect, other):
        return "ambiguous", None

    alleles = list(geno)
    allele_set = set(alleles)

    if allele_set.issubset({effect, other}):
        dosage = alleles.count(effect)
        return "ok", float(dosage)

    comp_eff = complement_allele(effect)
    comp_oth = complement_allele(other)
    if comp_eff and comp_oth:
        if allele_set.issubset({comp_eff, comp_oth}):
            dosage = alleles.count(comp_eff)
            return "ok", float(dosage)

    return "skip", None


def percentile_from_z(z: float) -> float:
    return 0.5 * (1 + math.erf(z / math.sqrt(2))) * 100
