"""
Deterministic SBERT-based MDT Agent
----------------------------------
• NO LLM
• NO hallucination
• SBERT only for semantic template matching
• Rule-based specialist selection
• Nurse-safe, non-prescriptive output
"""

from typing import Dict, List
import json
import os
import numpy as np
from sentence_transformers import SentenceTransformer

# =====================================================
# LOAD MDT RULES
# =====================================================
BASE_DIR = os.path.dirname(os.path.dirname(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
MDT_RULES_PATH = os.path.join(DATA_DIR, "mdt_rules.json")

with open(MDT_RULES_PATH, encoding="utf-8") as f:
    MDT_RULES = json.load(f)

# =====================================================
# SAFETY CONSTANTS
# =====================================================


SIMILARITY_THRESHOLD = 0.35  # safety cutoff

# =====================================================
# SPECIALIST SELECTION (RULE-BASED)
# =====================================================
def select_specialists(case_text: str, vitals: Dict) -> List[str]:
    txt = case_text.lower()
    age = vitals.get("age", 30)
    bp_sys = vitals.get("bp_sys", 120)

    if "chest pain" in txt or "breathing difficulty" in txt:
        return ["Cardiologist", "Pulmonologist"]

    if age < 12 and ("fever" in txt or "cough" in txt):
        return ["Pediatrician", "Pulmonologist"]

    if "vomit" in txt or "stomach" in txt or "abdominal" in txt:
        return ["Gastroenterologist", "GeneralPhysician"]

    if bp_sys < 100 or "dizziness" in txt:
        return ["Cardiologist", "Neurologist"]

    return ["GeneralPhysician", "Pulmonologist"]

# =====================================================
# MEDICINE SANITIZER
# =====================================================


# =====================================================
# MERGE SPECIALIST OPINIONS
# =====================================================
def merge_specialists(opinions: List[Dict]) -> Dict:
    impressions, nurse_actions, escalation, medicines = [], [], [], []

    for op in opinions:
        impressions.append(op["impression"])
        nurse_actions.extend(op["nurse_actions"])
        escalation.extend(op["escalation"])
        medicines.extend(op["medicines"])

    def dedupe(items):
        seen, out = set(), []
        for x in items:
            k = x.lower()
            if k not in seen:
                out.append(x)
                seen.add(k)
        return out

    return {
        "condition_summary": " ".join(impressions[:3]),
        "possible_causes": dedupe(impressions),
        "nurse_actions": dedupe(nurse_actions),
        "escalation_criteria": dedupe(escalation),
        "medicines_advised": dedupe(medicines)
    }

# =====================================================
# MDT AGENT (SBERT)
# =====================================================
class MDTAgentGroup:
    def __init__(self, llm_config=None, src_lang: str = "eng"):
        self.embedder = SentenceTransformer("all-MiniLM-L6-v2")
        self.template_index = self._build_template_index()

    def _build_template_index(self):
        index = {}

        for specialist, rules in MDT_RULES.items():
            index[specialist] = []
            for key, tpl in rules.items():
                text = tpl.get("description", tpl["impression"])
                emb = self.embedder.encode(text, normalize_embeddings=True)
                index[specialist].append({
                    "id": key,
                    "embedding": emb,
                    "template": tpl
                })

        return index

    def _select_template(self, specialist: str, case_text: str) -> Dict:
        case_emb = self.embedder.encode(case_text, normalize_embeddings=True)

        best_score = -1.0
        best_tpl = None

        for item in self.template_index[specialist]:
            score = float(np.dot(case_emb, item["embedding"]))
            if score > best_score:
                best_score = score
                best_tpl = item["template"]

        if best_score < SIMILARITY_THRESHOLD:
            return MDT_RULES[specialist]["general"]

        return best_tpl

    def run_interactive_case(
        self,
        case_text: str,
        vitals: Dict = None,
        rag_snippets: List[Dict] = None
    ) -> Dict:

        vitals = vitals or {}
        rag_snippets = rag_snippets or []

        specialists = select_specialists(case_text, vitals)

        mini_opinions = []
        templates_used = []

        for sp in specialists:
            tpl = self._select_template(sp, case_text)
            templates_used.append(f"{sp}:{tpl.get('id','general')}")

            mini_opinions.append({
                "specialist": sp,
                "impression": tpl["impression"],
                "nurse_actions": tpl["nurse_actions"],
                "escalation": tpl["escalation"],
                "medicines": tpl["medicines"]
            })

        merged = merge_specialists(mini_opinions)

        for snip in rag_snippets[:2]:
            merged["nurse_actions"].append(
                f"{snip['text']} (Guideline reference)"
            )

        summary_text = (
            f"CONDITION SUMMARY:\n{merged['condition_summary']}\n\n"
            f"POSSIBLE CAUSES:\n" +
            "\n".join(f"• {x}" for x in merged["possible_causes"]) + "\n\n"
            f"NURSE ACTIONS:\n" +
            "\n".join(f"• {x}" for x in merged["nurse_actions"]) + "\n\n"
            f"ESCALATION CRITERIA:\n" +
            "\n".join(f"• {x}" for x in merged["escalation_criteria"]) + "\n\n"
            f"MEDICINES ADVISED:\n" +
            "\n".join(f"• {x}" for x in merged["medicines_advised"])
        )

        return {
            "symptoms": [],
            "specialists": specialists,
            "discussion_text": "",
            "mdt_summary_raw": summary_text,
            "medicines": merged["medicines_advised"],
            "meta": {
                "templates_used": templates_used,
                "specialist_count": len(specialists)
            }
        }
