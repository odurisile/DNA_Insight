import math
import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR.parent / "nih" / "gwas_50k.db"

TRAIT_GROUPS = {
    "height": ["height"],
    "bmi": ["bmi", "body mass index"],
    "diabetes": [
        "type 2 diabetes",
        "type ii diabetes",
        "diabetes mellitus",
        "diabetes",
        "prediabetes",
    ],
    "heart_disease": [
        "coronary artery disease",
        "coronary heart disease",
        "heart attack",
        "myocardial infarction",
        "ischemic heart disease",
        "heart failure",
        "heart disease",
    ],
    "alzheimer": [
        "alzheimer",
        "late-onset alzheimer",
        "early-onset alzheimer",
        "family history of alzheimer",
        "dementia",
    ],
}


def allele_dosage(genotype: str, effect_allele: str) -> int:
    """
    Count copies of the effect allele in a genotype string.
    Examples:
        A/G with A -> 1
        C/C with C -> 2
        T/T with C -> 0
    """
    if not genotype or not effect_allele:
        return 0

    g = genotype.replace("/", "").replace("|", "").upper().strip()
    effect = effect_allele.upper().strip()

    if g in {"", "--"}:
        return 0

    return g.count(effect)


def ensure_indexes():
    """
    Safe to run repeatedly. Helps query speed.
    """
    conn = sqlite3.connect(str(DB_PATH))
    cur = conn.cursor()

    cur.execute("CREATE INDEX IF NOT EXISTS idx_gwas_snps_rsid ON gwas_snps(rsid)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_gwas_snps_trait ON gwas_snps(trait)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_gwas_snps_rsid_trait ON gwas_snps(rsid, trait)")

    conn.commit()
    conn.close()


def _build_trait_condition(trait_keywords: list[str]) -> str:
    return " OR ".join(["LOWER(trait) LIKE ?"] * len(trait_keywords))


def _fetch_matching_rows(genome: dict, trait_keywords: list[str]) -> list[tuple]:
    """
    Fetch only rows where:
    - rsid exists in the user's genome
    - trait matches one of the keywords
    """
    rsids = list(genome.keys())
    if not rsids:
        return []

    conn = sqlite3.connect(str(DB_PATH))
    cur = conn.cursor()

    rows = []
    chunk_size = 900
    trait_condition = _build_trait_condition(trait_keywords)
    trait_params = [f"%{keyword.lower()}%" for keyword in trait_keywords]

    for i in range(0, len(rsids), chunk_size):
        chunk = rsids[i:i + chunk_size]
        rsid_placeholders = ",".join(["?"] * len(chunk))

        query = f"""
            SELECT rsid, trait, effect_allele, beta
            FROM gwas_snps
            WHERE rsid IN ({rsid_placeholders})
              AND ({trait_condition})
        """

        params = chunk + trait_params
        cur.execute(query, params)
        rows.extend(cur.fetchall())

    conn.close()
    return rows


def _deduplicate_rows(rows: list[tuple]) -> list[tuple]:
    """
    Deduplicate repeated rsid entries within a grouped trait query.
    Keep the row with the largest absolute beta for each (rsid, effect_allele).
    """
    best = {}

    for rsid, trait, effect_allele, beta in rows:
        key = (rsid, effect_allele)
        beta = float(beta)

        if key not in best or abs(beta) > abs(best[key][3]):
            best[key] = (rsid, trait, effect_allele, beta)

    return list(best.values())


def compute_single_prs(genome: dict, trait_keywords: list[str]):
    """
    Compute grouped PRS from DB rows matching requested trait keywords.
    """
    rows = _fetch_matching_rows(genome, trait_keywords)
    if not rows:
        return None

    rows = _deduplicate_rows(rows)

    score = 0.0
    contributing_snps = 0

    for rsid, trait, effect_allele, beta in rows:
        genotype = genome.get(rsid, {}).get("genotype")
        dosage = allele_dosage(genotype, effect_allele)

        if dosage == 0:
            continue

        score += float(beta) * dosage
        contributing_snps += 1

    if contributing_snps == 0:
        return None

    # Temporary normalization.
    # This keeps the output bounded and avoids every trait slamming to 100%.
    scaled_score = score / max(1, math.sqrt(contributing_snps))
    z = scaled_score
    percentile = 0.5 * (1 + math.erf(z / math.sqrt(2)))

    return {
        "raw_score": score,
        "scaled_score": scaled_score,
        "z": z,
        "percentile": percentile * 100,
        "snps_used": contributing_snps,
    }


def compute_prs(genome: dict):
    """
    Main entry point for grouped PRS outputs.
    """
    results = {}

    for output_trait, keywords in TRAIT_GROUPS.items():
        results[output_trait] = compute_single_prs(genome, keywords)

    return results


def inspect_matching_traits(genome: dict, output_trait: str) -> list[str]:
    """
    Debug helper: show real DB trait strings that matched a grouped output trait.
    """
    if output_trait not in TRAIT_GROUPS:
        return []

    rows = _fetch_matching_rows(genome, TRAIT_GROUPS[output_trait])
    return sorted(set(trait for _, trait, _, _ in rows))


if __name__ == "__main__":
    print("DB_PATH:", DB_PATH)
    print("Exists:", DB_PATH.exists())

    ensure_indexes()

    example_genome = {
        "rs599839": {"genotype": "G/G"},
        "rs7412": {"genotype": "C/T"},
        "rs429358": {"genotype": "C/C"},
        "rs7903146": {"genotype": "C/T"},
    }

    results = compute_prs(example_genome)
    print("\nPRS RESULTS:")
    print(results)

    print("\nMatched Alzheimer traits:")
    print(inspect_matching_traits(example_genome, "alzheimer"))