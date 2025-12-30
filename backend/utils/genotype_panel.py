"""
Builds a small, human-friendly genotype panel for key pigmentation
and neuro/cardio markers used across the app. This is meant to power
the front-end "evidence" view without exposing the full genome.
"""

GENE_BLOCKS = [
    {
        "title": "Pigmentation (HERC2 / OCA2)",
        "description": "Primary drivers for iris color intensity.",
        "snps": [
            {"rsid": "rs12913832", "gene": "HERC2"},
            {"rsid": "rs1129038", "gene": "OCA2"},
            {"rsid": "rs1800407", "gene": "OCA2"},
        ],
    },
    {
        "title": "Melanin Transport (SLC24A5 / SLC45A2)",
        "description": "Skin and hair light/dark balance.",
        "snps": [
            {"rsid": "rs1426654", "gene": "SLC24A5"},
            {"rsid": "rs16891982", "gene": "SLC45A2"},
            {"rsid": "rs1042602", "gene": "TYR"},
        ],
    },
    {
        "title": "MC1R Pathway (Hair / Freckling)",
        "description": "Red hair likelihood and freckling intensity.",
        "snps": [
            {"rsid": "rs1805007", "gene": "MC1R"},
            {"rsid": "rs1805008", "gene": "MC1R"},
            {"rsid": "rs1805009", "gene": "MC1R"},
            {"rsid": "rs12203592", "gene": "IRF4"},
        ],
    },
    {
        "title": "APOE (Neuro)",
        "description": "Late-onset Alzheimer's risk modulation.",
        "snps": [
            {"rsid": "rs429358", "gene": "APOE"},
            {"rsid": "rs7412", "gene": "APOE"},
        ],
    },
    {
        "title": "Diet & Metabolism",
        "description": "Lactose tolerance, caffeine metabolism, and related nutritional traits.",
        "snps": [
            {"rsid": "rs4988235", "gene": "LCT"},
            {"rsid": "rs762551", "gene": "CYP1A2"},
            {"rsid": "rs1801133", "gene": "MTHFR"},
        ],
    },
    {
        "title": "Performance & Cardiometabolic",
        "description": "Muscle fiber bias and hypertension-linked markers.",
        "snps": [
            {"rsid": "rs1815739", "gene": "ACTN3"},
            {"rsid": "rs699", "gene": "AGT"},
            {"rsid": "rs16969968", "gene": "CHRNA5"},
        ],
    },
    {
        "title": "Alcohol Flush",
        "description": "ALDH2 variant influencing acetaldehyde metabolism.",
        "snps": [
            {"rsid": "rs671", "gene": "ALDH2"},
        ],
    },
    {
        "title": "Celiac Risk (HLA proxies)",
        "description": "Common HLA-DQ2/DQ8 tagging variants used in consumer reports.",
        "snps": [
            {"rsid": "rs2187668", "gene": "HLA-DQB1"},
            {"rsid": "rs7454108", "gene": "HLA-DQA1"},
        ],
    },
    {
        "title": "Iron Metabolism",
        "description": "Hereditary hemochromatosis-associated HFE variants.",
        "snps": [
            {"rsid": "rs1800562", "gene": "HFE"},
            {"rsid": "rs1799945", "gene": "HFE"},
        ],
    },
]


def extract_genotype_panel(genome):
    """
    Returns a concise list of gene/SNP calls present in the genome.
    Output:
    [
      {
        "title": "...",
        "description": "...",
        "snps": [
          {"rsid": "rs12913832", "gene": "HERC2", "genotype": "A/G"},
          ...
        ]
      },
      ...
    ]
    """
    panel = []
    for block in GENE_BLOCKS:
        calls = []
        for snp in block["snps"]:
            rsid = snp["rsid"]
            if rsid in genome:
                genotype = genome[rsid].get("genotype")
                if genotype:
                    calls.append({
                        "rsid": rsid,
                        "gene": snp.get("gene"),
                        "genotype": genotype
                    })

        if calls:
            panel.append({
                "title": block["title"],
                "description": block.get("description", ""),
                "snps": calls
            })

    return panel
