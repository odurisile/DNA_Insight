import argparse
import csv
import json
import os
from typing import Dict, List, Optional, Tuple

AMBIGUOUS_PAIRS = {frozenset({"A", "T"}), frozenset({"C", "G"})}


def is_ambiguous(effect: str, other: str) -> bool:
    return frozenset({effect, other}) in AMBIGUOUS_PAIRS


def _parse_float(value: Optional[str]) -> Optional[float]:
    if value is None or value == "":
        return None
    try:
        return float(value)
    except Exception:
        return None


def _load_config(path: str) -> Dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _read_table(path: str, delimiter: Optional[str] = None) -> List[Dict[str, str]]:
    if delimiter is None:
        delimiter = "\t" if path.endswith(".tsv") else ","
    rows = []
    with open(path, "r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter=delimiter)
        for row in reader:
            rows.append(row)
    return rows


def _apply_quality_filters(effect: str, other: str, eaf: Optional[float]) -> bool:
    if not effect or not other:
        return False
    effect = effect.upper()
    other = other.upper()
    if is_ambiguous(effect, other):
        if eaf is None or (0.42 <= eaf <= 0.58):
            return False
    return True


def _merge_record(
    catalog: Dict[str, Dict],
    record: Dict,
    ancestry: str,
    source: str,
):
    rsid = record["rsid"]
    if rsid not in catalog:
        catalog[rsid] = {
            "rsid": rsid,
            "chr": record.get("chr"),
            "pos": record.get("pos"),
            "effect_allele": record.get("effect_allele"),
            "other_allele": record.get("other_allele"),
            "gene": record.get("gene"),
            "pathway": record.get("pathway"),
            "betas": {},
            "sources": set(),
            "eaf": {},
            "imputation": {},
        }
    entry = catalog[rsid]
    if entry.get("effect_allele") and record.get("effect_allele") != entry.get("effect_allele"):
        return
    if entry.get("other_allele") and record.get("other_allele") != entry.get("other_allele"):
        return
    entry["betas"][ancestry] = record.get("beta")
    if record.get("eaf") is not None:
        entry["eaf"][ancestry] = record.get("eaf")
    if record.get("imputation") is not None:
        entry["imputation"][ancestry] = record.get("imputation")
    entry["sources"].add(source)
    if not entry.get("gene") and record.get("gene"):
        entry["gene"] = record.get("gene")
    if not entry.get("pathway") and record.get("pathway"):
        entry["pathway"] = record.get("pathway")


def build_height_catalog(
    config_path: str,
    output_tsv: str,
    output_report: str,
    output_parquet: Optional[str] = None,
    ld_prune: bool = False,
):
    config = _load_config(config_path)
    catalog: Dict[str, Dict] = {}

    gene_pathways = config.get("gene_pathways", {})
    canonical_snps = config.get("canonical_snps", {})

    for source in config.get("sources", []):
        path = source["path"]
        ancestry = source["ancestry"]
        mapping = source.get("columns", {})
        delimiter = source.get("delimiter")
        rows = _read_table(path, delimiter)
        for row in rows:
            rsid = row.get(mapping.get("rsid", "rsid"))
            if not rsid:
                continue
            effect = (row.get(mapping.get("effect_allele", "effect_allele")) or "").upper()
            other = (row.get(mapping.get("other_allele", "other_allele")) or "").upper()
            eaf = _parse_float(row.get(mapping.get("eaf", "eaf")))
            if not _apply_quality_filters(effect, other, eaf):
                continue
            beta = _parse_float(row.get(mapping.get("beta", "beta")))
            if beta is None:
                continue
            gene = row.get(mapping.get("gene", "nearest_gene"))
            pathway = gene_pathways.get(gene) if gene else None
            record = {
                "rsid": rsid,
                "chr": row.get(mapping.get("chr", "chr")),
                "pos": row.get(mapping.get("pos", "pos")),
                "effect_allele": effect,
                "other_allele": other,
                "beta": beta,
                "eaf": eaf,
                "imputation": _parse_float(row.get(mapping.get("imputation", "info"))),
                "gene": gene,
                "pathway": pathway,
            }
            _merge_record(catalog, record, ancestry=ancestry, source=source.get("name", path))

    for rsid, meta in canonical_snps.items():
        if rsid not in catalog:
            catalog[rsid] = {
                "rsid": rsid,
                "chr": meta.get("chr"),
                "pos": meta.get("pos"),
                "effect_allele": meta.get("effect_allele"),
                "other_allele": meta.get("other_allele"),
                "gene": meta.get("gene"),
                "pathway": gene_pathways.get(meta.get("gene")),
                "betas": {},
                "sources": {"canonical"},
                "eaf": {},
            }
        else:
            catalog[rsid]["sources"].add("canonical")

    os.makedirs(os.path.dirname(output_tsv), exist_ok=True)
    fieldnames = [
        "rsid",
        "chr",
        "pos",
        "effect_allele",
        "other_allele",
        "gene",
        "pathway",
        "beta_AFR",
        "beta_EUR",
        "beta_EAS",
        "beta_SAS",
        "beta_NAT",
        "beta_AMR",
        "imputation_AFR",
        "imputation_EUR",
        "imputation_EAS",
        "imputation_SAS",
        "imputation_NAT",
        "imputation_AMR",
        "sources",
    ]

    ancestry_counts = {"AFR": 0, "EUR": 0, "EAS": 0, "SAS": 0, "NAT": 0, "AMR": 0}
    with open(output_tsv, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter="\t")
        writer.writeheader()
        for record in catalog.values():
            betas = record.get("betas", {})
            for ancestry in ancestry_counts:
                if ancestry in betas:
                    ancestry_counts[ancestry] += 1
            writer.writerow(
                {
                    "rsid": record.get("rsid"),
                    "chr": record.get("chr"),
                    "pos": record.get("pos"),
                    "effect_allele": record.get("effect_allele"),
                    "other_allele": record.get("other_allele"),
                    "gene": record.get("gene"),
                    "pathway": record.get("pathway"),
                    "beta_AFR": betas.get("AFR"),
                    "beta_EUR": betas.get("EUR"),
                    "beta_EAS": betas.get("EAS"),
                    "beta_SAS": betas.get("SAS"),
                    "beta_NAT": betas.get("NAT"),
                    "beta_AMR": betas.get("AMR"),
                    "imputation_AFR": record.get("imputation", {}).get("AFR"),
                    "imputation_EUR": record.get("imputation", {}).get("EUR"),
                    "imputation_EAS": record.get("imputation", {}).get("EAS"),
                    "imputation_SAS": record.get("imputation", {}).get("SAS"),
                    "imputation_NAT": record.get("imputation", {}).get("NAT"),
                    "imputation_AMR": record.get("imputation", {}).get("AMR"),
                    "sources": ",".join(sorted(record.get("sources", []))),
                }
            )

    if output_parquet:
        try:
            import pandas as pd  # type: ignore
        except Exception:
            pd = None
        if pd is not None:
            df = pd.read_csv(output_tsv, sep="\t")
            df.to_parquet(output_parquet, index=False)

    total = len(catalog)
    afr_beta = ancestry_counts["AFR"]
    report = {
        "total_snps": total,
        "ancestry_coverage": ancestry_counts,
        "percent_african_beta": (afr_beta / total * 100) if total else 0,
        "canonical_snps": len(canonical_snps),
        "ld_prune_requested": ld_prune,
    }
    with open(output_report, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)


def main():
    parser = argparse.ArgumentParser(description="Build unified height SNP catalog.")
    parser.add_argument("--config", required=True, help="Catalog config JSON.")
    parser.add_argument("--output-tsv", required=True, help="Output TSV path.")
    parser.add_argument("--output-report", required=True, help="Output report JSON.")
    parser.add_argument("--output-parquet", help="Output parquet path.")
    parser.add_argument("--ld-prune", action="store_true", help="Placeholder flag; requires LD reference.")
    args = parser.parse_args()

    build_height_catalog(
        config_path=args.config,
        output_tsv=args.output_tsv,
        output_report=args.output_report,
        output_parquet=args.output_parquet,
        ld_prune=args.ld_prune,
    )


if __name__ == "__main__":
    main()
