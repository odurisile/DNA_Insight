from collections import defaultdict


CATALOG = [
    {"gene": "HERC2", "rsid": "rs12913832", "category": "Pigmentation", "note": "Major iris color regulator"},
    {"gene": "OCA2", "rsid": "rs1129038", "category": "Pigmentation", "note": "Eye color modifier"},
    {"gene": "OCA2", "rsid": "rs1800407", "category": "Pigmentation", "note": "Eye and skin pigmentation modifier"},
    {"gene": "SLC24A5", "rsid": "rs1426654", "category": "Pigmentation", "note": "Skin pigmentation signal"},
    {"gene": "SLC45A2", "rsid": "rs16891982", "category": "Pigmentation", "note": "Skin and hair pigmentation signal"},
    {"gene": "TYR", "rsid": "rs1042602", "category": "Pigmentation", "note": "Melanin pathway marker"},
    {"gene": "MC1R", "rsid": "rs1805007", "category": "Pigmentation", "note": "Red hair and freckling pathway"},
    {"gene": "MC1R", "rsid": "rs1805008", "category": "Pigmentation", "note": "Red hair and freckling pathway"},
    {"gene": "MC1R", "rsid": "rs1805009", "category": "Pigmentation", "note": "Red hair and freckling pathway"},
    {"gene": "IRF4", "rsid": "rs12203592", "category": "Pigmentation", "note": "Freckling and pigmentation modifier"},
    {"gene": "APOE", "rsid": "rs429358", "category": "Neuro", "note": "APOE haplotype component"},
    {"gene": "APOE", "rsid": "rs7412", "category": "Neuro", "note": "APOE haplotype component"},
    {"gene": "LCT", "rsid": "rs4988235", "category": "Diet", "note": "Lactose tolerance marker"},
    {"gene": "CYP1A2", "rsid": "rs762551", "category": "Wellness", "note": "Caffeine metabolism marker"},
    {"gene": "MTHFR", "rsid": "rs1801133", "category": "Wellness", "note": "Folate metabolism marker"},
    {"gene": "ACTN3", "rsid": "rs1815739", "category": "Fitness", "note": "Muscle performance marker"},
    {"gene": "AGT", "rsid": "rs699", "category": "Cardiometabolic", "note": "Hypertension-linked marker"},
    {"gene": "CHRNA5", "rsid": "rs16969968", "category": "Behavior", "note": "Nicotine dependence marker"},
    {"gene": "ALDH2", "rsid": "rs671", "category": "Wellness", "note": "Alcohol flush marker"},
    {"gene": "HLA-DQB1", "rsid": "rs2187668", "category": "Autoimmune", "note": "Celiac proxy marker"},
    {"gene": "HLA-DQA1", "rsid": "rs7454108", "category": "Autoimmune", "note": "Celiac proxy marker"},
    {"gene": "HFE", "rsid": "rs1800562", "category": "Iron metabolism", "note": "Hemochromatosis marker"},
    {"gene": "HFE", "rsid": "rs1799945", "category": "Iron metabolism", "note": "Hemochromatosis marker"},
    {"gene": "GLI3", "rsid": "rs4648379", "category": "Morphology", "note": "Facial morphology signal"},
    {"gene": "EDAR", "rsid": "rs3827760", "category": "Morphology", "note": "Facial morphology signal"},
]


def search_supported_genes(genome, query):
    normalized_query = (query or "").strip().lower()
    if not normalized_query:
        return []

    grouped = defaultdict(list)
    for marker in CATALOG:
        search_blob = " ".join([marker["gene"], marker["rsid"], marker["category"], marker["note"]]).lower()
        if normalized_query not in search_blob:
            continue

        observed = genome.get(marker["rsid"])
        grouped[marker["gene"]].append(
            {
                "rsid": marker["rsid"],
                "category": marker["category"],
                "note": marker["note"],
                "genotype": observed.get("genotype") if observed else None,
                "chrom": observed.get("chrom") if observed else None,
                "pos": observed.get("pos") if observed else None,
                "present_in_file": bool(observed),
            }
        )

    return [
        {
            "gene": gene,
            "matches": sorted(matches, key=lambda item: item["rsid"]),
            "matched_count": len(matches),
            "present_count": sum(1 for item in matches if item["present_in_file"]),
        }
        for gene, matches in sorted(grouped.items())
    ]
