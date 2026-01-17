# modules/complexity.py

import numpy as np
import os

import joblib
from sentence_transformers import SentenceTransformer

LABELS = ["low","medium","high"]


class ComplexityAssessor:
    """
    ML-based complexity assessor using SBERT + vitals + safety rules.
    """

    def __init__(self, *_):
        self.model = SentenceTransformer("all-MiniLM-L6-v2")
        BASE_DIR = os.path.dirname(__file__)
        MODEL_PATH = os.path.join(BASE_DIR, "complexity_model.pkl")
        self.clf = joblib.load(MODEL_PATH)


    def _embed(self, text):
        return self.model.encode([text], normalize_embeddings=True)[0]

    def _vital_vector(self, v):
        return np.array([
            v.get("age",30),
            v.get("spo2",98),
            v.get("pulse",80),
            v.get("bp_sys",120),
            v.get("bp_dia",80),
            1 if v.get("age",30)<5 else 0,
            1 if v.get("age",30)>=60 else 0,
            1 if v.get("spo2",98)<94 else 0,
            1 if v.get("bp_sys",120)<90 else 0,
            1 if v.get("pulse",80)>110 else 0
        ], dtype=float)

    def assess(self, symptom_summary: dict) -> str:
        text = symptom_summary.get("raw_text","").lower()
          # 🔍 DEBUG: print incoming symptom text
        print("\n🧠 [ComplexityAgent] Input symptom text:")
        print(text)
        print("--------------------------------------------------")

        # 🚨 hard override
      

        text_vec = self._embed(text)
        vitals = symptom_summary.get("vitals",{})
        vvec = self._vital_vector(vitals)

        X = np.hstack([text_vec, vvec])
        probs = self.clf.predict_proba([X])[0]
        predicted = LABELS[int(probs.argmax())]

        print(f"🧠 [ComplexityAgent] Predicted complexity: {predicted}\n")
        return LABELS[int(probs.argmax())]
