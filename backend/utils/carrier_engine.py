import csv
import gzip
import os

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

CLINVAR_PATHS = [
    os.path.join(BASE_DIR, "nih", "clinvar.gz"),
    os.path.join(BASE_DIR, "clinvar.gz"),
    "backend/nih/clinvar.gz",
    "backend/clinvar.gz"
]

CLINVAR_WARNED = False
CLINVAR_LOADED_LOGGED = False

# --------------------------------------------------------------
# Load ClinVar pathogenic variants (compressed database)
# Structure:
# { rsid: { "gene": "CFTR", "variant": "F508del", "type": "pathogenic", "inheritance": "recessive" } }
# --------------------------------------------------------------

CLINVAR_DB = {}

def load_clinvar():
    global CLINVAR_DB, CLINVAR_WARNED, CLINVAR_LOADED_LOGGED
    if CLINVAR_DB:
        return

    loaded = False
    for path in CLINVAR_PATHS:
        if not os.path.exists(path):
            continue
        try:
            with gzip.open(path, "rt") as f:
                reader = csv.DictReader(f, delimiter="\t")
                for row in reader:
                    rsid = row.get("RSID")
                    if not rsid:
                        continue

                    CLINVAR_DB[rsid] = {
                        "gene": row.get("GeneSymbol", "Unknown"),
                        "variant": row.get("VariantName", ""),
                        "type": row.get("ClinicalSignificance", "").lower(),
                        "inheritance": row.get("ModeOfInheritance", "").lower(),
                    }
            loaded = True
            if not CLINVAR_LOADED_LOGGED:
                print(f"Loaded ClinVar: {len(CLINVAR_DB)} variants from {path}")
                CLINVAR_LOADED_LOGGED = True
            break
        except Exception as e:
            if not CLINVAR_WARNED:
                print(f"Failed loading ClinVar from {path}: {e}")

    if not loaded and not CLINVAR_WARNED:
        print(f"ClinVar database not found; tried paths: {CLINVAR_PATHS}")
        CLINVAR_WARNED = True


# --------------------------------------------------------------
# Helper: allele dosage
# --------------------------------------------------------------
def dosage(genotype: str, allele: str):
    if not genotype:
        return 0
    g = genotype.replace("/", "").upper()
    return g.count(allele.upper())


# --------------------------------------------------------------
# Gene-specific pathogenic variant lists (extra known SNPs)
# --------------------------------------------------------------

GENE_PANELS = {
    "CFTR": ["rs113993960", "rs80224365", "rs1800111"],
    "HBB": ["rs334", "rs33930165"],
    "PAH": ["rs5030858"],
    "TYR": ["rs1042602", "rs1126809"],
    "OCA2": ["rs1800407"],
    "GJB2": ["rs80338939", "rs72474224"],
    "MC1R": ["rs1805007", "rs1805008", "rs1805009"],
    "HEXA": ["rs1800432"],
    "ATP7B": ["rs76151636"],
    "CYP21A2": ["rs6470"],
    "GBA": ["rs76763715", "rs421016"],
    "ACADM": ["rs77931234"],
    "F8": ["rs137852795"],
    "HFE": ["rs1800562", "rs1799945"],
    "G6PD": ["rs1050828"]
}

DOMINANT_GENES = {
    "BRCA1": ["rs80357713", "rs80357756"],
    "BRCA2": ["rs80359406", "rs80359083"],
    "LDLR": ["rs121908025"],
    "FBN1": ["rs121913626"],
    "TERT": ["rs2736100"],
    "RET": ["rs79011770"]
}


# --------------------------------------------------------------
# Main carrier detection engine
# --------------------------------------------------------------
def detect_carrier_status(genome):
    """
    Returns:
    {
      "carriers": [...],
      "dominant_variants": [...]
    }
    """

    load_clinvar()

    carriers = []
    dominants = []

    # First: ClinVar pathogenic variants
    for rsid, info in genome.items():
        geno = info["genotype"].replace("/", "")

        if rsid in CLINVAR_DB:
            cinfo = CLINVAR_DB[rsid]
            if "patho" in cinfo["type"]:
                if "recess" in cinfo["inheritance"]:
                    # Carrier if heterozygous
                    if len(geno) == 2 and geno[0] != geno[1]:
                        carriers.append({
                            "gene": cinfo["gene"],
                            "rsid": rsid,
                            "variant": cinfo["variant"],
                            "status": "Carrier (ClinVar)",
                            "genotype": info.get("genotype")
                        })
                else:
                    # Dominant pathogenic variant
                    dominants.append({
                        "gene": cinfo["gene"],
                        "rsid": rsid,
                        "variant": cinfo["variant"],
                        "status": "Pathogenic (Dominant)",
                        "genotype": info.get("genotype")
                    })

    # Additional known panels
    for gene, snps in GENE_PANELS.items():
        for rsid in snps:
            if rsid in genome:
                genotype = genome[rsid]["genotype"]
                g = genotype.replace("/", "") if genotype else ""
                # carrier if heterozygous in recessive genes
                if len(g) == 2 and g[0] != g[1]:
                    carriers.append({
                        "gene": gene,
                        "rsid": rsid,
                        "variant": "Known Pathogenic Mutation",
                        "status": "Carrier",
                        "genotype": genotype
                    })

    # Dominant genes
    for gene, snps in DOMINANT_GENES.items():
        for rsid in snps:
            if rsid in genome:
                genotype = genome[rsid].get("genotype")
                dominants.append({
                    "gene": gene,
                    "rsid": rsid,
                    "variant": "Known Pathogenic",
                    "status": "Pathogenic (Dominant)",
                    "genotype": genotype
                })

    return {
        "carriers": carriers,
        "dominant_variants": dominants
    }
