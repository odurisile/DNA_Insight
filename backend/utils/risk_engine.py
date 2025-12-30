from utils.prs_engine import compute_prs
from utils.carrier_engine import detect_carrier_status
from utils.apoe import compute_apoe_genotype


# -------------------------------------------------------------
# Priority order:
# - Pathogenic dominant variant → HIGH RISK
# - Risk allele (APOE e4/e4, e3/e4) → ELEVATED
# - PRS percentile → MODERATE/HIGH/LOW
# - Recessive carrier → no risk unless homozygous
# -------------------------------------------------------------

def prs_category(percentile: float):
    """
    Convert PRS percentile → risk category.
    """
    if percentile is None:
        return "Unknown"
    if percentile >= 90:
        return "High"
    if percentile >= 70:
        return "Moderate"
    if percentile >= 30:
        return "Average"
    if percentile >= 10:
        return "Low"
    return "Very Low"


def apoe_risk(apoe):
    """
    Convert APOE genotype → Alzheimer's risk annotation.
    """

    if apoe["genotype"] in ["Unknown", None]:
        return "Unknown"

    mapping = {
        "e2/e2": "Reduced",
        "e2/e3": "Reduced",
        "e3/e3": "Average",
        "e2/e4": "Slightly Elevated",
        "e3/e4": "Elevated",
        "e4/e4": "High",
    }

    return mapping.get(apoe["genotype"], "Unknown")


def allele_risk_label(genome, rsid, risk_allele):
    """
    Quick single-SNP risk classifier returning a category and dosage.
    """
    if rsid not in genome:
        return {"category": "Unknown", "dosage": 0}
    geno = (genome[rsid].get("genotype") or "").replace("/", "").upper()
    dosage = geno.count(risk_allele.upper())
    if dosage >= 2:
        category = "High"
    elif dosage == 1:
        category = "Elevated"
    else:
        category = "Average"
    return {"category": category, "dosage": dosage, "genotype": geno}


# -------------------------------------------------------------
# Final Risk Engine (Main Output)
# -------------------------------------------------------------

def compute_health_risk(genome):
    """
    Integrates:
    - PRS
    - APOE
    - ClinVar pathogenic variants
    - Carrier screening
    Returns master health summary.
    """

    # 1. Get PRS
    prs = compute_prs(genome)

    # 2. ClinVar: carriers + dominant pathogenic mutations
    carriers_info = detect_carrier_status(genome)
    carrier_list = carriers_info["carriers"]
    dominant_list = carriers_info["dominant_variants"]

    # 3. APOE risk
    apoe = compute_apoe_genotype(genome)
    alz_risk = apoe_risk(apoe)

    # ---------------------------------------------------------
    # Compose Health Interpretations
    # ---------------------------------------------------------

    # If a dominant pathogenic variant exists → force HIGH risk
    dominant_risk = "None"
    if len(dominant_list) > 0:
        dominant_risk = "High"

    # PRS-based risk
    diabetes_risk = prs_category(prs["diabetes"]["percentile"]) if prs["diabetes"] else "Unknown"
    heart_risk = prs_category(prs["heart_disease"]["percentile"]) if prs["heart_disease"] else "Unknown"
    obesity_risk = prs_category(prs["bmi"]["percentile"]) if prs["bmi"] else "Unknown"
    height_percentile = prs["height"]["percentile"] if prs["height"] else None

    # Targeted SNP-based risks
    celiac = allele_risk_label(genome, "rs2187668", "T")
    celiac_alt = allele_risk_label(genome, "rs7454108", "C")
    # take the higher risk between the two markers
    rank = {"Unknown": 0, "Average": 1, "Elevated": 2, "High": 3}
    celiac_risk = max([celiac["category"], celiac_alt["category"]], key=lambda x: rank.get(x, 0))

    hypertension = allele_risk_label(genome, "rs699", "T")
    hemo_c282y = allele_risk_label(genome, "rs1800562", "A")  # HFE C282Y
    hemo_h63d = allele_risk_label(genome, "rs1799945", "G")   # HFE H63D
    hemo_rank = {"Unknown": 0, "Average": 1, "Elevated": 2, "High": 3}
    hemo_risk = max([hemo_c282y["category"], hemo_h63d["category"]], key=lambda x: hemo_rank.get(x, 0))

    # Compose structured JSON
    output = {
        "apoe": apoe,
        "prs": prs,
        "carrier_status": carrier_list,
        "dominant_mutations": dominant_list,
        "risk_summary": {
            "Alzheimers": alz_risk,
            "Diabetes": diabetes_risk,
            "HeartDisease": heart_risk,
            "Obesity": obesity_risk,
            "DominantMutations": dominant_risk,
            "Celiac": celiac_risk,
            "Hypertension": hypertension["category"],
            "Hemochromatosis": hemo_risk
        },
        "height_percentile": height_percentile,
        "targeted": {
            "celiac": celiac,
            "celiac_support": celiac_alt,
            "hypertension": hypertension,
            "hemo_c282y": hemo_c282y,
            "hemo_h63d": hemo_h63d
        }
    }

    return output
