import json
import os
import uuid
from sentence_transformers import SentenceTransformer, util

# --------------------------------------
# Safety / configuration
# --------------------------------------

RED_FLAGS = [
    "unconscious", "seizure", "fits", "cannot breathe",
    "blue lips", "blood in stool", "blood in vomit", "chest pain"
]

CLUSTER_PRIORITY = {
    "cardiac": 5,
    "neurological": 5,
    "respiratory": 4,
    "poisoning": 4,
    "snake_scorpion_bite": 4,
    "maternal_health": 4,
    "gastrointestinal": 3,
    "vector_borne_fever": 3,
    "tuberculosis_suspect": 3,
    "jaundice_hepatitis": 3,
    "fever_general": 2,
    "pediatric_general": 2
}

NEGATION_PHRASES = [
    "no", "not", "none", "never",
    "no such", "nothing like",
    "only headache", "only pain",
    "no problem", "no symptoms"
]


class SymptomCollector:
    """
    SBERT-based deterministic symptom clarification engine.

    ✔ Semantic cluster detection
    ✔ Slot filling
    ✔ Negative confirmation handling (CRITICAL FIX)
    ❌ No regex
    ❌ No intent guessing
    ❌ No LLM
    """

    def __init__(self, *_):
        self.model = SentenceTransformer("all-MiniLM-L6-v2")

        base = os.path.dirname(os.path.abspath(__file__))
        with open(os.path.join(base, "symptom_clusters.json"), "r", encoding="utf-8") as f:
            self.clusters = json.load(f)

        self.sessions = {}

    # --------------------------------------
    # Embedding helper
    # --------------------------------------
    def _embed(self, text):
        return self.model.encode(text, convert_to_tensor=True)

    # --------------------------------------
    # Simple negative confirmation detector
    # --------------------------------------
    def is_negative_answer(self, answer: str) -> bool:
        a = answer.lower().strip()
        return any(p in a for p in NEGATION_PHRASES)

    # --------------------------------------
    # STEP 1: Detect active clusters
    # --------------------------------------
    def detect_clusters(self, text, threshold=0.45):
        text_emb = self._embed(text)
        active = {}

        for cname, cdata in self.clusters.items():
            best = 0.0
            for kw in cdata.get("keywords", []):
                sim = util.cos_sim(text_emb, self._embed(kw))[0][0]
                best = max(best, float(sim))

            if best >= threshold:
                active[cname] = {
                    "score": best,
                    "priority": CLUSTER_PRIORITY.get(cname, 1),
                    "slots": {slot: None for slot in cdata["questions"]}
                }

        return active

    # --------------------------------------
    # STEP 2: Auto-fill slots if already answered
    # --------------------------------------
    def prefill_slots(self, text, active_clusters):
        text_emb = self._embed(text)

        for cname, cdata in active_clusters.items():
            for slot in cdata["slots"]:
                if cdata["slots"][slot] is not None:
                    continue

                question = self.clusters[cname]["questions"][slot]
                sim = util.cos_sim(text_emb, self._embed(question))[0][0]

                if float(sim) >= 0.55:
                    cdata["slots"][slot] = True

    # --------------------------------------
    # STEP 3: Start case
    # --------------------------------------
    def clarification_loop_api(self, initial_input, *_):
        cid = str(uuid.uuid4())[:8]

        active = self.detect_clusters(initial_input)
        self.prefill_slots(initial_input, active)

        self.sessions[cid] = {
            "text": initial_input,
            "active_clusters": active,
            "asked": set(),
            "last_cluster": None   # ⭐ track last asked cluster
        }

        return initial_input, [self._next_question(cid)]

    # --------------------------------------
    # STEP 4: Decide next question
    # --------------------------------------
    def _next_question(self, cid):
        session = self.sessions[cid]


        ordered = sorted(
            session["active_clusters"].items(),
            key=lambda x: (x[1]["priority"], x[1]["score"]),
            reverse=True
        )

        for cname, cdata in ordered:
            for slot, value in cdata["slots"].items():
                qid = f"{cname}:{slot}"
                if value is None and qid not in session["asked"]:
                    question = self.clusters[cname]["questions"][slot]

                    print("\n [Collector] NEXT QUESTION SELECTED")
                    print(f"   Cluster : {cname}")
                    print(f"   Slot    : {slot}")
                    print(f"   Text    : {question}")
                    print("--------------------------------------------------")
                
                    session["asked"].add(qid)
                    session["last_cluster"] = cname   # ⭐ remember source
                    return self.clusters[cname]["questions"][slot]
        print("[Collector] No more questions")
        return None

    # --------------------------------------
    # STEP 5: After each answer
    # --------------------------------------
    def generate_next_question_api(
        self,
        collected_context,
        new_answers=None,
        asked_questions=None,
        confidence_threshold=70
    ):
        cid = next(iter(self.sessions))
        session = self.sessions[cid]

        # ⭐ NEGATIVE CONFIRMATION HANDLING
        if new_answers:
            for ans in new_answers.values():
                if self.is_negative_answer(ans):
                    denied = session.get("last_cluster")
                    if denied and denied in session["active_clusters"]:
                        # Close entire cluster
                        for slot in session["active_clusters"][denied]["slots"]:
                            session["active_clusters"][denied]["slots"][slot] = True

        session["text"] = collected_context
        self.prefill_slots(collected_context, session["active_clusters"])

        next_q = self._next_question(cid)

        if not next_q:
            return True, None, collected_context

        return False, next_q, collected_context
