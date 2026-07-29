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


def normalized_genotype(genotype: str) -> str:
    if not genotype:
        return ""
    return genotype.replace("/", "").upper()


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
#  Vitamin D proxy panel
# ---------------------------------------------------------
def predict_vitamin_d(genome):
    """
    Uses common vitamin D-associated markers as a simple proxy panel.
    Lower score leans toward reduced circulating vitamin D.
    """
    score = 0
    markers = 0

    if "rs2282679" in genome:  # GC
        score -= dosage(genome["rs2282679"]["genotype"], "G") * 1.2
        markers += 1
    if "rs12785878" in genome:  # DHCR7/NADSYN1
        score -= dosage(genome["rs12785878"]["genotype"], "G") * 1.0
        markers += 1
    if "rs10741657" in genome:  # CYP2R1
        score -= dosage(genome["rs10741657"]["genotype"], "A") * 0.9
        markers += 1

    if markers == 0:
        return "Unknown"
    if score <= -2.5:
        return "Lower vitamin D tendency"
    if score <= -1.0:
        return "Moderately lower vitamin D tendency"
    return "Typical vitamin D tendency"


# ---------------------------------------------------------
#  Sleep chronotype proxy panel
# ---------------------------------------------------------
def predict_sleep_chronotype(genome):
    """
    Simple morning/evening tendency model using common chronotype markers.
    """
    score = 0
    markers = 0

    if "rs12927162" in genome:  # RGS16
        score += dosage(genome["rs12927162"]["genotype"], "T") * 1.0
        markers += 1
    if "rs228697" in genome:  # PER3
        score += dosage(genome["rs228697"]["genotype"], "G") * 0.9
        markers += 1
    if "rs139315125" in genome:  # ASB1-associated chronotype signal
        score -= dosage(genome["rs139315125"]["genotype"], "A") * 1.0
        markers += 1

    if markers == 0:
        return "Unknown"
    if score >= 1.5:
        return "Morning leaning"
    if score <= -1.0:
        return "Evening leaning"
    return "Intermediate chronotype"


# ---------------------------------------------------------
#  Pain sensitivity proxy panel
# ---------------------------------------------------------
def predict_pain_sensitivity(genome):
    """
    Heuristic panel based on COMT / OPRM1 / SCN9A-linked sensitivity markers.
    """
    score = 0
    markers = 0

    if "rs4680" in genome:  # COMT Val158Met
        score += dosage(genome["rs4680"]["genotype"], "A") * 1.1
        markers += 1
    if "rs1799971" in genome:  # OPRM1 A118G
        score += dosage(genome["rs1799971"]["genotype"], "G") * 0.8
        markers += 1
    if "rs6746030" in genome:  # SCN9A
        score += dosage(genome["rs6746030"]["genotype"], "A") * 0.9
        markers += 1

    if markers == 0:
        return "Unknown"
    if score >= 2.0:
        return "Higher pain sensitivity"
    if score >= 0.8:
        return "Moderate pain sensitivity"
    return "Typical pain sensitivity"


# ---------------------------------------------------------
#  Endurance proxy panel
# ---------------------------------------------------------
def predict_endurance(genome):
    """
    Lightweight endurance tendency based on common performance-linked SNPs.
    """
    score = 0
    markers = 0

    if "rs1815739" in genome:  # ACTN3
        score += dosage(genome["rs1815739"]["genotype"], "T") * 1.1
        markers += 1
    if "rs8192678" in genome:  # PPARGC1A
        score += dosage(genome["rs8192678"]["genotype"], "A") * 0.9
        markers += 1
    if "rs4253778" in genome:  # PPARA
        score += dosage(genome["rs4253778"]["genotype"], "G") * 0.8
        markers += 1

    if markers == 0:
        return "Unknown"
    if score >= 2.0:
        return "Endurance leaning"
    if score >= 0.8:
        return "Balanced endurance profile"
    return "Power leaning"


# ---------------------------------------------------------
#  Bitter taste proxy panel
# ---------------------------------------------------------
def predict_bitter_taste(genome):
    """
    TAS2R38 common tasting haplotype proxy.
    """
    score = 0
    markers = 0

    for rsid in ["rs713598", "rs1726866", "rs10246939"]:
        if rsid in genome:
            score += dosage(genome[rsid]["genotype"], "C")
            markers += 1

    if markers == 0:
        return "Unknown"
    if score >= 4:
        return "Strong bitter taster"
    if score >= 2:
        return "Moderate bitter taster"
    return "Lower bitter sensitivity"


# ---------------------------------------------------------
#  ABO and Rh Blood Type
# ---------------------------------------------------------
def predict_blood_type(genome):
    """
    Conservative ABO and RhD blood type inference from consumer-genotype markers.

    rs8176719:
    - D allele tags the common O1 deletion
    - I allele tags a non-O allele

    rs8176746:
    - T allele tags the common B-associated haplotype
    - G allele is compatible with A/O contexts

    rs590787:
    - C/C tags the common RHD deletion associated with Rh-negative status
    - A or T indicates likely Rh-positive status (depending on reported strand)

    RhD inference from a single tag is not definitive, especially outside
    populations where the common RHD deletion explains most Rh-negative cases.
    """
    deletion_marker = genome.get("rs8176719", {}).get("genotype")
    b_marker = genome.get("rs8176746", {}).get("genotype")

    deletion_genotype = normalized_genotype(deletion_marker)
    b_genotype = normalized_genotype(b_marker)

    if not deletion_genotype or not b_genotype:
        return "Unknown"

    deletion_alleles = [allele for allele in deletion_genotype if allele in {"D", "I"}]
    b_alleles = [allele for allele in b_genotype if allele in {"G", "T"}]

    if len(deletion_alleles) != 2 or len(b_alleles) != 2:
        return "Unknown"

    o_count = deletion_alleles.count("D")
    b_count = b_alleles.count("T")

    abo_type = None
    if o_count == 2:
        abo_type = "O"
    elif o_count == 1:
        if b_count == 0:
            abo_type = "A"
        elif b_count == 1:
            abo_type = "B"
    else:
        # No O-tagged deletion allele present.
        if b_count == 0:
            abo_type = "A"
        elif b_count == 1:
            abo_type = "AB"
        elif b_count == 2:
            abo_type = "B"

    if not abo_type:
        return "Unknown"

    rh_genotype = normalized_genotype(
        genome.get("rs590787", {}).get("genotype")
    )
    rh_alleles = [allele for allele in rh_genotype if allele in {"A", "C", "G", "T"}]

    if len(rh_alleles) != 2:
        return f"Likely type {abo_type} (Rh unknown)"

    # Accept both strand orientations: C/C (or complementary G/G) tags Rh-.
    rh_status = "-" if set(rh_alleles) in ({"C"}, {"G"}) else "+"
    return f"Likely type {abo_type}{rh_status}"


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
    vitamin_d = predict_vitamin_d(genome)
    sleep_chronotype = predict_sleep_chronotype(genome)
    pain_sensitivity = predict_pain_sensitivity(genome)
    endurance = predict_endurance(genome)
    bitter_taste = predict_bitter_taste(genome)
    blood_type = predict_blood_type(genome)

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
        "vitamin_d": vitamin_d,
        "sleep_chronotype": sleep_chronotype,
        "pain_sensitivity": pain_sensitivity,
        "endurance": endurance,
        "bitter_taste": bitter_taste,
        "blood_type": blood_type,
        "apoe_genotype": apoe,
    }
