import os
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from utils import risk_engine, trait_engine
from utils.dna_parser import parse_raw_dna_file
from utils.trait_engine import predict_traits
from utils.risk_engine import compute_health_risk
from utils.child_predictor import predict_child
from utils.pdf_engine import generate_pdf_report
from utils.genotype_panel import extract_genotype_panel

app = Flask(__name__)
CSRF_COOKIE_SECURE = True
CORS(app)

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


def extract_key_snps(genome, snps):
    out = {}
    for snp in snps:
        if snp in genome and genome[snp].get("genotype"):
            out[snp] = genome[snp]["genotype"]
    return out


# ---------------------------------------------------------
# Helper
# ---------------------------------------------------------
def load_genome_from_request(upload):
    """Reads raw DNA file"""
    filepath = f"upload/{upload.filename}"
    upload.save(filepath)

    genome = parse_raw_dna_file(filepath)
    return genome


# ---------------------------------------------------------
# 1) SINGLE DNA UPLOAD – TRAIT + HEALTH
# ---------------------------------------------------------
@app.post("/upload_dna")
def upload_dna():
    if "file" not in request.files:
        return {"error": "No file uploaded"}, 400

    file = request.files["file"]
    if file.filename == "":
        return {"error": "Empty filename"}, 400

    filename = file.filename

    UPLOAD_FOLDER = os.path.join(os.getcwd(), "uploads")
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)

    file_path = os.path.join(UPLOAD_FOLDER, filename)
    file.save(file_path)

    dna_data = parse_raw_dna_file(file_path)
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
        return jsonify({"error": "Two DNA files required"}), 400

    p1_file = request.files["file1"]
    p2_file = request.files["file2"]

    parentA = load_genome_from_request(p1_file)
    parentB = load_genome_from_request(p2_file)

    parentA_data = {
        "traits": predict_traits(parentA),
        "health": compute_health_risk(parentA),
        "key_genotypes": {
            "rs12913832": parentA.get("rs12913832", {}).get("genotype")
        },
        "key_snps": {
            "eye": extract_key_snps(parentA, EYE_SNPS),
            "hair": extract_key_snps(parentA, HAIR_SNPS),
            "skin": extract_key_snps(parentA, SKIN_SNPS),
        },
    }

    parentB_data = {
        "traits": predict_traits(parentB),
        "health": compute_health_risk(parentB),
        "key_genotypes": {
            "rs12913832": parentB.get("rs12913832", {}).get("genotype")
        },
        "key_snps": {
            "eye": extract_key_snps(parentB, EYE_SNPS),
            "hair": extract_key_snps(parentB, HAIR_SNPS),
            "skin": extract_key_snps(parentB, SKIN_SNPS),
        },
    }

    child = predict_child(parentA, parentB)

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
    return jsonify({"status": "Backend running", "endpoints": ["/status", "/upload_dna", "/upload_parents", "/generate_pdf"]})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
