# Genome Full App

Designed and built a full-stack genomics analysis platform that ingests raw consumer DNA files from providers such as 23andMe and AncestryDNA, normalizes genotype data, and runs a series of predictive analytics pipelines across traits, health risk, ancestry, and polygenic scoring. The application used a Flask backend to orchestrate file upload, parsing, inference, and report generation workflows, and a Next.js frontend to deliver interactive visualizations, parent/child comparison tools, and downloadable reports. At the core of the platform, I implemented machine learning and statistical genetics components that transformed sparse SNP-level genotype data into higher-level phenotype predictions. This included ancestry inference using PCA-derived features and a scikit-learn logistic regression classifier, trait prediction modules built on logistic-regression-style SNP effect models, and a height polygenic score pipeline that computed ancestry-aware weighted SNP contributions, calibrated raw scores into interpretable height estimates, and returned confidence intervals, percentile rankings, coverage metrics, and bias warnings.

A major part of the project was the ML pipeline design and model engineering. I built training and inference code for ancestry and height prediction workflows using scikit-learn, including logistic regression for ancestry classification and linear, ridge, and isotonic regression options for height calibration. The height system combined raw polygenic score generation with post-model calibration that incorporated sex, global ancestry proportions, and ancestry-specific component scores to improve prediction quality on admixed populations. I also implemented supporting evaluation utilities such as R², MAE, and ancestry-stratified error analysis to measure performance across demographic groups, and added confidence interval logic, drift detection, and bias flags to surface when model behavior might be less reliable. Beyond the trained ML models, I integrated deterministic genetics logic for rule-based risk classification and genotype interpretation, allowing the system to blend traditional statistical genetics methods with more formal model-based inference in a single production workflow.

The project also required designing and implementing a SQL-backed genomic data layer to support efficient large-scale SNP and trait lookups. I built import and transformation scripts around SQLite to ingest GWAS and trait association data, normalize column names, create cleaned tables, and support fast query-time retrieval of effect alleles, betas, and phenotype associations. For analytical workloads and larger NIH-derived reference datasets, I also incorporated DuckDB as a lightweight embedded analytical database, using it to materialize tabular genomic datasets into a queryable local store for downstream matching and exploration. This database layer allowed the application to move beyond flat-file processing by enabling indexed, structured storage of SNP metadata, effect-size catalogs, and reference records that could be queried efficiently during scoring and inference. In practice, that meant the app could combine uploaded genotype data with SQL-managed reference data to drive PRS calculations, trait matching, and health-risk interpretation without requiring a separate external database server.

End to end, the system functioned as a production-style ML application rather than a simple research prototype. It exposed REST endpoints for single-user genomic analysis, two-parent child prediction, ancestry-aware height scoring, and PDF report generation; handled large DNA uploads; integrated multiple reference datasets such as GWAS and ClinVar-style variant resources; and produced outputs that were both technically rich and user-facing. The result was a genomics web app that joined machine learning, statistical genetics, SQL data engineering, and full-stack application development into one cohesive platform.

## Prerequisites
- Python 3.10+ (backend)
- Node 18+ (frontend / Next.js 14)
- Git (Git LFS if you choose to store large datasets)

## Environment
Create a `.env` (or `.env.local`) in the repo root using `.env.example`:
```
OPENAI_API_KEY=your_openai_api_key
OPENAI_MODEL=gpt-4o-mini
```
The AI explainer is optional; without a key, that endpoint returns 503.

## Backend setup (Flask)
```
cd backend
python -m venv .venv
.\.venv\Scripts\activate   # Windows PowerShell
pip install -r requirements.txt
python app.py
```
The server listens on port 5000.

### Reference data (not committed)
Large files like `backend/clinvar.gz`, `backend/nih/clinvar.gz`, and `backend/nih/dbsnp.gz` are ignored. Place them under `backend/` locally or use Git LFS if needed.

### Uploads
User uploads live under `backend/upload/` and `backend/uploads/` (ignored by git).

## Frontend setup (Next.js)
```
cd frontend
npm install
npm run dev
```
Dev server runs on port 3000. Ensure the backend (port 5000) is running for API calls.

## Features
- Parent DNA upload + child trait/health prediction (`/parents`, `/child-results`)
- Punnett-style visualizations and genotype heatmaps
- PDF report generation
- In-memory results cache: only a small `childResultId` is stored in `sessionStorage`; large payloads stay in memory
- Optional AI summary (`/api/explain-results`) when `OPENAI_API_KEY` is set
- Height Polygenic Score demo (`/height_pgs` backend, `/height` frontend)

## Basic workflow
1) Start backend (port 5000).
2) Start frontend (port 3000).
3) Upload parent DNA files; view child results.
4) Optionally generate a PDF or request an AI explanation.
5) For height PGS, open `/height`, upload a single raw DNA file, and view the bell-curve card.

## Height PGS
- Backend endpoint: `POST /height_pgs` with form-data `file`, optional `sex` (male/female/unspecified), and optional `global_ancestry` JSON (e.g. `{"AFR":0.6,"EUR":0.4}`).
- Demo weights: `backend/nih/height_demo_weights.csv` (swap with real weights as needed; supports `beta_afr`, `beta_eur`, etc columns).
- Output: raw/z scores, percentile, predicted height with CI90/CI95, coverage, confidence tier, warnings, ancestry breakdown, and ancestry component scores.
- Frontend page: `/height` with upload + sex/ancestry inputs and visualization.
- If `global_ancestry` is omitted, the backend attempts to infer it from an AIMs panel at `backend/nih/height_ancestry_aims.csv` (populate with reference frequencies).

## Height Calibration Engine
- Configurable calibration lives in `backend/utils/height_calibration/config.yaml`.
- Training: `python -m utils.height_calibration.train --input data/train.csv --config backend/utils/height_calibration/config.yaml --output-model data/height_calibration.joblib --output-metrics data/height_calibration_metrics.json`.
- Inference: `python -m utils.height_calibration.infer --config backend/utils/height_calibration/config.yaml --input-json data/sample_input.json`.

## Height SNP Catalog
- Build unified catalog: `python -m utils.height_catalog.ingest --config backend/utils/height_catalog/config.json --output-tsv data/height_catalog.tsv --output-report data/height_catalog_report.json`.
- Configure GWAS inputs by populating `sources` in `backend/utils/height_catalog/config.json` (GIANT, UKBB, PAGE, MVP, H3Africa, GWAS Catalog).

   
   <img width="431" height="610" alt="image" src="https://github.com/user-attachments/assets/f174cf24-85db-4c90-9165-c690fc3fa22b" />

   <img width="734" height="649" alt="image" src="https://github.com/user-attachments/assets/a4716275-7d71-43c5-aab3-e29ef06e199e" />

   <img width="1109" height="576" alt="image" src="https://github.com/user-attachments/assets/b7ef0a23-ce2f-4b46-a991-84453ec57e15" />

   


## Troubleshooting
- Storage/Quota: Large genomes are never stored in browser storage; only small IDs are. Reloading drops in-memory caches—re-upload to regenerate results.
- Push rejected for large files: keep datasets/caches out of git; use LFS or download scripts if needed.
