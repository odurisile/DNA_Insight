import random
from utils.trait_engine import predict_traits
from utils.risk_engine import compute_health_risk


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


# --------------------------------------------------------------
#  Make a gamete with recombination
# --------------------------------------------------------------
def make_gamete(parent_genome):
    """
    Takes a parent's genome and returns a 'gamete':
    one allele per rsID, after recombination.
    """

    chrom_map = {}
    for rsid, info in parent_genome.items():
        chrom = info["chrom"]
        pos = info["pos"]
        geno = info["genotype"]

        if chrom not in chrom_map:
            chrom_map[chrom] = []

        chrom_map[chrom].append((pos, rsid, geno))

    gamete = {}

    # Perform recombination per chromosome
    for chrom, snps in chrom_map.items():
        snps.sort(key=lambda x: x[0])
        num_xo = random.randint(1, 3)
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

    # Sample one child for a concrete "example" output
    gamA = make_gamete(parentA_genome)
    gamB = make_gamete(parentB_genome)
    child_genome = make_child_genome(gamA, gamB, parentA_genome)
    traits = predict_traits(child_genome)
    health = compute_health_risk(child_genome)

    # Monte Carlo to approximate distribution across recombination events
    counts = {}
    sims = max(8, min(simulations, 256))
    for _ in range(sims):
        sim_gamA = make_gamete(parentA_genome)
        sim_gamB = make_gamete(parentB_genome)
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
