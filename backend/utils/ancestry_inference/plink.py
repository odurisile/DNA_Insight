import subprocess
from typing import List, Optional


def run_command(cmd: List[str], workdir: Optional[str] = None) -> str:
    result = subprocess.run(cmd, cwd=workdir, capture_output=True, text=True, check=False)
    if result.returncode != 0:
        raise RuntimeError(f"Command failed: {' '.join(cmd)}\n{result.stderr}")
    return result.stdout


def build_plink_convert_command(plink2: str, input_path: str, out_prefix: str) -> List[str]:
    if input_path.lower().endswith(".vcf") or input_path.lower().endswith(".vcf.gz"):
        return [plink2, "--vcf", input_path, "--make-bed", "--out", out_prefix]
    return [plink2, "--23file", input_path, "--make-bed", "--out", out_prefix]


def build_plink_qc_command(
    plink2: str,
    bfile_prefix: str,
    out_prefix: str,
    max_missing: float,
    min_maf: float,
) -> List[str]:
    return [
        plink2,
        "--bfile",
        bfile_prefix,
        "--geno",
        str(max_missing),
        "--maf",
        str(min_maf),
        "--make-bed",
        "--out",
        out_prefix,
    ]


def build_plink_ld_prune_command(
    plink2: str,
    bfile_prefix: str,
    out_prefix: str,
    window_kb: int,
    step: int,
    r2: float,
) -> List[str]:
    return [
        plink2,
        "--bfile",
        bfile_prefix,
        "--indep-pairwise",
        str(window_kb),
        str(step),
        str(r2),
        "--out",
        out_prefix,
    ]


def build_plink_extract_command(plink2: str, bfile_prefix: str, extract_path: str, out_prefix: str) -> List[str]:
    return [
        plink2,
        "--bfile",
        bfile_prefix,
        "--extract",
        extract_path,
        "--make-bed",
        "--out",
        out_prefix,
    ]


def build_plink_merge_command(
    plink2: str,
    bfile_prefix: str,
    merge_prefix: str,
    out_prefix: str,
) -> List[str]:
    return [
        plink2,
        "--bfile",
        bfile_prefix,
        "--bmerge",
        merge_prefix,
        "--make-bed",
        "--out",
        out_prefix,
    ]


def build_plink_pca_command(plink2: str, bfile_prefix: str, out_prefix: str, pcs: int) -> List[str]:
    return [
        plink2,
        "--bfile",
        bfile_prefix,
        "--pca",
        str(pcs),
        "--out",
        out_prefix,
    ]
