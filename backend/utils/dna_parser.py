import os
import gzip
import zipfile
import csv

SUPPORTED_FORMATS = ["23andme", "ancestry", "myheritage", "ftdna"]

def detect_format(header_line: str):
    """Detects which company format the file uses."""
    line = header_line.lower()

    if "23andme" in line:
        return "23andme"
    if "ancestry" in line or "ancestrydna" in line:
        return "ancestry"
    if "myheritage" in line:
        return "myheritage"
    if "ftdna" in line or "family tree dna" in line:
        return "ftdna"

    # Try fallback based on structure
    cols = header_line.split()
    if len(cols) >= 4 and cols[0].lower() in ("rsid", "snp"):
        return "generic"

    return "unknown"


def open_file_auto(path):
    """Opens normal, gzipped, or zipped DNA files."""
    if path.endswith(".zip"):
        with zipfile.ZipFile(path, "r") as z:
            # Try to find the DNA file inside the ZIP
            for name in z.namelist():
                if name.endswith(".txt") or name.endswith(".csv"):
                    return z.open(name), name
            raise ValueError("ZIP does not contain a DNA text file.")

    if path.endswith(".gz"):
        return gzip.open(path, "rt"), path

    return open(path, "r", errors="ignore"), path


def normalize_genotype(g):
    """Convert genotypes like 'AA', 'A A', 'A|G' → 'A/G'."""
    if g is None:
        return None

    g = g.replace(" ", "").replace("|", "/").replace("\\", "/")

    # Insert slash if missing: "AG" → "A/G"
    if len(g) == 2 and "/" not in g:
        return f"{g[0]}/{g[1]}"

    return g.upper()


def parse_row(format_type, row):
    """Parses a row according to detected file format."""
    try:
        if format_type == "23andme":
            rsid = row[0]
            chrom = row[1]
            pos = int(row[2])
            genotype = normalize_genotype(row[3])
            return rsid, chrom, pos, genotype

        if format_type == "ancestry":
            rsid = row[0]
            chrom = row[1]
            pos = int(row[2])
            genotype = normalize_genotype(row[3])
            return rsid, chrom, pos, genotype

        if format_type == "myheritage":
            # MyHeritage sometimes uses 5 columns
            rsid = row[0]
            chrom = row[1]
            pos = int(row[2])
            genotype = normalize_genotype(row[3])
            return rsid, chrom, pos, genotype

        if format_type == "ftdna":
            rsid = row[0]
            chrom = row[1]
            pos = int(row[2])
            genotype = normalize_genotype(row[3])
            return rsid, chrom, pos, genotype

        # Generic fallback
        rsid = row[0]
        chrom = row[1]
        pos = int(row[2])
        genotype = normalize_genotype(row[3])
        return rsid, chrom, pos, genotype

    except Exception:
        return None


def parse_raw_dna_file(path: str):
    """
    Main entry: parses ANY DNA file into a unified dictionary.

    Returns:
    {
        "rs123": { "genotype": "A/G", "chrom": "7", "pos": 117199644 }
        ...
    }
    """
    snp_data = {}

    reader, name = open_file_auto(path)
    first_line = reader.readline()
    format_type = detect_format(first_line)

    # Skip comment lines starting with '#'
    while first_line.startswith("#"):
        first_line = reader.readline()

    # Now read with CSV parser
    reader = csv.reader(
        [first_line] + list(reader),
        delimiter="\t" if "\t" in first_line else ","
    )

    for row in reader:
        if not row or row[0].startswith("#"):
            continue
        parsed = parse_row(format_type, row)
        if parsed:
            rsid, chrom, pos, genotype = parsed
            if rsid and genotype:
                snp_data[rsid] = {
                    "genotype": genotype,
                    "chrom": chrom,
                    "pos": pos,
                }

    return snp_data
