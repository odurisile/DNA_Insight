import csv
import gzip
import os
import re
from collections import defaultdict

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

CLINVAR_PATHS = [
    os.path.join(BASE_DIR, "nih", "clinvar.gz"),
    os.path.join(BASE_DIR, "clinvar.gz"),
    "backend/nih/clinvar.gz",
    "backend/clinvar.gz",
]

CLINVAR_INDEX_CACHE = {}
CLINVAR_WARNED = False
CLINVAR_LOADED_LOGGED = False

# Conservative report catalog. We only apply inheritance labels when the
# allele and mode have been explicitly curated.
REPORTABLE_VARIANT_CATALOG = {
    "rs5030858": [{"alt": "A", "inheritance": "autosomal_recessive"}],
    "rs334": [{"alt": "A", "inheritance": "autosomal_recessive"}],
    "rs33930165": [
        {"alt": "A", "inheritance": "autosomal_recessive"},
        {"alt": "T", "inheritance": "autosomal_recessive"},
    ],
    "rs72474224": [
        {"alt": "A", "inheritance": "autosomal_recessive"},
        {"alt": "T", "inheritance": "autosomal_recessive"},
    ],
    "rs76151636": [{"alt": "T", "inheritance": "autosomal_recessive"}],
    "rs77931234": [
        {"alt": "C", "inheritance": "autosomal_recessive"},
        {"alt": "G", "inheritance": "autosomal_recessive"},
    ],
    "rs80359083": [{"alt": "A", "inheritance": "autosomal_dominant"}],
    "rs1050828": [{"alt": "T", "inheritance": "x_linked_recessive"}],
    "rs121908025": [{"alt": "G", "inheritance": "autosomal_dominant"}],
    "rs121913626": [
        {"alt": "A", "inheritance": "autosomal_dominant"},
        {"alt": "G", "inheritance": "autosomal_dominant"},
        {"alt": "T", "inheritance": "autosomal_dominant"},
    ],
}


def _normalize_rsid(value):
    if value in (None, "", "-"):
        return None
    text = str(value).strip()
    if not text:
        return None
    return text if text.startswith("rs") else f"rs{text}"


def _normalize_allele(value):
    if value in (None, "", "-"):
        return None
    text = str(value).strip().upper()
    if re.fullmatch(r"[ACGT]", text):
        return text
    return None


def _normalize_gene(gene):
    if not gene:
        return "Unknown"
    return str(gene).split(";")[0].strip() or "Unknown"


def _genotype_alleles(genotype):
    if not genotype:
        return []
    return re.findall(r"[ACGT]", str(genotype).upper())


def allele_dosage(genotype, allele):
    normalized = _normalize_allele(allele)
    alleles = _genotype_alleles(genotype)
    if not normalized or len(alleles) != 2:
        return None
    return sum(1 for observed in alleles if observed == normalized)


def classify_zygosity(genotype, allele):
    dosage = allele_dosage(genotype, allele)
    if dosage is None:
        return "ambiguous"
    if dosage == 0:
        return "reference"
    if dosage == 1:
        return "heterozygous"
    return "homozygous_alt"


def _parse_significance_tokens(value):
    raw = (value or "").strip().lower()
    if not raw:
        return set()
    pieces = []
    for chunk in re.split(r"[;,]", raw):
        chunk = chunk.strip()
        if not chunk:
            continue
        if chunk == "pathogenic/likely pathogenic":
            pieces.extend(["pathogenic", "likely pathogenic"])
        elif chunk == "benign/likely benign":
            pieces.extend(["benign", "likely benign"])
        else:
            pieces.append(chunk)
    return set(pieces)


def _is_germline_origin(origin):
    tokens = {token.strip().lower() for token in str(origin or "").split(";") if token.strip()}
    return bool(tokens & {"germline", "inherited", "maternal", "paternal", "biparental"})


def _summarize_clinvar_rows(rows):
    significance_tokens = set()
    review_statuses = set()
    origins = set()
    names = set()
    genes = set()

    for row in rows:
        significance_tokens.update(_parse_significance_tokens(row.get("clinical_significance")))
        if row.get("review_status"):
            review_statuses.add(row["review_status"])
        if row.get("origin"):
            origins.add(row["origin"])
        if row.get("name"):
            names.add(row["name"])
        if row.get("gene"):
            genes.add(row["gene"])

    if not rows:
        return {"is_reportable": False, "reason": "missing_clinvar_record"}

    if not any(_is_germline_origin(origin) for origin in origins):
        return {"is_reportable": False, "reason": "non_germline"}

    disqualifying = {
        "benign",
        "likely benign",
        "uncertain significance",
        "not provided",
        "conflicting classifications of pathogenicity",
        "association",
        "drug response",
        "other",
        "protective",
        "risk factor",
        "affects",
    }
    if significance_tokens & disqualifying:
        return {
            "is_reportable": False,
            "reason": "non_reportable_significance",
            "significance_tokens": significance_tokens,
            "review_statuses": review_statuses,
            "genes": genes,
            "names": names,
        }

    if not significance_tokens:
        return {"is_reportable": False, "reason": "missing_significance"}

    if not significance_tokens <= {"pathogenic", "likely pathogenic"}:
        return {
            "is_reportable": False,
            "reason": "ambiguous_significance",
            "significance_tokens": significance_tokens,
            "review_statuses": review_statuses,
            "genes": genes,
            "names": names,
        }

    if "pathogenic" in significance_tokens and "likely pathogenic" in significance_tokens:
        label = "Pathogenic/Likely pathogenic"
    elif "pathogenic" in significance_tokens:
        label = "Pathogenic"
    else:
        label = "Likely pathogenic"

    return {
        "is_reportable": True,
        "clinical_significance": label,
        "significance_tokens": significance_tokens,
        "review_statuses": review_statuses,
        "genes": genes,
        "names": names,
    }


def load_clinvar(allowed_rsids=None):
    global CLINVAR_INDEX_CACHE, CLINVAR_WARNED, CLINVAR_LOADED_LOGGED
    cache_key = tuple(sorted(allowed_rsids)) if allowed_rsids else ("__all__",)
    if cache_key in CLINVAR_INDEX_CACHE:
        return CLINVAR_INDEX_CACHE[cache_key]

    index = defaultdict(list)
    loaded = False

    for path in CLINVAR_PATHS:
        if not os.path.exists(path):
            continue
        try:
            with gzip.open(path, "rt", encoding="utf-8", errors="ignore") as handle:
                reader = csv.DictReader(handle, delimiter="\t")
                for row in reader:
                    rsid = _normalize_rsid(row.get("RSID") or row.get("RS# (dbSNP)") or row.get("RS#"))
                    if not rsid:
                        continue
                    if allowed_rsids is not None and rsid not in allowed_rsids:
                        continue

                    alt = _normalize_allele(row.get("AlternateAlleleVCF") or row.get("AlternateAllele"))
                    ref = _normalize_allele(row.get("ReferenceAlleleVCF") or row.get("ReferenceAllele"))
                    if not alt or not ref:
                        continue

                    index[(rsid, alt)].append(
                        {
                            "gene": _normalize_gene(row.get("GeneSymbol")),
                            "name": row.get("Name") or row.get("VariantName") or "",
                            "clinical_significance": row.get("ClinicalSignificance") or "",
                            "origin": row.get("Origin") or row.get("OriginSimple") or "",
                            "review_status": row.get("ReviewStatus") or "",
                            "ref": ref,
                            "alt": alt,
                        }
                    )
            loaded = True
            if not CLINVAR_LOADED_LOGGED:
                print(f"Loaded ClinVar: {len(index)} allele records from {path}")
                CLINVAR_LOADED_LOGGED = True
            break
        except Exception as exc:
            if not CLINVAR_WARNED:
                print(f"Failed loading ClinVar from {path}: {exc}")

    if not loaded:
        if not CLINVAR_WARNED:
            print(f"ClinVar database not found; tried paths: {CLINVAR_PATHS}")
            CLINVAR_WARNED = True
        CLINVAR_INDEX_CACHE[cache_key] = {}
        return CLINVAR_INDEX_CACHE[cache_key]

    CLINVAR_INDEX_CACHE[cache_key] = dict(index)
    return CLINVAR_INDEX_CACHE[cache_key]


def _finding_type_for_inheritance(inheritance, dosage):
    if dosage is None or dosage <= 0:
        return None

    if inheritance == "autosomal_dominant":
        return "dominant"
    if inheritance == "autosomal_recessive":
        if dosage == 1:
            return "carrier"
        if dosage >= 2:
            return "recessive"
    if inheritance == "pharmacogenomic":
        return "pharmacogenomic"
    return None


def _report_label_for_type(finding_type):
    labels = {
        "dominant": "Dominant finding",
        "carrier": "Carrier finding",
        "recessive": "Recessive finding",
        "pharmacogenomic": "Pharmacogenomic finding",
    }
    return labels.get(finding_type, "Clinical finding")


def interpret_clinvar_findings(genome, clinvar_index=None, variant_catalog=None):
    variant_catalog = variant_catalog if variant_catalog is not None else REPORTABLE_VARIANT_CATALOG
    clinvar_index = clinvar_index if clinvar_index is not None else load_clinvar(set(variant_catalog.keys()))

    findings = []
    suppressed_reasons = defaultdict(int)

    for rsid, variant_rules in variant_catalog.items():
        record = genome.get(rsid)
        genotype = record.get("genotype") if record else None
        if not genotype:
            continue

        alleles = _genotype_alleles(genotype)
        if len(alleles) != 2:
            suppressed_reasons["ambiguous_genotype"] += 1
            continue

        for rule in variant_rules:
            alt = _normalize_allele(rule.get("alt"))
            if not alt:
                suppressed_reasons["unsupported_catalog_allele"] += 1
                continue

            dosage = allele_dosage(genotype, alt)
            if dosage is None:
                suppressed_reasons["ambiguous_genotype"] += 1
                continue
            if dosage == 0:
                continue

            evidence_rows = clinvar_index.get((rsid, alt), [])
            summary = _summarize_clinvar_rows(evidence_rows)
            if not summary.get("is_reportable"):
                suppressed_reasons[summary.get("reason", "suppressed")] += 1
                continue

            finding_type = _finding_type_for_inheritance(rule.get("inheritance"), dosage)
            if not finding_type:
                suppressed_reasons["unsupported_inheritance"] += 1
                continue

            zygosity = classify_zygosity(genotype, alt)
            gene = sorted(summary.get("genes") or {"Unknown"})[0]
            variant_name = sorted(summary.get("names") or {f"{rsid} {alt}"})[0]
            review_status = sorted(summary.get("review_statuses") or {"Unspecified"})[0]

            findings.append(
                {
                    "gene": gene,
                    "rsid": rsid,
                    "variant": variant_name,
                    "genotype": genotype,
                    "matched_allele": alt,
                    "allele_dosage": dosage,
                    "zygosity": zygosity,
                    "clinical_significance": summary["clinical_significance"],
                    "review_status": review_status,
                    "inheritance": rule.get("inheritance"),
                    "finding_type": finding_type,
                    "report_label": _report_label_for_type(finding_type),
                    "source": "ClinVar",
                }
            )

    deduped = {}
    for finding in findings:
        key = (
            finding["gene"],
            finding["rsid"],
            finding["matched_allele"],
            finding["finding_type"],
            finding["zygosity"],
        )
        deduped[key] = finding

    ordered = sorted(
        deduped.values(),
        key=lambda item: (
            {"dominant": 0, "recessive": 1, "carrier": 2, "pharmacogenomic": 3}.get(item["finding_type"], 9),
            item["gene"],
            item["rsid"],
        ),
    )

    return {
        "reportable_findings": ordered,
        "dominant_findings": [item for item in ordered if item["finding_type"] == "dominant"],
        "recessive_findings": [item for item in ordered if item["finding_type"] == "recessive"],
        "carrier_findings": [item for item in ordered if item["finding_type"] == "carrier"],
        "pharmacogenomic_findings": [item for item in ordered if item["finding_type"] == "pharmacogenomic"],
        "suppressed_summary": dict(sorted(suppressed_reasons.items())),
        "default_report_policy": "Pathogenic/Likely pathogenic germline findings only; ambiguous or conflicting evidence suppressed.",
    }


def detect_carrier_status(genome):
    clinical_findings = interpret_clinvar_findings(genome)
    return {
        "clinical_findings": clinical_findings,
        "carriers": clinical_findings["carrier_findings"],
        "dominant_variants": clinical_findings["dominant_findings"],
    }
