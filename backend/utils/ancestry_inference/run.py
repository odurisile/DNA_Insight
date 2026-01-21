import argparse
import json
import os

from .pipeline import infer_global_ancestry_from_file


def main():
    parser = argparse.ArgumentParser(description="Run ancestry inference pipeline.")
    parser.add_argument("--input", required=True, help="Raw genotype file (VCF/23andMe/AncestryDNA).")
    parser.add_argument("--output-dir", required=True, help="Output directory.")
    parser.add_argument("--config", required=True, help="Config YAML/JSON.")
    parser.add_argument("--method", help="Override method (admixture_pca/pca).")
    args = parser.parse_args()

    os.makedirs(args.output_dir, exist_ok=True)
    result = infer_global_ancestry_from_file(
        raw_path=args.input,
        output_dir=args.output_dir,
        config_path=args.config,
        method=args.method,
    )
    with open(os.path.join(args.output_dir, "ancestry_result.json"), "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
