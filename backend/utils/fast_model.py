############################################################
# FAST POLYGENIC TRAIT PREDICTOR
# (Lightweight alternative to full HIrisPlex-S model)
############################################################

FAST_SNPS = {
    "eye_color": [
        "rs12913832",  # HERC2 main driver
        "rs1800407",   # OCA2 green modifier
        "rs12896399",  # SLC24A4 blue/light modifier
        "rs16891982",  # SLC45A2 pigmentation
        "rs12203592",  # IRF4 enhancer
        "rs1393350"    # TYR light pigmentation
    ],
    "hair_color": [
        "rs1805007",  # MC1R red hair
        "rs1805008",
        "rs1805009",
        "rs12913832", # indirectly impacts hair lightness
        "rs12821256", # blonde variant
        "rs16891982", # light pigment
        "rs3829241",  # brown vs black
    ],
    "skin_color": [
        "rs1426654", # SLC24A5 major light/dark SNP
        "rs16891982",# SLC45A2
        "rs1042602", # TYR
        "rs1800414", # OCA2 (East Asian depigmentation)
        "rs6058017", # DDB1/TMEM138 (African pigment SNP)
    ],
    "freckling": [
        "rs12203592", # IRF4 major freckling SNP
        "rs2153271",  # BNC2
        "rs6059655"   # MC1R
    ],
    "tanning": [
        "rs1805007",
        "rs1805008",
        "rs12913832",
        "rs26722"
    ],
}


############################################################
# Utility
############################################################

def gt(genotypes, snp):
    """Safe genotype getter."""
    return genotypes.get(snp, "")


############################################################
# EYE COLOR — FAST MODEL
############################################################
def fast_eye_color(genotypes):

    scores = { "blue":0, "green":0, "hazel":0, "brown":0 }

    # HERC2 rs12913832 (primary determinant)
    rs = gt(genotypes, "rs12913832")
    if rs == "AA":
        scores["blue"] += 40
    elif rs == "AG":
        scores["green"] += 30
        scores["hazel"] += 8
    else:
        scores["brown"] += 40
        scores["hazel"] += 10

    # OCA2 rs1800407 – green/hazel modifier
    rs = gt(genotypes, "rs1800407")
    if rs in ["AG","GG"]:
        scores["green"] += 20
        scores["hazel"] += 10

    # SLC24A4 rs12896399 – blue lightener
    rs = gt(genotypes, "rs12896399")
    if rs == "GG":
        scores["blue"] += 10
    elif rs == "GT":
        scores["blue"] += 5

    # IRF4 rs12203592 – blue/green enhancer
    rs = gt(genotypes, "rs12203592")
    if rs == "TT":
        scores["blue"] += 12
        scores["green"] += 6

    total = sum(scores.values()) or 1
    probs = {k: v/total for k,v in scores.items()}
    result = max(probs, key=probs.get)

    return {
        "result": result.capitalize(),
        "confidence": probs[result],
        "scores": probs
    }


############################################################
# HAIR COLOR — FAST MODEL
############################################################
def fast_hair_color(genotypes):

    scores = {"black":0, "brown":0, "blonde":0, "red":0}

    # MC1R — red hair variants
    red_snps = ["rs1805007","rs1805008","rs1805009"]
    red_hits = sum(1 for snp in red_snps if "T" in gt(genotypes, snp))
    
    if red_hits >= 2:
        scores["red"] += 50
    elif red_hits == 1:
        scores["red"] += 20

    # SLC45A2 rs16891982 — light pigmentation
    rs = gt(genotypes, "rs16891982")
    if rs == "CC":
        scores["blonde"] += 25
    elif rs == "CG":
        scores["blonde"] += 10

    # rs12821256 — strong blonde variant
    rs = gt(genotypes, "rs12821256")
    if rs == "AA":
        scores["blonde"] += 30
    elif rs == "AC":
        scores["blonde"] += 15

    # rs3829241 — black vs brown
    rs = gt(genotypes, "rs3829241")
    if rs == "AA":
        scores["black"] += 25
    elif rs == "AG":
        scores["brown"] += 10

    total = sum(scores.values()) or 1
    probs = {k: v/total for k,v in scores.items()}
    result = max(probs, key=probs.get)

    return {
        "result": result.capitalize(),
        "confidence": probs[result],
        "scores": probs
    }


############################################################
# SKIN COLOR — FAST MODEL
############################################################
def fast_skin_color(genotypes):

    scores = {"light":0, "medium":0, "dark":0}

    rs = gt(genotypes, "rs1426654")
    if rs == "AA":
        scores["light"] += 40
    elif rs == "AG":
        scores["medium"] += 20
    else:
        scores["dark"] += 40

    rs = gt(genotypes, "rs16891982")
    if rs == "CC":
        scores["light"] += 20
    elif rs == "CG":
        scores["medium"] += 10

    rs = gt(genotypes, "rs1800414")
    if rs == "CC":
        scores["light"] += 25

    total = sum(scores.values()) or 1
    probs = {k: v/total for k,v in scores.items()}
    result = max(probs, key=probs.get)

    return {
        "result": result.capitalize(),
        "confidence": probs[result],
        "scores": probs
    }


############################################################
# FRECKLING — FAST MODEL
############################################################
def fast_freckling(genotypes):
    score = 0

    if gt(genotypes,"rs12203592") == "TT":
        score += 40
    if gt(genotypes,"rs2153271") in ["AG","GG"]:
        score += 25
    if "T" in gt(genotypes,"rs6059655"):
        score += 25

    intensity = "Low"
    if score > 60: intensity = "High"
    elif score > 30: intensity = "Medium"

    return {
        "result": intensity,
        "confidence": min(score/100,1),
        "score": score
    }


############################################################
# TANNING — FAST MODEL
############################################################
def fast_tanning(genotypes):
    score = 0

    if "T" in gt(genotypes, "rs1805007"):
        score += 30
    if "T" in gt(genotypes, "rs1805008"):
        score += 20
    if gt(genotypes,"rs12913832") == "AA":
        score += 15

    level = "Tans easily"
    if score > 50: level = "Burns easily"
    elif score > 25: level = "Mixed"

    return {
        "result": level,
        "confidence": min(score/100,1),
        "score": score
    }


############################################################
# RED HAIR PROBABILITY
############################################################
def fast_red_hair_probability(genotypes):
    red_snps = ["rs1805007","rs1805008","rs1805009"]
    hits = sum(1 for snp in red_snps if "T" in gt(genotypes, snp))

    if hits >= 2:
        prob = 0.75
    elif hits == 1:
        prob = 0.35
    else:
        prob = 0.03

    return {
        "probability": prob,
        "percent": prob*100
    }


############################################################
# MAIN FAST MODE WRAPPER
############################################################
def run_fast_model(genotypes):
    return {
        "eye_color": fast_eye_color(genotypes),
        "hair_color": fast_hair_color(genotypes),
        "skin_color": fast_skin_color(genotypes),
        "freckling": fast_freckling(genotypes),
        "tanning": fast_tanning(genotypes),
        "red_hair_probability": fast_red_hair_probability(genotypes),
    }
