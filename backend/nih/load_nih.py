import duckdb
import polars as pl

DB_PATH = "nih.duckdb"

print("Loading datasets...")

print("Loading GWAS 50k...")
gwas = pl.read_csv("gwas_50k.csv")

print("Loading dbSNP-lite...")
dbsnp = pl.read_csv("dbsnp_lite.csv")

# Create a unified dataset
merged = (
    gwas.join(dbsnp, on="rsid", how="outer")
)

print(f"Total merged rows: {merged.height}")

con = duckdb.connect(DB_PATH, read_only=False)
con.execute("DROP TABLE IF EXISTS nih_data")
con.execute("CREATE TABLE nih_data AS SELECT * FROM merged")
con.execute("CREATE INDEX IF NOT EXISTS idx_rsid ON nih_data(rsid)")
con.close()

print("Lite NIH DB built successfully → nih.duckdb")
