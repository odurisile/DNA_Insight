import csv
from typing import Dict, List, Tuple


def load_reference_metadata(metadata_tsv: str, population_map: Dict[str, str]) -> Tuple[List[Dict], Dict[str, str]]:
    samples = []
    pop_to_cont = {}
    for pop, cont in population_map.items():
        pop_to_cont[pop] = cont
    with open(metadata_tsv, "r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter="\t")
        for row in reader:
            pop = row.get("population") or row.get("pop")
            if not pop:
                continue
            cont = pop_to_cont.get(pop, "UNK")
            samples.append(
                {
                    "sample_id": row.get("sample_id") or row.get("sample") or row.get("iid"),
                    "population": pop,
                    "continent": cont,
                }
            )
    return samples, pop_to_cont
