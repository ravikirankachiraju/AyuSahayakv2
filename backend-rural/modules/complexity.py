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
        age   = v.get("age")
        spo2  = v.get("spo2")
        pulse = v.get("pulse")
        sys   = v.get("bp_sys")
        dia   = v.get("bp_dia")
    
        return np.array([
            age   if age   is not None else 30,
            spo2  if spo2  is not None else 98,
            pulse if pulse is not None else 80,
            sys   if sys   is not None else 120,
            dia   if dia   is not None else 80,
    
            1 if (age  is not None and age < 5) else 0,
            1 if (age  is not None and age >= 60) else 0,
            1 if (spo2 is not None and spo2 < 94) else 0,
            1 if (sys  is not None and sys < 90) else 0,
            1 if (pulse is not None and pulse > 110) else 0,
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
