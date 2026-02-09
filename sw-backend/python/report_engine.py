import re
import numpy as np
from sentence_transformers import SentenceTransformer

# -----------------------------
# SBERT model
# -----------------------------
model = SentenceTransformer("all-MiniLM-L6-v2")

# -----------------------------
# Helpers
# -----------------------------
def normalize_name(name):
    name = re.sub(r"^[A-Z]{2}-", "", name)   # remove FU-, VI-, PA-
    name = re.sub(r"\([^)]*\)", "", name)    # remove brackets
    return name.replace("-", " ").strip().lower()


def extract_section(text, header):
    pattern = rf"{header}:\n([\s\S]*?)(?=\n[A-Z][a-zA-Z ]+?:|\Z)"
    match = re.search(pattern, text)
    return match.group(1).strip() if match else ""


# -----------------------------
# YES / NO NORMALIZATION (CRITICAL)
# -----------------------------
YES_PATTERNS = [
    r"\byes\b", r"\byeah\b", r"\byep\b", r"\btrue\b",
    r"\bpresent\b", r"\bseen\b", r"\bexists\b",
    r"\blooks like\b", r"\bthere is\b", r"\bi see\b",
    r"\bslightly\b", r"\bsome\b", r"\bmaybe\b"
]

NO_PATTERNS = [
    r"\bno\b", r"\bnot\b", r"\bnever\b", r"\bnone\b",
    r"\babsent\b", r"\bdoesn't\b", r"\bdoes not\b",
    r"\bdon't\b", r"\bdo not\b", r"\bwithout\b",
    r"\bnegative\b"
]


def normalize_yes_no(answer: str) -> str:
    """
    Returns: 'yes', 'no', or 'unknown'
    """
    if not answer:
        return "unknown"

    ans = answer.lower().strip()

    for p in NO_PATTERNS:
        if re.search(p, ans):
            return "no"

    for p in YES_PATTERNS:
        if re.search(p, ans):
            return "yes"

    return "unknown"


# -----------------------------
# DISEASE SCORING (FIXED LOGIC)
# -----------------------------
def score_diseases(top3_classes, questions, answers):
    """
    Rules:
    - YES      → SBERT similarity contributes
    - NO       → score = 0 for that disease
    - UNKNOWN  → very small contribution
    """

    scores = {d: 0.0 for d in top3_classes}

    for q_obj, ans in zip(questions, answers):
        disease = q_obj["disease"]
        features = q_obj["feature_phrases"]

        yn = normalize_yes_no(ans)

        # ❌ Explicit NO → zero contribution
        if yn == "no":
            continue

        # Encode answer
        ans_emb = model.encode([ans], convert_to_numpy=True)[0]
        ans_emb /= np.linalg.norm(ans_emb)

        feat_emb = model.encode(features, convert_to_numpy=True)
        feat_emb /= np.linalg.norm(feat_emb, axis=1, keepdims=True)

        similarity = float(np.dot(feat_emb, ans_emb.T).max())

        if yn == "yes":
            scores[disease] += similarity

        elif yn == "unknown":
            scores[disease] += similarity * 0.3   # weak evidence

    return scores


# -----------------------------
# REPORT GENERATION
# -----------------------------
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
        f"The patient’s symptoms and nurse responses closely match the typical pattern of {readable}. "
        f"{symptoms}"
        if symptoms else
        f"Findings are most consistent with {readable}."
    )

    recommended = (
        f"Follow home care guidance. {home_care}"
        if home_care else
        f"Follow standard home care guidelines for {readable}."
    )

    medicines = (
        treatment
        if treatment else
        "Use only mild OTC antifungals or antihistamines. "
        "Avoid strong steroids or antibiotics without a doctor."
    )

    return {
        "final_diagnosis": readable.title(),
        "clinical_reasoning": reasoning,
        "recommended_action": recommended,
        "red_flags": (
            "Seek urgent care if the rash spreads rapidly, "
            "there is severe pain, high fever, dizziness, vomiting, "
            "or difficulty moving."
        ),
        "medicines": medicines,
        "disclaimer": (
            "This AI report supports clinical decisions but "
            "is not a replacement for dermatologist evaluation."
        )
    }