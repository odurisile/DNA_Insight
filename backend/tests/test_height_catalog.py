import json
import os
import tempfile
import unittest

from utils.height_catalog.ingest import build_height_catalog


class HeightCatalogTests(unittest.TestCase):
    def test_catalog_ingest_filters_ambiguous(self):
        fixture = os.path.join(os.path.dirname(__file__), "fixtures", "height_gwas_small.tsv")
        with tempfile.TemporaryDirectory() as tmp:
            config_path = os.path.join(tmp, "config.json")
            output_tsv = os.path.join(tmp, "catalog.tsv")
            output_report = os.path.join(tmp, "report.json")
            config = {
                "sources": [
                    {
                        "name": "TEST",
                        "path": fixture,
                        "ancestry": "EUR",
                        "delimiter": "\t",
                        "columns": {
                            "rsid": "rsid",
                            "chr": "chr",
                            "pos": "pos",
                            "effect_allele": "effect_allele",
                            "other_allele": "other_allele",
                            "beta": "beta",
                            "eaf": "eaf",
                            "gene": "nearest_gene",
                            "imputation": "info"
                        }
                    }
                ],
                "canonical_snps": {},
                "gene_pathways": {}
            }
            with open(config_path, "w", encoding="utf-8") as f:
                json.dump(config, f)

            build_height_catalog(config_path, output_tsv, output_report)

            with open(output_report, "r", encoding="utf-8") as f:
                report = json.load(f)

            self.assertEqual(report["total_snps"], 1)


if __name__ == "__main__":
    unittest.main()
