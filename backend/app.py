import json
import os
from pathlib import Path
from uuid import uuid4
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from werkzeug.exceptions import RequestEntityTooLarge
from werkzeug.utils import secure_filename
from utils import risk_engine, trait_engine
from utils.dna_parser import parse_raw_dna_file
from utils.trait_engine import predict_traits
from utils.risk_engine import compute_health_risk
from utils.child_predictor import predict_child
from utils.pdf_engine import generate_pdf_report
from utils.genotype_panel import extract_genotype_panel
from utils.height_pgs import compute_height_pgs
from utils.gene_lookup import search_supported_genes
from utils.ancestry_inference import infer_global_ancestry_from_file
from utils.prs_engine import compute_all_trait_prs

app = Flask(__name__)
CSRF_COOKIE_SECURE = True

allowed_origins = [
    origin.strip()
    for origin in os.environ.get("CORS_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000").split(",")
    if origin.strip()
]
CORS(
    app,
    resources={
        r"/upload_*": {"origins": allowed_origins},
        r"/generate_pdf": {"origins": allowed_origins},
        r"/gene_lookup": {"origins": allowed_origins},
        r"/gwas_traits": {"origins": allowed_origins},
        r"/height_pgs": {"origins": allowed_origins},
        r"/status": {"origins": allowed_origins},
        r"/": {"origins": allowed_origins},
    },
)

# Key SNPs to surface for Punnett-style views
EYE_SNPS = ["rs12913832", "rs1129038", "rs1800407", "rs12896399", "rs16891982"]
HAIR_SNPS = ["rs12821256", "rs1805008", "rs1805007", "rs1805009", "rs16891982"]
SKIN_SNPS = [
    "rs1426654",  # SLC24A5
    "rs16891982", # SLC45A2
    "rs1042602",  # TYR
    "rs1800407",  # OCA2
    "rs1805007",  # MC1R
]
BLOOD_SNPS = ["rs8176719", "rs8176746", "rs590787"]
APOE_SNPS = ["rs429358", "rs7412"]
DIET_SNPS = ["rs4988235", "rs762551", "rs1801133", "rs2282679", "rs12785878", "rs10741657"]
PERFORMANCE_SNPS = ["rs1815739", "rs8192678", "rs4253778", "rs699", "rs16969968"]
ALCOHOL_SNPS = ["rs671"]
CELIAC_SNPS = ["rs2187668", "rs7454108"]
IRON_SNPS = ["rs1800562", "rs1799945"]
SLEEP_RECOVERY_SNPS = ["rs12927162", "rs228697", "rs139315125", "rs4680", "rs1799971", "rs6746030"]
TASTE_SNPS = ["rs713598", "rs1726866", "rs10246939"]

ALLOWED_EXTENSIONS = {".txt", ".csv", ".tsv"}


def extract_key_snps(genome, snps):
    out = {}
    for snp in snps:
        if snp in genome and genome[snp].get("genotype"):
            out[snp] = genome[snp]["genotype"]
    return out


def extract_debug_snp_groups(genome):
    """Return all supported editable marker groups for the child debug UI."""
    groups = {
        "eye": EYE_SNPS,
        "hair": HAIR_SNPS,
        "skin": SKIN_SNPS,
        "blood": BLOOD_SNPS,
        "apoe": APOE_SNPS,
        "diet_metabolism": DIET_SNPS,
        "performance_cardiometabolic": PERFORMANCE_SNPS,
        "alcohol_flush": ALCOHOL_SNPS,
        "celiac_risk": CELIAC_SNPS,
        "iron_metabolism": IRON_SNPS,
        "sleep_recovery": SLEEP_RECOVERY_SNPS,
        "taste_perception": TASTE_SNPS,
    }
    return {name: extract_key_snps(genome, snps) for name, snps in groups.items()}


def error_response(message, status_code=400, details=None):
    payload = {"error": message}
    if details:
        payload["details"] = details
    return jsonify(payload), status_code


@app.errorhandler(RequestEntityTooLarge)
def handle_large_upload(_error):
    return error_response("File exceeds the configured upload limit", status_code=413)


def save_upload(upload, subdir="uploads"):
    original_name = secure_filename(upload.filename or "")
    if not original_name:
        raise ValueError("Empty filename")

    suffix = Path(original_name).suffix.lower()
    if suffix not in ALLOWED_EXTENSIONS:
        raise ValueError("Unsupported file type")

    upload_dir = Path(os.getcwd()) / subdir
    upload_dir.mkdir(parents=True, exist_ok=True)
    stored_name = f"{uuid4().hex}{suffix}"
    file_path = upload_dir / stored_name
    upload.save(file_path)
    return str(file_path)


def delete_upload(file_path):
    """Best-effort removal of sensitive genotype data from local storage."""
    if file_path:
        try:
            Path(file_path).unlink(missing_ok=True)
        except OSError:
            app.logger.exception("Failed to delete processed upload")


def parse_uploaded_genome(upload, subdir="uploads"):
    """Save only long enough to parse, then remove the original upload."""
    file_path = save_upload(upload, subdir=subdir)
    try:
        return parse_raw_dna_file(file_path)
    finally:
        delete_upload(file_path)


# ---------------------------------------------------------
# Helper
# ---------------------------------------------------------
def load_genome_from_request(upload):
    """Reads raw DNA file"""
    return parse_uploaded_genome(upload, subdir="upload")


# ---------------------------------------------------------
# 1) SINGLE DNA UPLOAD – TRAIT + HEALTH
# ---------------------------------------------------------
@app.post("/upload_dna")
def upload_dna():
    if "file" not in request.files:
        return error_response("No file uploaded")

    file = request.files["file"]
    if file.filename == "":
        return error_response("Empty filename")

    try:
        dna_data = parse_uploaded_genome(file)
    except ValueError as exc:
        return error_response(str(exc))
    except Exception as exc:
        return error_response("Failed to parse genotype file", details=str(exc))

    traits = trait_engine.predict_traits(dna_data)
    health = risk_engine.compute_health_risk(dna_data)
    genotype_panel = extract_genotype_panel(dna_data)

    return {
        "status": "ok",
        "traits": traits,
        "health": health,
        "risk": health,  # backward compatibility alias
        "genotype_panel": genotype_panel
    }


# ---------------------------------------------------------
# 2) DOUBLE UPLOAD – CHILD PREDICTOR (traits/health only)
# ---------------------------------------------------------
@app.route("/upload_parents", methods=["POST"])
def upload_parents():
    if "file1" not in request.files or "file2" not in request.files:
        return error_response("Two DNA files required")

    p1_file = request.files["file1"]
    p2_file = request.files["file2"]

    try:
        parentA = load_genome_from_request(p1_file)
        parentB = load_genome_from_request(p2_file)
    except ValueError as exc:
        return error_response(str(exc))
    except Exception as exc:
        return error_response("Failed to parse one or both genotype files", details=str(exc))

    parentA_data = {
        "traits": predict_traits(parentA),
        "health": compute_health_risk(parentA),
        "key_genotypes": {
            "rs12913832": parentA.get("rs12913832", {}).get("genotype")
        },
        "key_snps": extract_debug_snp_groups(parentA),
    }

    parentB_data = {
        "traits": predict_traits(parentB),
        "health": compute_health_risk(parentB),
        "key_genotypes": {
            "rs12913832": parentB.get("rs12913832", {}).get("genotype")
        },
        "key_snps": extract_debug_snp_groups(parentB),
    }

    child = predict_child(parentA, parentB, simulations=32)

    # Height PGS for the sampled child genome (sex-specific)
    try:
        child_height_male = compute_height_pgs(child.get("child_genome") or {}, sex="male")
        child_height_female = compute_height_pgs(child.get("child_genome") or {}, sex="female")
        child_height = {"male": child_height_male, "female": child_height_female}
    except Exception as e:
        child_height = {"error": f"height_pgs_failed: {e}"}
    child["child_height_pgs"] = child_height

    return jsonify({
        "parentA": parentA_data,
        "parentB": parentB_data,
        "child": child
    })


# ---------------------------------------------------------
# 3) GENERATE PDF REPORT (for single or parents+child)
# ---------------------------------------------------------
@app.route("/generate_pdf", methods=["POST"])
def generate_pdf():
    data = request.json
    if not data:
        return error_response("Missing JSON payload")

    user_name = data.get("name", "Anonymous")
    traits = data["traits"]
    health = data["health"]
    child = data.get("child")

    pdf_buffer = generate_pdf_report(
        user_name=user_name,
        traits=traits,
        health=health,
        child=child
    )

    return send_file(
        pdf_buffer,
        as_attachment=True,
        download_name="genetic_report.pdf",
        mimetype="application/pdf"
    )


# ---------------------------------------------------------
# Health check
# ---------------------------------------------------------
@app.route("/status")
def status():
    return jsonify({"status": "Backend running"})


@app.route("/", methods=["GET"])
def root():
    return jsonify({"status": "Backend running", "endpoints": ["/status", "/upload_dna", "/upload_parents", "/generate_pdf", "/gene_lookup", "/gwas_traits", "/height_pgs"]})


# ---------------------------------------------------------
# 4) SUPPORTED GENE LOOKUP
# ---------------------------------------------------------
@app.post("/gene_lookup")
def gene_lookup():
    if "file" not in request.files:
        return error_response("No file uploaded")

    upload = request.files["file"]
    if upload.filename == "":
        return error_response("Empty filename")

    query = (request.form.get("query") or "").strip()
    if not query:
        return error_response("Missing gene or rsID query")

    try:
        genome = parse_uploaded_genome(upload)
    except ValueError as exc:
        return error_response(str(exc))
    except Exception as exc:
        return error_response("Failed to parse genotype file", details=str(exc))

    matches = search_supported_genes(genome, query)
    return jsonify({
        "query": query,
        "catalog_scope": "supported-gene-catalog",
        "results": matches,
        "result_count": len(matches),
    })


# ---------------------------------------------------------
# 5) GWAS TRAIT EXPLORER
# ---------------------------------------------------------
@app.post("/gwas_traits")
def gwas_traits():
    if "file" not in request.files:
        return error_response("No file uploaded")

    upload = request.files["file"]
    if upload.filename == "":
        return error_response("Empty filename")

    try:
        min_snps = int(request.form.get("min_snps", "2"))
    except Exception as exc:
        return error_response("Invalid min_snps", details=str(exc))

    try:
        genome = parse_uploaded_genome(upload)
    except ValueError as exc:
        return error_response(str(exc))
    except Exception as exc:
        return error_response("Failed to parse genotype file", details=str(exc))

    traits = compute_all_trait_prs(genome, min_snps=max(1, min_snps))
    return jsonify({
        "catalog_scope": "gwas_snps",
        "min_snps": max(1, min_snps),
        "result_count": len(traits),
        "traits": traits,
    })


# ---------------------------------------------------------
# 6) HEIGHT POLYGENIC SCORE
# ---------------------------------------------------------
@app.post("/height_pgs")
def height_pgs():
    if "file" not in request.files:
        return error_response("No file uploaded")

    upload = request.files["file"]
    if upload.filename == "":
        return error_response("Empty filename")

    try:
        file_path = save_upload(upload)
    except ValueError as exc:
        return error_response(str(exc))

    try:
        try:
            genome = parse_raw_dna_file(file_path)
        except Exception as e:
            return error_response("Failed to parse genotype file", details=str(e))

        sex = (request.form.get("sex") or "unspecified").lower()
        ancestry_payload = request.form.get("global_ancestry")
        global_ancestry = None
        if ancestry_payload:
            try:
                global_ancestry = json.loads(ancestry_payload)
            except Exception as e:
                return error_response("Invalid global_ancestry JSON", details=str(e))
        elif os.environ.get("ANCESTRY_INFERENCE_CONFIG"):
            try:
                ancestry_output = infer_global_ancestry_from_file(
                    raw_path=file_path,
                    output_dir=os.path.join(os.getcwd(), "uploads", "ancestry"),
                    config_path=os.environ["ANCESTRY_INFERENCE_CONFIG"],
                )
                global_ancestry = ancestry_output.get("global_ancestry")
            except Exception as e:
                return error_response("Failed to infer ancestry", status_code=500, details=str(e))
    finally:
        delete_upload(file_path)

    observed_height_cm = None
    if request.form.get("observed_height_cm"):
        try:
            observed_height_cm = float(request.form.get("observed_height_cm"))
        except Exception as e:
            return error_response("Invalid observed_height_cm", details=str(e))

    try:
        result = compute_height_pgs(
            genome, sex=sex, global_ancestry=global_ancestry, observed_height_cm=observed_height_cm
        )
    except FileNotFoundError:
        return error_response(
            "Height weights file not found",
            status_code=500,
            details="Expected height_demo_weights.csv under backend/nih/",
        )
    except Exception as e:
        return error_response("Failed to compute height PGS", status_code=500, details=str(e))

    return jsonify(result)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
