from utils.hirisplex_model import hirisplex_predict
from utils.apoe import compute_apoe_genotype

# ---------------------------------------------------------
#  Helper: count effect allele dosage
# ---------------------------------------------------------
def dosage(genotype: str, allele: str) -> int:
    if not genotype:
        return 0
    g = genotype.replace("/", "").upper()
    return g.count(allele.upper())


# ---------------------------------------------------------
#  Freckling Model (simplified additive polygenic model)
# ---------------------------------------------------------
def predict_freckling(genome):
    """
    Based on MC1R + IRF4 + OCA2.
    Produces: Low / Moderate / High freckling.
    """

    score = 0

    # MC1R red-hair pathway -> freckles
    for snp in ["rs1805007", "rs1805008", "rs1805009"]:
        if snp in genome:
            score += dosage(genome[snp]["genotype"], "T") * 1.2

    # IRF4 enhancer
    if "rs12203592" in genome:
        score += dosage(genome["rs12203592"]["genotype"], "T") * 0.9

    # OCA2 modifier
    if "rs12913832" in genome:
        score += dosage(genome["rs12913832"]["genotype"], "G") * 0.4

    if score < 1.0:
        return "Low"
    if score < 2.5:
        return "Moderate"
    return "High"


# ---------------------------------------------------------
#  Tanning Response Prediction
# ---------------------------------------------------------
def predict_tanning(genome):
    """
    Predicts skin UV response:
    - Burns easily
    - Burns then tans
    - Tans easily

    Based on SLC24A5, SLC45A2, MC1R.
    """
    score = 0

    # Darker pigmentation SNPs -> easier tanning
    if "rs16891982" in genome:
        score += dosage(genome["rs16891982"]["genotype"], "C") * 1.1
    if "rs1426654" in genome:
        score += dosage(genome["rs1426654"]["genotype"], "A") * 1.3

    # MC1R -> burns easily
    for snp in ["rs1805007", "rs1805008", "rs1805009"]:
        if snp in genome:
            score -= dosage(genome[snp]["genotype"], "T") * 1.2

    if score < -0.5:
        return "Burns Easily"
    if score < 1.5:
        return "Burns then Tans"
    return "Tans Easily"


# ---------------------------------------------------------
#  Facial Morphology (basic SNP-index)
#  Nose width, lip fullness, cheek prominence
# ---------------------------------------------------------
def predict_face(genome):
    """
    Returns morphological SNP-based predictions.
    Not 100% accurate, but follows known associations.
    """

    nose_score = 0
    lip_score = 0
    cheek_score = 0

    # Nose width – rs4648379 GLI3
    if "rs4648379" in genome:
        nose_score += dosage(genome["rs4648379"]["genotype"], "A") * 1.2

    # Lip fullness – rs11807848
    if "rs11807848" in genome:
        lip_score += dosage(genome["rs11807848"]["genotype"], "T") * 1.1

    # Cheek prominence – rs3827760 EDAR
    if "rs3827760" in genome:
        cheek_score += dosage(genome["rs3827760"]["genotype"], "G") * 1.4

    def label(score, low, mid):
        if score < low:
            return "Low"
        if score < mid:
            return "Moderate"
        return "High"

    return {
        "nose_width": label(nose_score, 1.0, 2.0),
        "lip_fullness": label(lip_score, 1.0, 2.0),
        "cheek_prominence": label(cheek_score, 1.0, 2.0),
    }


# ---------------------------------------------------------
#  Lactose Tolerance (rs4988235 near LCT)
# ---------------------------------------------------------
def predict_lactose(genome):
    """
    - T allele enables lactase persistence (tolerance)
    - CC associated with intolerance
    """
    key = "rs4988235"
    if key not in genome:
        return "Unknown"
    geno = (genome[key].get("genotype") or "").replace("/", "").upper()
    if "T" in geno:
        if geno.count("T") == 2:
            return "Likely tolerant (TT)"
        return "Tolerant carrier (CT)"
    if geno == "CC":
        return "Likely lactose sensitive (CC)"
    return "Unknown"


# ---------------------------------------------------------
#  Caffeine Metabolism (CYP1A2 rs762551)
# ---------------------------------------------------------
def predict_caffeine(genome):
    """
    AA: fast metabolizer
    AC: intermediate
    CC: slow metabolizer (more sensitive)
    """
    key = "rs762551"
    if key not in genome:
        return "Unknown"
    geno = (genome[key].get("genotype") or "").replace("/", "").upper()
    if geno == "AA":
        return "Fast metabolizer"
    if geno in ("AC", "CA"):
        return "Intermediate"
    if geno == "CC":
        return "Slow / sensitive"
    return "Unknown"


# ---------------------------------------------------------
#  Muscle Performance (ACTN3 rs1815739)
# ---------------------------------------------------------
def predict_muscle(genome):
    """
    CC: power/sprint enriched
    CT: mixed
    TT: endurance leaning
    """
    key = "rs1815739"
    if key not in genome:
        return "Unknown"
    geno = (genome[key].get("genotype") or "").replace("/", "").upper()
    if geno == "CC":
        return "Power / sprint"
    if geno in ("CT", "TC"):
        return "Mixed"
    if geno == "TT":
        return "Endurance leaning"
    return "Unknown"


# ---------------------------------------------------------
#  Alcohol Flush (ALDH2 rs671)
# ---------------------------------------------------------
def predict_alcohol_flush(genome):
    """
    ALDH2*2 (A allele) reduces acetaldehyde clearance -> flushing.
    """
    key = "rs671"
    if key not in genome:
        return "Unknown"
    geno = (genome[key].get("genotype") or "").replace("/", "").upper()
    if geno == "GG":
        return "No flush predisposition"
    if geno in ("AG", "GA"):
        return "Likely flush (heterozygous)"
    if geno == "AA":
        return "Strong flush (homozygous)"
    return "Unknown"


# ---------------------------------------------------------
#  Nicotine Dependence (CHRNA5 rs16969968)
# ---------------------------------------------------------
def predict_nicotine(genome):
    """
    AA: higher nicotine dependence risk
    AG: moderate
    GG: lower
    """
    key = "rs16969968"
    if key not in genome:
        return "Unknown"
    geno = (genome[key].get("genotype") or "").replace("/", "").upper()
    if geno == "AA":
        return "Higher dependence risk"
    if geno in ("AG", "GA"):
        return "Moderate dependence risk"
    if geno == "GG":
        return "Lower dependence risk"
    return "Unknown"


# ---------------------------------------------------------
#  Folate Metabolism (MTHFR C677T rs1801133)
# ---------------------------------------------------------
def predict_folate(genome):
    """
    TT: reduced enzyme activity, consider folate/B12
    CT: mildly reduced
    CC: typical
    """
    key = "rs1801133"
    if key not in genome:
        return "Unknown"
    geno = (genome[key].get("genotype") or "").replace("/", "").upper()
    if geno == "TT":
        return "Reduced activity (TT)"
    if geno in ("CT", "TC"):
        return "Slightly reduced (CT)"
    if geno == "CC":
        return "Typical activity (CC)"
    return "Unknown"


# ---------------------------------------------------------
#  Master Trait Engine
# ---------------------------------------------------------
def predict_traits(genome):
    """
    Combines:
    - HIrisPlex-S (Eye, Hair, Skin)
    - Freckles
    - Tanning
    - Facial morphology
    - Lactose tolerance
    - Caffeine metabolism
    - Muscle performance
    - Alcohol flush
    - Nicotine dependence tendency
    - Folate metabolism
    - APOE genotype
    """

    # Primary models
    iris_results = hirisplex_predict(genome)

    # Additional phenotype layers
    freckling = predict_freckling(genome)
    tanning = predict_tanning(genome)
    face = predict_face(genome)
    lactose = predict_lactose(genome)
    caffeine = predict_caffeine(genome)
    muscle = predict_muscle(genome)
    alcohol_flush = predict_alcohol_flush(genome)
    nicotine = predict_nicotine(genome)
    folate = predict_folate(genome)

    # APOE
    apoe = compute_apoe_genotype(genome)

    # Build final phenotype dictionary
    return {
        "eye_color": iris_results["eye"],
        "hair_color": iris_results["hair"],
        "skin_color": iris_results["skin"],
        "freckling": freckling,
        "tanning_response": tanning,
        "face_shape": face,
        "lactose_tolerance": lactose,
        "caffeine_metabolism": caffeine,
        "muscle_performance": muscle,
        "alcohol_flush": alcohol_flush,
        "nicotine_dependence": nicotine,
        "folate_metabolism": folate,
        "apoe_genotype": apoe,
    }
