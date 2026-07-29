from io import BytesIO

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas


def section_title(pdf, title, y):
    pdf.setFont("Helvetica-Bold", 18)
    pdf.setFillColor(colors.HexColor("#2E7D32"))
    pdf.drawString(50, y, title)
    pdf.setFillColor(colors.black)
    return y - 25


def text_block(pdf, x, y, key, value, size=12):
    pdf.setFont("Helvetica-Bold", size)
    pdf.drawString(x, y, f"{key}:")
    pdf.setFont("Helvetica", size)
    pdf.drawString(x + 140, y, str(value))
    return y - (size + 6)


def format_list(values, limit=8):
    if len(values) <= limit:
        return ", ".join(values)
    return ", ".join(values[:limit]) + f"... (+{len(values) - limit} more)"


def generate_pdf_report(user_name, traits, health, child=None):
    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=letter)
    _width, height = letter
    y = height - 60

    pdf.setFont("Helvetica-Bold", 28)
    pdf.setFillColor(colors.HexColor("#1B5E20"))
    pdf.drawString(50, y, "DNA Insight - Genetic Report")
    pdf.setFillColor(colors.black)

    y -= 50
    pdf.setFont("Helvetica", 16)
    pdf.drawString(50, y, f"Prepared for: {user_name}")

    y -= 30
    pdf.setFont("Helvetica", 12)
    pdf.drawString(50, y, "Confidential genetic summary")
    pdf.showPage()

    y = height - 60
    y = section_title(pdf, "Trait Summary", y)

    y = text_block(pdf, 50, y, "Eye Color", traits["eye_color"]["result"])
    y = text_block(pdf, 50, y, "Hair Color", traits["hair_color"]["result"])
    y = text_block(pdf, 50, y, "Skin Tone", traits["skin_color"]["result"])
    y = text_block(pdf, 50, y, "Freckling", traits["freckling"])
    y = text_block(pdf, 50, y, "Tanning Response", traits["tanning_response"])

    face = traits["face_shape"]
    y = text_block(pdf, 50, y, "Nose Width", face["nose_width"])
    y = text_block(pdf, 50, y, "Lip Fullness", face["lip_fullness"])
    y = text_block(pdf, 50, y, "Cheek Prominence", face["cheek_prominence"])

    if "lactose_tolerance" in traits:
        y = text_block(pdf, 50, y, "Lactose Tolerance", traits["lactose_tolerance"])
    if "caffeine_metabolism" in traits:
        y = text_block(pdf, 50, y, "Caffeine Metabolism", traits["caffeine_metabolism"])
    if "muscle_performance" in traits:
        y = text_block(pdf, 50, y, "Muscle Performance", traits["muscle_performance"])
    if "blood_type" in traits:
        y = text_block(pdf, 50, y, "Blood Type (ABO + RhD)", traits["blood_type"])

    pdf.showPage()

    y = height - 60
    y = section_title(pdf, "Health Summary", y)

    apoe = health["apoe"]["genotype"]
    alz_risk = health["risk_summary"]["Alzheimers"]

    y = text_block(pdf, 50, y, "APOE Genotype", apoe)
    y = text_block(pdf, 50, y, "Alzheimer's Risk", alz_risk)

    prs = health["prs"]
    if prs["height"]:
        y = text_block(pdf, 50, y, "Height Percentile", f"{prs['height']['percentile']:.1f}%")
    if prs["bmi"]:
        y = text_block(pdf, 50, y, "Obesity Risk (BMI PRS)", health["risk_summary"]["Obesity"])
    if prs["diabetes"]:
        y = text_block(pdf, 50, y, "Diabetes Risk (PRS)", health["risk_summary"]["Diabetes"])
    if prs["heart_disease"]:
        y = text_block(pdf, 50, y, "Heart Disease Risk", health["risk_summary"]["HeartDisease"])

    clinical = health.get("clinical_findings") or {}
    dominant_findings = clinical.get("dominant_findings", health.get("dominant_mutations", []))
    if dominant_findings:
        y = text_block(pdf, 50, y, "Pathogenic Variants", format_list([item["gene"] for item in dominant_findings]))
    else:
        y = text_block(pdf, 50, y, "Pathogenic Variants", "None Detected")

    if "Celiac" in health["risk_summary"]:
        y = text_block(pdf, 50, y, "Celiac Markers", health["risk_summary"]["Celiac"])
    if "Hypertension" in health["risk_summary"]:
        y = text_block(pdf, 50, y, "Hypertension Marker", health["risk_summary"]["Hypertension"])

    pdf.showPage()

    y = height - 60
    y = section_title(pdf, "ClinVar Findings", y)

    reportable_findings = clinical.get("reportable_findings", [])
    if not reportable_findings:
        pdf.setFont("Helvetica", 14)
        pdf.drawString(50, y, "No reportable ClinVar germline findings detected.")
    else:
        pdf.setFont("Helvetica", 12)
        for finding in reportable_findings:
            y -= 20
            label = finding.get("report_label", "Clinical finding")
            pdf.drawString(50, y, f"{finding['gene']} - {label} - {finding['rsid']} - {finding['genotype']}")
            if y < 80:
                pdf.showPage()
                y = height - 60
                pdf.setFont("Helvetica", 12)

    pdf.showPage()

    if child:
        y = height - 60
        y = section_title(pdf, "Child Predictor", y)

        child_traits = child["child_traits"]
        y = text_block(pdf, 50, y, "Eye Color", child_traits["eye_color"]["result"])
        y = text_block(pdf, 50, y, "Hair Color", child_traits["hair_color"]["result"])
        y = text_block(pdf, 50, y, "Skin Tone", child_traits["skin_color"]["result"])
        pdf.showPage()

    pdf.save()
    buffer.seek(0)
    return buffer
