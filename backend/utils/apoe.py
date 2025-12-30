def get_allele(geno: str) -> str:
    """Returns allele characters without slash."""
    if not geno:
        return "--"
    return geno.replace("/", "").upper()


def apoe_from_snps(rs429358: str, rs7412: str):
    """
    Converts SNP genotypes to APOE allele:
    APOE allele mapping:
        rs429358   rs7412    → APOE
           T         T          e2
           T         C          e3
           C         C          e4
    """
    mapping = {
        ("T", "T"): "e2",
        ("T", "C"): "e3",
        ("C", "C"): "e4",
    }

    key = (rs429358, rs7412)
    return mapping.get(key, None)


def compute_apoe_genotype(genome):
    """
    Returns dict:
    {
       "genotype": "e3/e4",
       "risk": "Elevated",
       "confidence": 1.0
    }
    """

    if "rs429358" not in genome or "rs7412" not in genome:
        return {
            "genotype": "Unknown",
            "risk": "Unknown",
            "confidence": 0.0
        }

    g1 = get_allele(genome["rs429358"]["genotype"])
    g2 = get_allele(genome["rs7412"]["genotype"])

    # Extract each allele separately
    a1 = apoe_from_snps(g1[0], g2[0])
    a2 = apoe_from_snps(g1[1], g2[1])

    # If invalid or missing
    if not a1 or not a2:
        return {
            "genotype": "Unknown",
            "risk": "Unknown",
            "confidence": 0.5
        }

    genotype = f"{a1}/{a2}"

    # Alzheimer's risk classification
    risk_levels = {
        "e2/e2": "Reduced",
        "e2/e3": "Reduced",
        "e3/e3": "Average",
        "e2/e4": "Slightly Elevated",
        "e3/e4": "Elevated",
        "e4/e4": "High",
    }

    risk = risk_levels.get(genotype, "Unknown")

    return {
        "genotype": genotype,
        "risk": risk,
        "confidence": 1.0,
    }
