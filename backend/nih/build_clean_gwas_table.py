import sqlite3
import math

DB_FILE = "gwas_50k.db"
RAW_TABLE = "gwas_catalog_raw"
CLEAN_TABLE = "gwas_snps"


def extract_effect_allele(raw_value: str):
    """
    Examples:
    - 'rs7506045-T' -> 'T'
    - 'rs9536591-C' -> 'C'
    - '?'
    - None
    """
    if not raw_value:
        return None

    raw_value = raw_value.strip()
    if "-" not in raw_value:
        return None

    allele = raw_value.split("-")[-1].strip().upper()

    if allele in {"A", "C", "G", "T"}:
        return allele

    return None


def parse_rsid(value):
    """
    Convert SNP_ID_CURRENT into rsid format.
    GWAS raw data often stores this as numeric text like '7506045',
    so we turn it into 'rs7506045'.
    """
    if value is None:
        return None

    value = str(value).strip()
    if not value:
        return None

    if value.lower().startswith("rs"):
        return value.lower()

    if value.isdigit():
        return f"rs{value}"

    return None


def parse_float(value):
    if value is None:
        return None
    value = str(value).strip()
    if value in {"", "NA", "NR"}:
        return None
    try:
        return float(value)
    except ValueError:
        return None


def normalize_beta(or_or_beta_value: float):
    """
    Heuristic:
    - If > 1, treat as odds ratio and convert with log()
    - Else, treat as beta already
    """
    if or_or_beta_value is None:
        return None

    if or_or_beta_value > 1:
        return math.log(or_or_beta_value)

    return or_or_beta_value


def create_clean_table(conn):
    cur = conn.cursor()

    cur.execute(f"DROP TABLE IF EXISTS {CLEAN_TABLE}")

    cur.execute(f"""
    CREATE TABLE {CLEAN_TABLE} (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        rsid TEXT NOT NULL,
        trait TEXT NOT NULL,
        effect_allele TEXT NOT NULL,
        beta REAL NOT NULL,
        p_value REAL,
        raw_or_beta REAL,
        raw_strongest_snp_risk_allele TEXT,
        UNIQUE(rsid, trait, effect_allele)
    )
    """)

    cur.execute(f"CREATE INDEX IF NOT EXISTS idx_{CLEAN_TABLE}_rsid ON {CLEAN_TABLE}(rsid)")
    cur.execute(f"CREATE INDEX IF NOT EXISTS idx_{CLEAN_TABLE}_trait ON {CLEAN_TABLE}(trait)")
    conn.commit()


def build_clean_table():
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()

    create_clean_table(conn)

    cur.execute(f"""
        SELECT
            snp_id_current,
            disease_trait,
            strongest_snp_risk_allele,
            or_or_beta,
            p_value
        FROM {RAW_TABLE}
    """)

    batch = []
    batch_size = 1000
    inserted = 0
    skipped = 0

    insert_sql = f"""
        INSERT OR IGNORE INTO {CLEAN_TABLE}
        (
            rsid,
            trait,
            effect_allele,
            beta,
            p_value,
            raw_or_beta,
            raw_strongest_snp_risk_allele
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """

    for snp_id_current, disease_trait, strongest_snp_risk_allele, or_or_beta, p_value in cur.fetchall():
        rsid = parse_rsid(snp_id_current)
        trait = disease_trait.strip().lower() if disease_trait else None
        effect_allele = extract_effect_allele(strongest_snp_risk_allele)
        effect_value = parse_float(or_or_beta)
        p_val = parse_float(p_value)

        if not rsid or not trait or not effect_allele or effect_value is None:
            skipped += 1
            continue

        if p_val is None or p_val >= 5e-8:
            skipped += 1
            continue

        beta = normalize_beta(effect_value)

        if beta is None:
            skipped += 1
            continue

        batch.append((
            rsid,
            trait,
            effect_allele,
            beta,
            p_val,
            effect_value,
            strongest_snp_risk_allele
        ))

        if len(batch) >= batch_size:
            cur.executemany(insert_sql, batch)
            conn.commit()
            inserted += len(batch)
            print(f"Inserted {inserted} cleaned rows...")
            batch = []

    if batch:
        cur.executemany(insert_sql, batch)
        conn.commit()
        inserted += len(batch)

    print(f"Finished building {CLEAN_TABLE}.")
    print(f"Inserted: {inserted}")
    print(f"Skipped: {skipped}")

    cur.execute(f"SELECT COUNT(*) FROM {CLEAN_TABLE}")
    print("Final clean row count:", cur.fetchone()[0])

    cur.execute(f"""
        SELECT rsid, trait, effect_allele, beta, p_value
        FROM {CLEAN_TABLE}
        LIMIT 10
    """)
    print("\nSample cleaned rows:")
    for row in cur.fetchall():
        print(row)

    conn.close()


if __name__ == "__main__":
    build_clean_table()