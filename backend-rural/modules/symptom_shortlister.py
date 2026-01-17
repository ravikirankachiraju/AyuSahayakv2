import json
import os
from sentence_transformers import SentenceTransformer, util


# -----------------------------
# Deterministic Negation Words
# -----------------------------
NEGATION_WORDS = {
    "no", "not", "never", "without", "denies", "deny",
    "none", "nothing", "nil", "absent"
}


class SymptomShortlister:
    """
    Deterministic SBERT-based symptom extractor with negation handling.
    - NO LLM
    - NO hallucination
    - Semantic detection + logical polarity
    """

    def __init__(self, *_):
        self.model = SentenceTransformer("all-MiniLM-L6-v2")

        BASE_DIR = os.path.dirname(os.path.abspath(__file__))
        CLUSTER_PATH = os.path.join(BASE_DIR, "symptom_clusters.json")

        with open(CLUSTER_PATH, "r", encoding="utf-8") as f:
            self.clusters = json.load(f)

        # -----------------------------
        # Build flat symptom list
        # -----------------------------
        self.symptoms = set()
        for cluster in self.clusters.values():
            for kw in cluster.get("keywords", []):
                self.symptoms.add(kw.lower())

        # -----------------------------
        # Pre-embed symptoms
        # -----------------------------
        self.symptom_embeddings = {
            s: self.model.encode(s, convert_to_tensor=True)
            for s in self.symptoms
        }

    # -------------------------------------------------
    # Local window-based negation detection
    # -------------------------------------------------
    def _is_negated(self, text: str, symptom: str, window: int = 4) -> bool:
        tokens = text.lower().split()
        sym_tokens = symptom.split()

        for i in range(len(tokens)):
            if tokens[i:i + len(sym_tokens)] == sym_tokens:
                start = max(0, i - window)
                context = tokens[start:i]

                for w in context:
                    if w in NEGATION_WORDS:
                        return True

        return False

    # -------------------------------------------------
    # Main shortlisting function
    # -------------------------------------------------
    def shortlist(self, patient_text: str):
        text = patient_text.lower()
        text_emb = self.model.encode(text, convert_to_tensor=True)

        present = []
        absent = []

        for symptom, sym_emb in self.symptom_embeddings.items():
            score = util.cos_sim(text_emb, sym_emb)[0][0]

            if score >= 0.50:  # semantic match
                if self._is_negated(text, symptom):
                    absent.append(symptom)
                else:
                    present.append(symptom)

        return {
            "symptoms": sorted(present),
            "negated_symptoms": sorted(absent),
            "raw_text": patient_text
        }
