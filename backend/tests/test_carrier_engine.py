import unittest

from utils.carrier_engine import (
    allele_dosage,
    classify_zygosity,
    interpret_clinvar_findings,
)


def _row(gene, significance, origin="germline", name=None, review="criteria provided, multiple submitters, no conflicts"):
    return {
        "gene": gene,
        "clinical_significance": significance,
        "origin": origin,
        "name": name or f"{gene} synthetic variant",
        "review_status": review,
    }


class CarrierEngineTests(unittest.TestCase):
    def test_reference_homozygous_is_never_positive(self):
        genome = {"rsTest1": {"genotype": "C/C"}}
        clinvar_index = {
            ("rsTest1", "A"): [_row("GENE1", "Pathogenic")],
        }
        catalog = {"rsTest1": [{"alt": "A", "inheritance": "autosomal_dominant"}]}

        findings = interpret_clinvar_findings(genome, clinvar_index=clinvar_index, variant_catalog=catalog)

        self.assertEqual(findings["reportable_findings"], [])

    def test_allele_dosage_and_zygosity(self):
        self.assertEqual(allele_dosage("A/G", "A"), 1)
        self.assertEqual(allele_dosage("A/A", "A"), 2)
        self.assertEqual(allele_dosage("G/G", "A"), 0)
        self.assertEqual(classify_zygosity("A/G", "A"), "heterozygous")
        self.assertEqual(classify_zygosity("A/A", "A"), "homozygous_alt")

    def test_recessive_heterozygous_is_carrier_but_homozygous_is_recessive(self):
        clinvar_index = {
            ("rsTest2", "T"): [_row("GENE2", "Pathogenic/Likely pathogenic")],
        }
        catalog = {"rsTest2": [{"alt": "T", "inheritance": "autosomal_recessive"}]}

        heterozygous = interpret_clinvar_findings(
            {"rsTest2": {"genotype": "C/T"}},
            clinvar_index=clinvar_index,
            variant_catalog=catalog,
        )
        homozygous = interpret_clinvar_findings(
            {"rsTest2": {"genotype": "T/T"}},
            clinvar_index=clinvar_index,
            variant_catalog=catalog,
        )

        self.assertEqual(len(heterozygous["carrier_findings"]), 1)
        self.assertEqual(heterozygous["carrier_findings"][0]["finding_type"], "carrier")
        self.assertEqual(homozygous["carrier_findings"], [])
        self.assertEqual(len(homozygous["recessive_findings"]), 1)
        self.assertEqual(homozygous["recessive_findings"][0]["finding_type"], "recessive")

    def test_benign_and_vus_are_suppressed_from_default_report(self):
        genome = {
            "rsBenign": {"genotype": "A/G"},
            "rsVus": {"genotype": "C/T"},
        }
        clinvar_index = {
            ("rsBenign", "A"): [_row("GENE3", "Likely benign")],
            ("rsVus", "T"): [_row("GENE4", "Uncertain significance")],
        }
        catalog = {
            "rsBenign": [{"alt": "A", "inheritance": "autosomal_dominant"}],
            "rsVus": [{"alt": "T", "inheritance": "autosomal_recessive"}],
        }

        findings = interpret_clinvar_findings(genome, clinvar_index=clinvar_index, variant_catalog=catalog)

        self.assertEqual(findings["reportable_findings"], [])
        self.assertGreaterEqual(findings["suppressed_summary"].get("non_reportable_significance", 0), 2)

    def test_conflicting_interpretations_fail_closed(self):
        genome = {"rsConflict": {"genotype": "A/G"}}
        clinvar_index = {
            ("rsConflict", "A"): [_row("GENE5", "Conflicting classifications of pathogenicity")],
        }
        catalog = {"rsConflict": [{"alt": "A", "inheritance": "autosomal_dominant"}]}

        findings = interpret_clinvar_findings(genome, clinvar_index=clinvar_index, variant_catalog=catalog)

        self.assertEqual(findings["reportable_findings"], [])
        self.assertEqual(findings["suppressed_summary"].get("non_reportable_significance"), 1)

    def test_inheritance_logic_runs_only_after_allele_match(self):
        genome = {"rsDom": {"genotype": "G/G"}}
        clinvar_index = {
            ("rsDom", "A"): [_row("GENE6", "Pathogenic")],
        }
        catalog = {"rsDom": [{"alt": "A", "inheritance": "autosomal_dominant"}]}

        findings = interpret_clinvar_findings(genome, clinvar_index=clinvar_index, variant_catalog=catalog)

        self.assertEqual(findings["dominant_findings"], [])

    def test_redundant_rows_collapse_to_one_finding(self):
        genome = {"rsDedup": {"genotype": "A/G"}}
        clinvar_index = {
            ("rsDedup", "A"): [
                _row("GENE7", "Pathogenic", name="GENE7 variant"),
                _row("GENE7", "Pathogenic", name="GENE7 variant"),
            ],
        }
        catalog = {"rsDedup": [{"alt": "A", "inheritance": "autosomal_dominant"}]}

        findings = interpret_clinvar_findings(genome, clinvar_index=clinvar_index, variant_catalog=catalog)

        self.assertEqual(len(findings["reportable_findings"]), 1)

    def test_pharmacogenomic_findings_are_labeled_separately(self):
        genome = {"rsPgx": {"genotype": "A/G"}}
        clinvar_index = {
            ("rsPgx", "A"): [_row("GENE8", "Pathogenic")],
        }
        catalog = {"rsPgx": [{"alt": "A", "inheritance": "pharmacogenomic"}]}

        findings = interpret_clinvar_findings(genome, clinvar_index=clinvar_index, variant_catalog=catalog)

        self.assertEqual(len(findings["pharmacogenomic_findings"]), 1)
        self.assertEqual(findings["pharmacogenomic_findings"][0]["report_label"], "Pharmacogenomic finding")


if __name__ == "__main__":
    unittest.main()
