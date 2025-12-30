import math

# ---------------------------------------------------------
#  HIrisPlex-S Logistic Regression Coefficients
# ---------------------------------------------------------

EYE_MODEL = {
    "blue": {
        "intercept": 1.523,
        "snps": {
            "rs1129038": ("A", 1.85),
            "rs12913832": ("G", 4.12),
            "rs1800407": ("T", 1.31),
            "rs12896399": ("T", 0.47),
            "rs16891982": ("C", 0.78),
        },
    },
    "intermediate": {
        "intercept": -0.83,
        "snps": {
            "rs12913832": ("G", -2.51),
            "rs12203592": ("T", 1.25),
            "rs16891982": ("C", 0.32),
        },
    },
    "brown": {
        "intercept": -2.19,
        "snps": {
            "rs12913832": ("A", 2.71),
            "rs1800407": ("C", -1.12),
            "rs12896399": ("C", 0.41),
            "rs16891982": ("G", 0.76),
        },
    },
}

HAIR_MODEL = {
    "blond": {
        "intercept": -1.55,
        "snps": {
            "rs12821256": ("T", 2.25),
            "rs1805008": ("T", -1.31),
            "rs1805007": ("T", -1.02),
        },
    },
    "brown": {
        "intercept": 0.61,
        "snps": {
            "rs12913832": ("A", 1.14),
            "rs16891982": ("G", -0.42),
        },
    },
    "red": {
        "intercept": -3.41,
        "snps": {
            "rs1805007": ("T", 3.1),
            "rs1805008": ("T", 2.55),
            "rs1805009": ("T", 1.85),
        },
    },
    "black": {
        "intercept": -0.92,
        "snps": {
            "rs16891982": ("C", 2.12),
            "rs1426654": ("A", 1.41),
        },
    },
}

SKIN_MODEL = {
    "intercept": -1.95,
    "snps": {
        "rs1426654": ("A", 3.88),
        "rs16891982": ("C", 1.27),
        "rs1042602": ("A", 0.96),
        "rs1800407": ("T", 0.57),
        "rs2228479": ("A", 0.74),
        "rs4959270": ("G", 0.44),
        "rs885479": ("A", -0.62),
    },
}

# ---------------------------------------------------------
# Helper Functions
# ---------------------------------------------------------

def _allele_dosage(geno, effect):
    """Return 0–2 copies of an effect allele."""
    if not geno:
        return 0
    geno = geno.replace("/", "").replace("|", "").replace(" ", "").upper()
    effect = effect.upper()
    # Count how many of the characters match the effect allele
    return sum(1 for base in geno if base == effect)


def _logit(intercept, snps, genome):
    x = intercept
    for rsid, (effect, beta) in snps.items():
        g = genome.get(rsid)
        if not g:
            continue
        dosage = _allele_dosage(g.get("genotype"), effect)
        x += beta * dosage
    return x


def _softmax(logits):
    exps = [math.exp(v) for v in logits]
    total = sum(exps)
    if total == 0:
        return [1 / len(logits)] * len(logits)
    return [e / total for e in exps]


# ---------------------------------------------------------
#  Eye Color Prediction
# ---------------------------------------------------------

def _quick_herc2_call(genome):
    """Safety net: rs12913832 dominant brown call unless homozygous G/G."""
    g = genome.get("rs12913832")
    if not g:
        return None
    geno = (g.get("genotype") or "").upper()
    geno = geno.replace("/", "").replace("|", "").replace(" ", "")

    if "A" in geno:
        return "Brown"
    if geno == "GG":
        return "Blue"
    return None


def predict_eye(genome):
    # Strong HERC2 rule: any A allele biases to brown regardless of model logits
    herc2 = genome.get("rs12913832")
    if herc2 and herc2.get("genotype"):
        geno = herc2["genotype"].replace("/", "").replace("|", "").upper()
        if "A" in geno:
            return {
                "result": "Brown",
                "probabilities": {"Brown": 0.82, "Hazel": 0.1, "Green": 0.06, "Blue": 0.02},
                "confidence": 0.82,
                "model": "HERC2 override (A allele present)"
            }

    # Count how many of the eye SNPs we actually have
    present = {
        rsid
        for model in EYE_MODEL.values()
        for rsid in model["snps"].keys()
        if rsid in genome
    }

    if len(present) < 2:
        # Not enough information → don’t pretend we know
        quick = _quick_herc2_call(genome)
        if quick:
            return {
                "result": quick,
                "probabilities": {quick: 1.0},
                "confidence": 1.0,
                "model": "rs12913832 heuristic (low SNP coverage)",
            }
        return {
            "result": "Unknown",
            "probabilities": {},
            "confidence": 0.0,
            "model": "HIrisPlex-S (Eye) — insufficient SNPs",
        }

    logits = []
    colors = ["blue", "intermediate", "brown"]

    for c in colors:
        model = EYE_MODEL[c]
        logits.append(_logit(model["intercept"], model["snps"], genome))

    probs = _softmax(logits)
    proto = {
        "Blue": probs[0],
        "Green/Hazel": probs[1],
        "Brown": probs[2],
    }

    # Split intermediate into green/hazel
    green = proto["Green/Hazel"] * 0.7
    hazel = proto["Green/Hazel"] * 0.3

    final = {
        "Blue": proto["Blue"],
        "Green": green,
        "Hazel": hazel,
        "Brown": proto["Brown"],
    }

    best = max(final, key=final.get)

    # If rs12913832 gives a very contradictory call, you can optionally override here.
    quick = _quick_herc2_call(genome)
    if quick and (quick == "Brown" or final.get(quick, 0) + 0.15 > final[best]):
        best = quick

    return {
        "result": best,
        "probabilities": final,
        "confidence": final[best],
        "model": "HIrisPlex-S (Eye) + rs12913832 safety net",
    }


# ---------------------------------------------------------
#  Hair Color Prediction
# ---------------------------------------------------------

def predict_hair(genome):
    logits = []
    colors = ["blond", "brown", "red", "black"]

    for c in colors:
        model = HAIR_MODEL[c]
        logits.append(_logit(model["intercept"], model["snps"], genome))

    probs = _softmax(logits)
    final = {
        "Blond": probs[0],
        "Brown": probs[1],
        "Red": probs[2],
        "Black": probs[3],
    }

    best = max(final, key=final.get)
    return {
        "result": best,
        "probabilities": final,
        "confidence": final[best],
        "model": "HIrisPlex-S (Hair)",
    }


# ---------------------------------------------------------
#  Skin Pigmentation Prediction
# ---------------------------------------------------------

def predict_skin(genome):
    model = SKIN_MODEL
    x = _logit(model["intercept"], model["snps"], genome)
    melanin_index = 1 / (1 + math.exp(-x))

    categories = {
        "Very Light": 0.15,
        "Light": 0.30,
        "Medium": 0.45,
        "Brown": 0.60,
        "Dark": 0.75,
        "Very Dark": 0.90,
    }

    result = min(categories, key=lambda k: abs(categories[k] - melanin_index))

    return {
        "result": result,
        "melanin_index": melanin_index,
        "model": "HIrisPlex-S (Skin)",
    }


# ---------------------------------------------------------
# Unified interface
# ---------------------------------------------------------

def hirisplex_predict(genome):
    return {
        "eye": predict_eye(genome),
        "hair": predict_hair(genome),
        "skin": predict_skin(genome),
    }
