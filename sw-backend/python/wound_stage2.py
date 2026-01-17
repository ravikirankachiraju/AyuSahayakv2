# =========================================
# wound_stage2.py — Structured Wound Report Generator
# =========================================
import sys, json, os
sys.stdout.reconfigure(encoding='utf-8')

from dotenv import load_dotenv
import google.generativeai as genai

from wound_report_engine import score_diseases, build_report

# --------------------------------------------
# ENV SETUP
# --------------------------------------------
load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
gemini = genai.GenerativeModel("gemini-2.5-flash")

# --------------------------------------------
# INPUT PARSING
# --------------------------------------------
if len(sys.argv) < 2:
    print(json.dumps({"error": "No JSON input"}))
    sys.exit(1)

try:
    data = json.loads(sys.argv[1])
except Exception as e:
    print(json.dumps({"error": f"Invalid JSON: {e}"}))
    sys.exit(1)

top3 = data.get("top3_classes", [])
qs = data.get("questions", [])
ans = data.get("answers", [])
rag_summary = data.get("rag_summary", "")

# --------------------------------------------
# 1️⃣ SBERT SCORING → BEST DIAGNOSIS
# --------------------------------------------
scores = score_diseases(top3, qs, ans)
final_diagnosis = max(scores, key=scores.get)

# --------------------------------------------
# 2️⃣ EXTRACT STRUCTURED REPORT FIELDS
# --------------------------------------------
report = build_report(final_diagnosis, rag_summary)

# --------------------------------------------
# 3️⃣ LLM REWRITES FOR NURSE-FRIENDLINESS
# --------------------------------------------
rewrite_prompt = f"""
You are NOT allowed to make medical decisions.

Your ONLY task is to simplify the wording of the report written by our backend.
You must NOT:
- Change the diagnosis
- Add or remove symptoms
- Add medicines or modify medicines
- Add reasoning or remove reasoning
- Add red flags or modify red flags
- Invent missing data

You MUST rewrite each section using the same meaning and same content.
If a section is empty, keep it empty.

Rewrite using the EXACT SAME STRUCTURE:

### Diagnosis
{report['final_diagnosis']}

### Reasoning
{report['clinical_reasoning']}

### Recommended Action
{report['recommended_action']}

### Medicines
{report['medicines']}

### Red Flags
{report['red_flags']}

### Disclaimer
{report['disclaimer']}

Rewrite using shorter, simpler, nurse-friendly sentences.
Do NOT change any facts.
"""


try:
    rewritten = gemini.generate_content(rewrite_prompt).text.strip()
except Exception as e:
    rewritten = f"Error generating report: {e}"

print(json.dumps({"final_report": rewritten}, ensure_ascii=False))
