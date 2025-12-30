import csv
import math

GWAS_PATH = "../backend/nih/gwas_50k.csv"

# Structure:
# GWAS_TABLE = {
#   "height": { "rs123": {beta:0.01, allele:"A"}, ... }
#   "bmi": {...}
# }
GWAS_TABLE = {}


def load_gwas_table():
    """
    Loads ~50,000 SNPs into memory.
    Organizes them by trait → rsid → beta & allele.
    """
    global GWAS_TABLE
    if GWAS_TABLE:
        return

    with open(GWAS_PATH, "r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            trait = row["trait"].lower()
            rsid = row["rsid"]

            if trait not in GWAS_TABLE:
                GWAS_TABLE[trait] = {}

            try:
                GWAS_TABLE[trait][rsid] = {
                    "beta": float(row["beta"]),
                    "effect": row["effect_allele"].upper()
                }
            except:
                continue


def allele_dosage(genotype: str, effect: str) -> int:
    if not genotype:
        return 0
    g = genotype.replace("/", "").upper()
    return g.count(effect)


def compute_single_prs(genome, trait: str):
    """
    Computes:
    - raw PRS
    - normalized Z-score
    - percentile estimate
    """
    if trait not in GWAS_TABLE:
        return None

    variants = GWAS_TABLE[trait]

    score = 0.0
    contributing_snps = 0

    for rsid, info in variants.items():
        if rsid not in genome:
            continue

        g = genome[rsid]["genotype"]
        dosage = allele_dosage(g, info["effect"])
        score += info["beta"] * dosage
        contributing_snps += 1

    if contributing_snps == 0:
        return None

    # Mean and SD approximations for polygenic traits
    mean = 0.0
    sd = 1.0

    z = (score - mean) / sd
    percentile = 0.5 * (1 + math.erf(z / math.sqrt(2)))

    return {
        "raw_score": score,
        "z": z,
        "percentile": percentile * 100,
        "snps_used": contributing_snps
    }


def compute_prs(genome):
    """
    Computes PRS for all major traits:
    - height
    - bmi
    - diabetes
    - heart_disease
    - alzheimer_prs (NOT APOE)
    """

    load_gwas_table()

    traits = ["height", "bmi", "diabetes", "heart_disease", "alzheimer_prs"]

    results = {}

    for trait in traits:
        prs = compute_single_prs(genome, trait)
        results[trait] = prs

    return results
