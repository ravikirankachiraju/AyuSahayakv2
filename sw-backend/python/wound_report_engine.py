# wound_report_engine.py
import re
import numpy as np
from sentence_transformers import SentenceTransformer

model = SentenceTransformer("all-MiniLM-L6-v2")


def extract_section(block, header):
    """
    Extracts text under a specific header until the next header.
    Uses case-insensitive matching.
    """
    pattern = rf"{header}:\s*\n([\s\S]*?)(?=\n[A-Za-z][A-Za-z\s&()]+?:|\Z)"
    match = re.search(pattern, block, flags=re.IGNORECASE)
    return match.group(1).strip() if match else ""


def score_diseases(top3_classes, questions, answers):
    """
    SBERT scoring based on semantic similarity.
    """
    scores = {d: 0.0 for d in top3_classes}

    for q, ans in zip(questions, answers):
        disease = q["disease"]
        features = q["feature_phrases"]

        ans_emb = model.encode([ans], convert_to_numpy=True)[0]
        ans_emb /= np.linalg.norm(ans_emb)

        feat_emb = model.encode(features, convert_to_numpy=True)
        feat_emb /= np.linalg.norm(feat_emb, axis=1, keepdims=True)

        sim = np.dot(feat_emb, ans_emb.T)
        scores[disease] += float(sim.max())

    return scores


def build_report(final_diagnosis, rag_summary):
    """
    Builds the final structured wound report using RAG content.
    Works with your EXACT wound.txt format.
    """

    # ---------- 1. FIND THE FULL BLOCK ----------
    # Always extract until next ### section
    disease_lower = final_diagnosis.lower()

    start = rag_summary.lower().find(disease_lower)
    if start == -1:
        block = rag_summary
    else:
        remaining = rag_summary[start:]
        parts = remaining.split("###")
        block = parts[0]  # full block for this disease

    # Clean markdown headers
    block = re.sub(r"^###.*$", "", block, flags=re.MULTILINE).strip()

    # ---------- 2. EXTRACT SECTIONS ----------
    overview = extract_section(block, "Overview")
    symptoms = extract_section(block, "Symptoms and Clinical Presentation")
    treatment = extract_section(block, "Treatment and Medications")
    homecare = extract_section(block, "Home Care and Prevention")

    # ---------- 3. RETURN STRUCTURED FIELDS ----------
    return {
        "final_diagnosis": final_diagnosis,
        "clinical_reasoning": (overview + "\n\n" + symptoms).strip(),
        "recommended_action": homecare or "Basic wound care instructions apply.",
        "medicines": treatment or "No specific medicines listed.",
        "red_flags": (
            "Watch for spreading redness, worsening swelling, foul smell, fever, severe pain, "
            "blackened tissue, or rapid deterioration."
        ),
        "disclaimer": (
            "AI-generated wound assessment. A wound-care specialist must verify before major treatment decisions."
        )
    }
