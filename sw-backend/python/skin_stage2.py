# skin_stage2.py
import sys, json, os
from dotenv import load_dotenv
import google.generativeai as genai
from report_engine import score_diseases, build_report

load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
gemini = genai.GenerativeModel("gemini-2.5-flash")

data = json.loads(sys.argv[1])

# ---- Weighted scoring ----
sb_scores = score_diseases(data["top3_classes"], data["questions"], data["answers"])  # SBERT similarity
final_scores = {}

for disease, sb_score in sb_scores.items():
    fusion_prob = data["top3_probs"][data["top3_classes"].index(disease)]  # from Stage-1
    final_scores[disease] = (fusion_prob * 0.7) + (sb_score * 0.3)

final_diagnosis = max(final_scores, key=final_scores.get)


report = build_report(final_diagnosis, data["rag_summary"])

rewrite_prompt = f"""
Rewrite this report in simple nurse-friendly language.
Do NOT add or remove medical details.
Do NOT change medicines or diagnosis.

Diagnosis: {report['final_diagnosis']}
Reasoning: {report['clinical_reasoning']}
Recommended Action: {report['recommended_action']}
Red Flags: {report['red_flags']}
Medicines: {report['medicines']}
Disclaimer: {report['disclaimer']}
"""

final_text = gemini.generate_content(rewrite_prompt).text.strip()
print(json.dumps({"final_report": final_text}, ensure_ascii=False))
