# Genome Full App

DNA analysis web app with a Flask backend and Next.js (App Router) frontend. Handles parent DNA uploads, child trait/health predictions, PDF reports, and an optional AI explainer. Heavy genomic datasets and user uploads stay out of git.

## Prerequisites
- Python 3.10+ (for backend)
- Node 18+ (for frontend / Next.js 14)
- Git (and Git LFS if you choose to store large datasets that way)

## Environment
Create a `.env` (or `.env.local`) in the repo root using `.env.example` as a guide:
```
OPENAI_API_KEY=your_openai_api_key
OPENAI_MODEL=gpt-4o-mini
```
The AI explainer feature is optional; without a key, that endpoint will return a 503.

## Backend setup (Flask)
```
cd backend
python -m venv .venv
.\.venv\Scripts\activate   # Windows PowerShell
pip install -r requirements.txt
```

Run the API:
```
cd backend
.\.venv\Scripts\activate
python app.py
```
The server listens on port 5000 by default.

### Reference data (not committed)
Large reference files like `backend/clinvar.gz`, `backend/nih/clinvar.gz`, and `backend/nih/dbsnp.gz` are ignored. Place them under `backend/` as needed. If you must version them, use Git LFS.

### Uploads
User uploads are stored under `backend/upload/` and `backend/uploads/` (ignored by git). Avoid committing personal genome files.

## Frontend setup (Next.js)
```
cd frontend
npm install
npm run dev
```
The dev server runs on port 3000 by default. Ensure the backend (port 5000) is running for API calls.

## Features
- Parent DNA upload → child trait/health prediction (`/parents`, `/child-results`)
- Punnett-style trait visualizations and genotype heatmaps
- PDF report generation
- In-memory results cache: only a small `childResultId` is stored in `sessionStorage`; large payloads stay in memory and are not persisted to browser storage.
- Optional AI summary (`/api/explain-results`) when `OPENAI_API_KEY` is set

## Notes on data and size
- Keep `node_modules`, `.next`, `venv`, uploads, and large genomic datasets out of git (see `.gitignore`).
- If you need to share big reference files, prefer Git LFS or an external download script rather than regular commits.

## Basic workflow
1) Start backend (port 5000).
2) Start frontend (port 3000).
3) Visit the frontend, upload parent DNA files, view child results.
4) Optionally generate a PDF or request an AI explanation.

   
   <img width="431" height="610" alt="image" src="https://github.com/user-attachments/assets/f174cf24-85db-4c90-9165-c690fc3fa22b" />

   <img width="734" height="649" alt="image" src="https://github.com/user-attachments/assets/a4716275-7d71-43c5-aab3-e29ef06e199e" />

   <img width="1109" height="576" alt="image" src="https://github.com/user-attachments/assets/b7ef0a23-ce2f-4b46-a991-84453ec57e15" />

   


## Troubleshooting
- Storage/Quota issues: Large genomes are never stored in browser storage; only small IDs are. Reloading the tab drops in-memory caches—re-upload to regenerate results.
- Push rejected due to large files: ensure large datasets and caches stay ignored; clean history if needed before pushing.
