import re
import numpy as np
from sentence_transformers import SentenceTransformer, CrossEncoder


class SemanticAnswerGuardrail:
    """
    Semantic-first medical answer validator
    GUARANTEED coverage for all questions in provided clusters.

    Design:
    - Intent-aware
    - Semantic-first
    - Polarity-aware
    - Numeric-aware
    - Red-flag safe
    """

    # -----------------------------
    # Polarity & state vocabulary
    # -----------------------------
    NEGATIVE_WORDS = {
        "no", "not", "none", "never", "normal", "fine", "okay",
        "good", "absent", "without", "nil", "nothing"
    }

    POSITIVE_WORDS = {
        "yes", "present", "having", "exists", "severe", "mild",
        "continuous", "worse", "vomiting", "bleeding", "pain",
        "breathless", "confused", "drowsy"
    }

    STATE_WORDS = {
        "alert", "conscious", "feeding", "active",
        "eating", "drinking", "responsive"
    }

    NUMBER_PATTERN = r"\b\d+\b"

    # -----------------------------
    # Init
    # -----------------------------
    def __init__(self):
        self.embedder = SentenceTransformer("all-MiniLM-L6-v2")
        self.cross_encoder = CrossEncoder(
            "cross-encoder/ms-marco-MiniLM-L-6-v2"
        )

    # -----------------------------
    # Infer intent from question
    # -----------------------------
    def infer_intent(self, question: str) -> str:
        q = question.lower()

        if any(w in q for w in ["since", "when", "how long", "weeks", "days"]):
            return "duration"

        if any(w in q for w in ["how many", "times", "24 hours"]):
            return "frequency"

        if any(w in q for w in ["severe", "mild", "continuous", "active", "feeding"]):
            return "severity"

        if any(w in q for w in ["any", "with", "along with", "only"]):
            return "systems"

        if any(w in q for w in [
            "confusion", "bleeding", "unconscious",
            "collapse", "fits", "seizure", "paralysis"
        ]):
            return "red_flag"

        return "systems"

    # -----------------------------
    # Polarity detection
    # -----------------------------
    def detect_polarity(self, answer: str) -> str:
        a = answer.lower()

        if any(w in a for w in self.NEGATIVE_WORDS):
            return "negative"

        if any(w in a for w in self.POSITIVE_WORDS):
            return "positive"

        if any(w in a for w in self.STATE_WORDS):
            return "positive"

        return "unknown"

    # -----------------------------
    # Semantic similarity
    # -----------------------------
    def semantic_similarity(self, t1: str, t2: str) -> float:
        v1 = self.embedder.encode(t1, normalize_embeddings=True)
        v2 = self.embedder.encode(t2, normalize_embeddings=True)
        return float(np.dot(v1, v2))

    # -----------------------------
    # Main validation
    # -----------------------------
    def validate(self, question: str, answer: str) -> dict:
        if not answer or not answer.strip():
            return {"is_valid": False, "reason": "Empty answer"}

        answer = answer.strip().lower()
        intent = self.infer_intent(question)
        polarity = self.detect_polarity(answer)

        # 1️⃣ Duration → always valid
        if intent == "duration":
            return {
                "is_valid": True,
                "reason": "Duration response",
                "polarity": polarity
            }

        # 2️⃣ Numeric answers (frequency, pregnancy, weeks, etc.)
        if re.search(self.NUMBER_PATTERN, answer):
            return {
                "is_valid": True,
                "reason": "Numeric clinical response",
                "polarity": polarity
            }

        # 3️⃣ Red flags → ANY clear yes/no or symptom mention is valid
        if intent == "red_flag":
            if polarity in {"positive", "negative"}:
                return {
                    "is_valid": True,
                    "reason": "Red-flag polarity response",
                    "polarity": polarity
                }

        # 4️⃣ Systems / severity → accept polarity & state words
        if intent in {"systems", "severity"}:
            if polarity in {"positive", "negative"}:
                return {
                    "is_valid": True,
                    "reason": "Polarity-based clinical response",
                    "polarity": polarity
                }

        # 5️⃣ Semantic similarity (primary semantic gate)
        sim = self.semantic_similarity(question, answer)
        if sim >= 0.45:
            return {
                "is_valid": True,
                "reason": "Semantic match",
                "confidence": round(sim, 3),
                "polarity": polarity
            }

        # 6️⃣ Cross-encoder fallback (high precision)
        ce_score = self.cross_encoder.predict([(question, answer)])[0]
        if ce_score >= 0.30:
            return {
                "is_valid": True,
                "reason": "Semantic relevance (cross-encoder)",
                "confidence": round(float(ce_score), 3),
                "polarity": polarity
            }

        # ❌ Reject
        return {
            "is_valid": False,
            "reason": "Answer not clinically relevant",
            "confidence": round(sim, 3)
        }


# -----------------------------
# Quick sanity test
# -----------------------------
if __name__ == "__main__":
    g = SemanticAnswerGuardrail()

    tests = [
        ("Is the patient breathless at rest or while walking?", "breathing is fine"),
        ("Any vomiting, headache, or bleeding?", "only mild headache"),
        ("How many months pregnant is the patient?", "7 months"),
        ("Is the child feeding and active?", "feeding less but active"),
        ("Any confusion or fits?", "patient is alert"),
        ("Since how many weeks has the cough been present?", "about 3 weeks")
    ]

    for q, a in tests:
        print("\nQ:", q)
        print("A:", a)
        print("→", g.validate(q, a))
