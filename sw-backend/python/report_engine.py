import re
import numpy as np
from sentence_transformers import SentenceTransformer

model = SentenceTransformer("all-MiniLM-L6-v2")

def normalize_name(name):
    name = re.sub(r"^[A-Z]{2}-", "", name)  # remove FU-, VI-, PA-
    name = re.sub(r"\([^)]*\)", "", name)   # remove brackets
    return name.replace("-", " ").strip().lower()

def extract_section(text, header):
    pattern = rf"{header}:\n([\s\S]*?)(?=\n[A-Z][a-zA-Z ]+?:|\Z)"
    match = re.search(pattern, text)
    return match.group(1).strip() if match else ""

def score_diseases(top3_classes, questions, answers):
    scores = {d: 0.0 for d in top3_classes}

    for q_obj, ans in zip(questions, answers):
        disease = q_obj["disease"]
        feats = q_obj["feature_phrases"]

        ans_emb = model.encode([ans], convert_to_numpy=True)[0]
        ans_emb /= np.linalg.norm(ans_emb)

        feat_emb = model.encode(feats, convert_to_numpy=True)
        feat_emb /= np.linalg.norm(feat_emb, axis=1, keepdims=True)

        sims = np.dot(feat_emb, ans_emb.T)
        scores[disease] += float(sims.max())

    return scores


def build_report(final_diagnosis, rag_summary):
    readable = normalize_name(final_diagnosis)

    # -------- extract correct disease block --------
    block = ""
    for section in rag_summary.split("\n---\n"):
        if readable in section.lower():
            block = section
            break

    overview = extract_section(block, "Overview")
    symptoms = extract_section(block, "Symptoms and Clinical Presentation")
    treatment = extract_section(block, "Treatment and Medications")
    home_care = extract_section(block, "Home Care and Prevention")

    reasoning = (
        f"The patient’s symptoms and nurse answers closely match the typical pattern of {readable}. "
        f"{symptoms}" if symptoms else f"Findings are most consistent with {readable}."
    )

    recommended = (
        f"Follow home care guidance. {home_care}"
        if home_care else f"Follow standard home care guidelines for {readable}."
    )

    medicines = (
        treatment if treatment else "Use only mild OTC antifungals / antihistamines. Avoid strong steroids or antibiotics without a doctor."
    )

    return {
        "final_diagnosis": readable.title(),
        "clinical_reasoning": reasoning,
        "recommended_action": recommended,
        "red_flags": (
            "Seek urgent care if the rash spreads rapidly, there is severe pain, high fever, dizziness, vomiting, "
            "or difficulty moving."
        ),
        "medicines": medicines,
        "disclaimer": "This AI report supports clinical decisions but is not a replacement for dermatologist evaluation."
    }
