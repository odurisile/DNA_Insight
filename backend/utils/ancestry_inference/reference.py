import csv
from typing import Dict, List, Tuple


def load_reference_metadata(metadata_tsv: str) -> Tuple[List[Dict], Dict[str, str]]:
    samples = []
    sample_to_cont = {}
    valid_continents = {"AFR", "EUR", "EAS", "SAS", "AMR", "NAT"}
    
    with open(metadata_tsv, "r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter="\t")

        for row in reader:
            sample_id = row.get("Sample name")
            pop = row.get("Population code")
            cont = row.get("Superpopulation code")
            if "," in cont or "/" in cont or ";" in cont:
                continue

            if cont not in valid_continents:
                continue
            if not sample_id or not cont:
                continue

            sample_id = sample_id.strip()
            pop = pop.strip() if pop else "UNK"
            cont = cont.strip().upper()

            samples.append({
                "sample_id": sample_id,
                "population": pop,
                "continent": cont,
            })

            sample_to_cont[sample_id] = cont

    return samples, sample_to_cont