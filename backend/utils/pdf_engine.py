from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from io import BytesIO


# ---------------------------------------------------------
# Helper: section title
# ---------------------------------------------------------
def section_title(c, title, y):
    c.setFont("Helvetica-Bold", 18)
    c.setFillColor(colors.HexColor("#2E7D32"))
    c.drawString(50, y, title)
    c.setFillColor(colors.black)
    return y - 25


# ---------------------------------------------------------
# Helper: draw key-value text block
# ---------------------------------------------------------
def text_block(c, x, y, key, value, size=12):
    c.setFont("Helvetica-Bold", size)
    c.drawString(x, y, f"{key}:")
    c.setFont("Helvetica", size)
    c.drawString(x + 140, y, str(value))
    return y - (size + 6)


# ---------------------------------------------------------
# TRIM: shorten long lists for PDF display
# ---------------------------------------------------------
def format_list(arr, limit=8):
    if len(arr) <= limit:
        return ", ".join(arr)
    return ", ".join(arr[:limit]) + f"... (+{len(arr)-limit} more)"


# ---------------------------------------------------------
# MAIN FUNCTION
# ---------------------------------------------------------
def generate_pdf_report(user_name, traits, health, child=None):
    """
    traits = predict_traits(...)
    health = compute_health_risk(...)
    child = predict_child(...) or None
    """

    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter
    y = height - 60

    # COVER PAGE
    c.setFont("Helvetica-Bold", 28)
    c.setFillColor(colors.HexColor("#1B5E20"))
    c.drawString(50, y, "DNA Insight – Genetic Report")
    c.setFillColor(colors.black)

    y -= 50
    c.setFont("Helvetica", 16)
    c.drawString(50, y, f"Prepared for: {user_name}")

    y -= 30
    c.setFont("Helvetica", 12)
    c.drawString(50, y, "Confidential genetic summary")
    c.showPage()

    # PAGE 2 – TRAIT SUMMARY
    y = height - 60
    y = section_title(c, "Trait Summary", y)

    eye = traits["eye_color"]["result"]
    hair = traits["hair_color"]["result"]
    skin = traits["skin_color"]["result"]

    y = text_block(c, 50, y, "Eye Color", eye)
    y = text_block(c, 50, y, "Hair Color", hair)
    y = text_block(c, 50, y, "Skin Tone", skin)

    y = text_block(c, 50, y, "Freckling", traits["freckling"])
    y = text_block(c, 50, y, "Tanning Response", traits["tanning_response"])

    face = traits["face_shape"]
    y = text_block(c, 50, y, "Nose Width", face["nose_width"])
    y = text_block(c, 50, y, "Lip Fullness", face["lip_fullness"])
    y = text_block(c, 50, y, "Cheek Prominence", face["cheek_prominence"])

    if "lactose_tolerance" in traits:
        y = text_block(c, 50, y, "Lactose Tolerance", traits["lactose_tolerance"])
    if "caffeine_metabolism" in traits:
        y = text_block(c, 50, y, "Caffeine Metabolism", traits["caffeine_metabolism"])
    if "muscle_performance" in traits:
        y = text_block(c, 50, y, "Muscle Performance", traits["muscle_performance"])

    c.showPage()

    # PAGE 3 – HEALTH & RISK SUMMARY
    y = height - 60
    y = section_title(c, "Health Summary", y)

    apoe = health["apoe"]["genotype"]
    alz_risk = health["risk_summary"]["Alzheimers"]

    y = text_block(c, 50, y, "APOE Genotype", apoe)
    y = text_block(c, 50, y, "Alzheimer's Risk", alz_risk)

    prs = health["prs"]
    if prs["height"]:
        y = text_block(c, 50, y, "Height Percentile", f"{prs['height']['percentile']:.1f}%")
    if prs["bmi"]:
        y = text_block(c, 50, y, "Obesity Risk (BMI PRS)", health["risk_summary"]["Obesity"])
    if prs["diabetes"]:
        y = text_block(c, 50, y, "Diabetes Risk (PRS)", health["risk_summary"]["Diabetes"])
    if prs["heart_disease"]:
        y = text_block(c, 50, y, "Heart Disease Risk", health["risk_summary"]["HeartDisease"])

    dom = health["dominant_mutations"]
    if len(dom) > 0:
        y = text_block(c, 50, y, "Pathogenic Variants", format_list([d["gene"] for d in dom]))
    else:
        y = text_block(c, 50, y, "Pathogenic Variants", "None Detected")

    if "Celiac" in health["risk_summary"]:
        y = text_block(c, 50, y, "Celiac Markers", health["risk_summary"]["Celiac"])
    if "Hypertension" in health["risk_summary"]:
        y = text_block(c, 50, y, "Hypertension Marker", health["risk_summary"]["Hypertension"])

    c.showPage()

    # PAGE 4 – CARRIER STATUS
    y = height - 60
    y = section_title(c, "Carrier Status", y)

    carriers = health["carrier_status"]
    if len(carriers) == 0:
        c.setFont("Helvetica", 14)
        c.drawString(50, y, "No carrier variants detected.")
    else:
        c.setFont("Helvetica", 12)
        for cinfo in carriers:
            y -= 20
            gene = cinfo["gene"]
            var = cinfo["variant"]
            rsid = cinfo["rsid"]
            c.drawString(50, y, f"{gene} – {var} ({rsid})")

    c.showPage()

    # PAGE 5 – CHILD PREDICTION (if provided)
    if child:
        y = height - 60
        y = section_title(c, "Child Predictor", y)

        ct = child["child_traits"]
        y = text_block(c, 50, y, "Eye Color", ct["eye_color"]["result"])
        y = text_block(c, 50, y, "Hair Color", ct["hair_color"]["result"])
        y = text_block(c, 50, y, "Skin Tone", ct["skin_color"]["result"])

        c.showPage()

    c.save()
    buffer.seek(0)
    return buffer
