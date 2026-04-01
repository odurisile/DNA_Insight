import sqlite3
import csv
import re

TSV_FILE = "gwas.tsv"
DB_FILE = "gwas_50k.db"
TABLE_NAME = "gwas_catalog_raw"


def normalize_column_name(name: str) -> str:
    """
    Convert GWAS Catalog headers into SQL-safe snake_case column names.
    """
    name = name.strip().lower()
    name = re.sub(r"[^a-z0-9]+", "_", name)
    name = re.sub(r"_+", "_", name).strip("_")
    if not name:
        name = "unnamed_column"
    if name[0].isdigit():
        name = f"col_{name}"
    return name


def get_headers_and_mapping():
    """
    Read the TSV headers and return:
    - original headers
    - normalized SQL column names
    """
    with open(TSV_FILE, "r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f, delimiter="\t")
        headers = reader.fieldnames

    if not headers:
        raise ValueError("No headers found in TSV file.")

    normalized = []
    seen = {}

    for header in headers:
        col = normalize_column_name(header)
        if col in seen:
            seen[col] += 1
            col = f"{col}_{seen[col]}"
        else:
            seen[col] = 0
        normalized.append(col)

    return headers, normalized


def create_database():
    headers, normalized_columns = get_headers_and_mapping()

    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()

    cur.execute(f'DROP TABLE IF EXISTS {TABLE_NAME}')

    column_defs = ",\n        ".join([f'"{col}" TEXT' for col in normalized_columns])

    cur.execute(f"""
    CREATE TABLE {TABLE_NAME} (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        {column_defs}
    )
    """)

    conn.commit()
    conn.close()

    print(f"Created table: {TABLE_NAME}")
    print("Column mapping:")
    for original, normalized in zip(headers, normalized_columns):
        print(f"  {original}  ->  {normalized}")


def import_tsv():
    headers, normalized_columns = get_headers_and_mapping()

    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()

    quoted_cols = ", ".join([f'"{col}"' for col in normalized_columns])
    placeholders = ", ".join(["?"] * len(normalized_columns))

    insert_sql = f"""
    INSERT INTO {TABLE_NAME} ({quoted_cols})
    VALUES ({placeholders})
    """

    batch = []
    batch_size = 1000
    total_rows = 0

    with open(TSV_FILE, "r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f, delimiter="\t")

        for row in reader:
            values = [row.get(header) for header in headers]
            batch.append(values)

            if len(batch) >= batch_size:
                cur.executemany(insert_sql, batch)
                conn.commit()
                total_rows += len(batch)
                print(f"Imported {total_rows} rows...")
                batch = []

        if batch:
            cur.executemany(insert_sql, batch)
            conn.commit()
            total_rows += len(batch)

    conn.close()
    print(f"Finished import. Total rows imported: {total_rows}")


def test_query():
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()

    cur.execute(f"SELECT COUNT(*) FROM {TABLE_NAME}")
    print("Row count:", cur.fetchone()[0])

    cur.execute(f"SELECT * FROM {TABLE_NAME} LIMIT 3")
    rows = cur.fetchall()

    print("\nSample rows:")
    for row in rows:
        print(row)

    conn.close()


if __name__ == "__main__":
    create_database()
    import_tsv()
    test_query()