import random
from utils.trait_engine import predict_traits
from utils.risk_engine import compute_health_risk

TRAIT_RELEVANT_RSIDS = {
    "rs1129038",
    "rs11807848",
    "rs12203592",
    "rs12785878",
    "rs12821256",
    "rs12896399",
    "rs12913832",
    "rs12927162",
    "rs139315125",
    "rs1426654",
    "rs16891982",
    "rs16969968",
    "rs1726866",
    "rs1799971",
    "rs1800407",
    "rs1801133",
    "rs1805007",
    "rs1805008",
    "rs1805009",
    "rs1815739",
    "rs2228479",
    "rs2282679",
    "rs228697",
    "rs3827760",
    "rs4253778",
    "rs429358",
    "rs4648379",
    "rs4680",
    "rs4959270",
    "rs4988235",
    "rs671",
    "rs6746030",
    "rs713598",
    "rs7412",
    "rs762551",
    "rs8192678",
    "rs885479",
    "rs8176719",
    "rs8176746",
    "rs590787",
    "rs10246939",
    "rs1042602",
    "rs10741657",
}


# --------------------------------------------------------------
#  Helper: get allele 1 or allele 2 randomly
# --------------------------------------------------------------
def split_genotype(geno):
    """
    Convert "A/G" -> ["A","G"]
    """
    g = geno.replace("/", "").upper()
    if len(g) != 2:
        return ["N", "N"]
    return [g[0], g[1]]


def _build_chrom_map(genome, allowed_rsids=None):
    chrom_map = {}

    for rsid, info in genome.items():
        if allowed_rsids is not None and rsid not in allowed_rsids:
            continue

        chrom = info["chrom"]
        pos = info["pos"]
        geno = info["genotype"]

        chrom_map.setdefault(chrom, []).append((pos, rsid, geno))

    for snps in chrom_map.values():
        snps.sort(key=lambda x: x[0])

    return chrom_map


# --------------------------------------------------------------
#  Make a gamete with recombination
# --------------------------------------------------------------
def make_gamete(parent_genome):
    """
    Takes a parent's genome and returns a 'gamete':
    one allele per rsID, after recombination.
    """
    return make_gamete_from_chrom_map(_build_chrom_map(parent_genome))


def make_gamete_from_chrom_map(chrom_map):
    gamete = {}

    for snps in chrom_map.values():
        if not snps:
            continue

        max_xo = min(3, len(snps))
        num_xo = random.randint(1, max_xo)
        crossover_points = sorted(random.sample(range(len(snps)), num_xo))

        current_side = random.randint(0, 1)
        xo_index = 0

        for i, (pos, rsid, geno) in enumerate(snps):
            alleles = split_genotype(geno)
            gamete[rsid] = alleles[current_side]

            if xo_index < len(crossover_points) and i == crossover_points[xo_index]:
                current_side = 1 - current_side
                xo_index += 1

    return gamete


# --------------------------------------------------------------
#  Combine gametes -> child diploid genome
# --------------------------------------------------------------
def make_child_genome(gamA, gamB, parent_template):
    """
    parent_template: used to retrieve chrom + pos structure
    """

    child = {}

    for rsid, info in parent_template.items():
        a1 = gamA.get(rsid, "N")
        a2 = gamB.get(rsid, "N")

        child[rsid] = {
            "genotype": f"{a1}/{a2}",
            "chrom": info["chrom"],
            "pos": info["pos"],
        }

    return child


# --------------------------------------------------------------
#  Master Child Prediction (traits + health)
# --------------------------------------------------------------
def _summarize_trait_results(traits_dict):
    """
    Convert detailed trait dict into {trait: result_string} for aggregation.
    """
    summary = {}
    for key, val in traits_dict.items():
        if isinstance(val, dict) and "result" in val:
            summary[key] = val["result"]
        elif isinstance(val, dict):
            # collapse nested dict (e.g., face_shape) into a deterministic string
            try:
                import json
                summary[key] = json.dumps(val, sort_keys=True)
            except Exception:
                summary[key] = str(val)
        else:
            summary[key] = val
    return summary


def predict_child(parentA_genome, parentB_genome, simulations: int = 64):
    """
    Full child simulation:
    - Gamete formation + recombination
    - Child diploid genome
    - Trait prediction
    - Health risk
    - Monte Carlo over recombinations for trait probability summaries
    """

    parentA_chrom_map = _build_chrom_map(parentA_genome)
    parentB_chrom_map = _build_chrom_map(parentB_genome)
    parentA_trait_chrom_map = _build_chrom_map(parentA_genome, allowed_rsids=TRAIT_RELEVANT_RSIDS)
    parentB_trait_chrom_map = _build_chrom_map(parentB_genome, allowed_rsids=TRAIT_RELEVANT_RSIDS)

    # Sample one child for a concrete "example" output
    gamA = make_gamete_from_chrom_map(parentA_chrom_map)
    gamB = make_gamete_from_chrom_map(parentB_chrom_map)
    child_genome = make_child_genome(gamA, gamB, parentA_genome)
    traits = predict_traits(child_genome)
    health = compute_health_risk(child_genome)

    # Monte Carlo to approximate distribution across recombination events
    counts = {}
    sims = max(8, min(simulations, 32))
    for _ in range(sims):
        sim_gamA = make_gamete_from_chrom_map(parentA_trait_chrom_map)
        sim_gamB = make_gamete_from_chrom_map(parentB_trait_chrom_map)
        sim_child = make_child_genome(sim_gamA, sim_gamB, parentA_genome)
        sim_traits = predict_traits(sim_child)
        summary = _summarize_trait_results(sim_traits)
        for trait, val in summary.items():
            counts.setdefault(trait, {})
            counts[trait][val] = counts[trait].get(val, 0) + 1

    distribution = {
        trait: {val: round(cnt / sims, 4) for val, cnt in vals.items()}
        for trait, vals in counts.items()
    }

    return {
        "child_traits": traits,
        "child_health": health,
        "child_trait_distribution": distribution,
    }
