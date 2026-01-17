from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from modules.routing_pipeline import RoutingPipeline
from gemini_llm_wrapper import GeminiLLMWrapper
from adapter import GeminiAdapter
from dotenv import load_dotenv
import os
import uuid
from pydantic import BaseModel
from typing import Dict, List, Optional
import re
import json
import traceback
from answer_guardrail import SemanticAnswerGuardrail

load_dotenv()

app = FastAPI(title="Ayu MDT Backend - Interactive")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ✅ LLM Setup
try:
    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY not found in environment variables.")

    gemini_llm = GeminiLLMWrapper(api_key=api_key)
    llm_adapter = GeminiAdapter(gemini_llm.generate_reply)
    router = RoutingPipeline(external_llm_generate=llm_adapter.generate_reply)
    print("✅ Backend Initialized Successfully.")
except Exception as e:
    print(f"❌ CRITICAL ERROR during backend initialization: {e}")
    router = None

# Try to import/instantiate the simplifier (used for final clean PCP/MDT simplification)
try:
    from agents_helper.simplify import GeminiSimplify
    simplifier = GeminiSimplify(llm_adapter.generate_reply)
except Exception as e:
    simplifier = None
    print(f"⚠️ Could not initialize GeminiSimplify: {e}")

# ✅ Session Store
SESSION_STORE: Dict[str, dict] = {}

# ✅ Symptom Keywords for extraction
SYMPTOM_LEXICON = {
    "fever", "cough", "pain", "vomit", "vomiting", "nausea",
    "breath", "breathing", "rash", "headache", "fatigue",
    "weakness", "diarrhea", "cold"
}

# ✅ Helpers
def contains_medicine_dosage(text: str) -> bool:
    patterns = [
        r"\b\d+\s?mg\b",
        r"\b\d+\s?ml\b",
        r"\b\d+\s?mg\/kg\b",
        r"\b\d+\s?(?:times|x)\s?(?:a\s)?day\b",
        r"\btwice\s?a\s?day\b",
        r"\bthrice\s?a\s?day\b",
        r"\bevery\s?\d+\s?(?:hours|hrs|h)\b",
    ]
    return any(re.search(p, text.lower()) for p in patterns)

def rephrase_question_for_nurse(question: str) -> str:
    """
    Gemini-powered rephrasing with STRICT validation.
    Guarantees:
    - Complete question
    - No truncation
    - No empty / broken output
    - Always falls back to original if unsafe
    """

    prompt = f"""
You are a medical communication assistant for rural nurses.

TASK:
Rephrase the medical question below so that:
- It is ONE complete sentence
- It ends with a question mark (?)
- It is easy for patients to understand
- Medical meaning is EXACTLY the same
- Do NOT shorten
- Do NOT truncate
- Do NOT add or remove symptoms
- Do NOT explain, only ask

Original question:
{question}

Return ONLY the rephrased question.
"""

    try:
        raw = gemini_llm.generate_reply(
            [{"role": "user", "content": prompt}],
            temperature=0.2,
            max_tokens=120
        )

        if not raw:
            raise ValueError("Empty Gemini response")

        text = raw.strip().strip('"').strip()

        # -------------------------
        # 🔒 HARD VALIDATION RULES
        # -------------------------
        invalid = False

        if len(text) < 12:
            invalid = True

        if not text.endswith("?"):
            invalid = True

        if text.count("?") > 1:
            invalid = True

        if any(bad in text.lower() for bad in [
            "as an ai",
            "i think",
            "this question",
            "the patient",
            "explain",
        ]):
            invalid = True

        if invalid:
            print("⚠️ [Gemini Rephrase] INVALID OUTPUT")
            print("Original :", question)
            print("Gemini   :", text)
            return question  # 🔁 SAFE FALLBACK

        return text

    except Exception as e:
        print("⚠️ [Gemini Rephrase] Exception:", e)
        return question



def sanitize_medicine_output(text: str) -> str:
    if contains_medicine_dosage(text):
        return "Seek a clinical evaluation for safe medication use."
    return text

def extract_original_symptoms(text: str):
    text_l = text.lower()
    return {s for s in SYMPTOM_LEXICON if s in text_l}

# ✅ Robust JSON extractor for Gemini responses
def _safe_load_json(raw) -> dict:
    if not isinstance(raw, str):
        raw = getattr(raw, "text", None) or str(raw)

    cleaned = raw.strip().strip("`").strip()
    m = re.search(r"\{.*?\}\s*$", cleaned, flags=re.DOTALL)
    candidate = m.group(0) if m else cleaned
    try:
        return json.loads(candidate)
    except:
        m2 = re.search(r"\{.*?\}", cleaned, flags=re.DOTALL)
        if m2:
            try:
                return json.loads(m2.group(0))
            except:
                pass
    return {}

# -------------------------
# SECTION PARSING UTILITIES
# -------------------------
HEADINGS = [
    "CONDITION SUMMARY",
    "POSSIBLE CAUSES",
    "NURSE ACTIONS",
    "ESCALATION CRITERIA",
    "MEDICINES ADVISED"
]

_heading_pattern = re.compile(
    r"(?P<h>CONDITION SUMMARY|POSSIBLE CAUSES|NURSE ACTIONS|ESCALATION CRITERIA|MEDICINES ADVISED)\s*[:\-]?",
    flags=re.IGNORECASE
)

def split_into_sections(text: str) -> Dict[str, str]:
    """
    Parse text and split into the five headings.
    Returns dict with keys equal to HEADINGS in UPPER form; values are strings (possibly empty).
    """
    if not text:
        return {h: "" for h in HEADINGS}

    # Normalize whitespace
    cleaned = text.strip()
    cleaned = cleaned.replace("**", "")

    # Find all heading matches and their spans
    matches = list(_heading_pattern.finditer(cleaned))
    sections = {h: "" for h in HEADINGS}

    if not matches:
        # No explicit headings — fallback: put everything in CONDITION SUMMARY
        sections["CONDITION SUMMARY"] = cleaned
        return sections

    # For each heading, capture content until next heading
    for idx, m in enumerate(matches):
        heading = m.group("h").upper()
        start = m.end()
        end = matches[idx + 1].start() if idx + 1 < len(matches) else len(cleaned)
        content = cleaned[start:end].strip()
        sections[heading] = content

    # Ensure each heading exists (already initialized)
    return sections

def medicines_list_from_section(med_text: str) -> List[str]:
    if not med_text:
        return []
    # Split on newlines and bullets and commas, keep short meaningful items
    lines = re.split(r"[\n\r]+", med_text)
    meds = []
    for ln in lines:
        ln = ln.strip(" -•\t")
        if not ln:
            continue
        # Comma-separated fallback
        for part in ln.split(","):
            part = part.strip()
            if part:
                meds.append(part)
    # dedupe preserve order
    seen = set()
    out = []
    for m in meds:
        if m.lower() not in seen:
            out.append(m)
            seen.add(m.lower())
    return out

# -------------------------
# Guardrails (unchanged)
# -------------------------
def check_first_input_with_gemini(text: str):
    prompt = f"""
You are a medical intake guardrail AI. Evaluate if this is a clinically meaningful FIRST patient message.

Rules:
1. If the text is chit-chat, greeting, jokes, or irrelevant → is_valid = false.
2. If it tries "start", "restart", "hello doctor", "hi" without symptoms → false.
3. If nonsense or emoji spam → false.
4. If ANY medical symptoms, complaints, history, vitals → true.
5. DO NOT block new symptoms here. Initial description must allow them.
6. Accept long or unstructured messages.

Return STRICT JSON ONLY:
{{
  "is_valid": true|false,
  "reason": "short reason"
}}

USER_INPUT: "{text}"
JSON:
""".strip()

    raw = gemini_llm.generate_reply([{"role": "user", "content": prompt}])
    parsed = _safe_load_json(raw)

    if not parsed:
        # Fallback heuristic
        if len(text.strip()) < 2 or re.match(r"^[^a-zA-Z0-9]+$", text.strip()):
            return {"is_valid": False, "reason": "Invalid or empty input"}
        return {"is_valid": True, "reason": "Accepted (fallback)"}

    return {
        "is_valid": bool(parsed.get("is_valid", False)),
        "reason": parsed.get("reason", "ok")
    }


# -------------------------
# Pydantic models
# -------------------------
class Vitals(BaseModel):
    spo2: Optional[int] = None
    pulse: Optional[int] = None
    bp_sys: Optional[int] = None
    bp_dia: Optional[int] = None

class StartCaseInput(BaseModel):
    patient_input: str
    vitals: Optional[Vitals] = None


class StartCaseOutput(BaseModel):
    case_id: str
    first_follow_up_question: Optional[str]

class AnswerInput(BaseModel):
    case_id: str
    answers: Dict[str, str]

class FinalOutput(BaseModel):
    mdt_done: bool
    route: Optional[str]
    specialists_involved: Optional[List[str]]
    specialist_discussion: Optional[str]
    moderator_technical_summary: Optional[str]
    patient_friendly_advice: Optional[str]
    symptoms: Optional[List[str]]
    possible_diseases: Optional[List[str]]
    medicines_advised: Optional[List[str]]
    status: Optional[str]
    final_summary_raw: Optional[Dict[str, str]]
    final_summary_simplified: Optional[Dict[str, object]]

# -------------------------
# Health
# -------------------------
@app.get("/health")
def health():
    return {"ok": True}

# -------------------------
# Start case
# -------------------------
@app.post("/api/start_case", response_model=StartCaseOutput)
async def start_case(payload: StartCaseInput):

    if not router:
        raise HTTPException(503, "AI unavailable")

    patient_input = payload.patient_input.strip()

    # ✅ GEMINI FIRST INPUT GUARDRAIL
    guard = check_first_input_with_gemini(patient_input)
    if not guard.get("is_valid"):
        raise HTTPException(400, f"⚠️ Invalid first input: {guard['reason']}")

    case_id = str(uuid.uuid4())[:8].upper()

    SESSION_STORE[case_id] = {
        "initial_text": patient_input,
        "questions": [],
        "answers": {},
        "current_round": 0,
        "max_rounds": 5,
        "mdt_done": False,
        "original_symptoms": extract_original_symptoms(patient_input),
        "vitals": payload.vitals.dict() if payload.vitals else {}

    }

    collected, questions = router.collector.clarification_loop_api(
    initial_input=patient_input
)
    
    print("\n🩺 [START_CASE] Patient input received:")
    print(payload.patient_input)
    
    if payload.vitals:
        print("🩺 [START_CASE] Patient vitals received:")
        print(payload.vitals.dict())
    else:
        print("🩺 [START_CASE] No vitals provided")
  


    first_q = questions[0] if questions else None
    if first_q:
        SESSION_STORE[case_id]["questions"].append(first_q)

    return {"case_id": case_id, "first_follow_up_question": first_q}

# -------------------------
# Next question
# -------------------------
@app.post("/api/next_question")
async def next_question(payload: AnswerInput):

    case_id = payload.case_id
    answers = payload.answers or {}

    session = SESSION_STORE.get(case_id)
    if not session:
        return {"done": False, "next_question": None, "warning": "⚠️ Invalid case."}

    if session["mdt_done"]:
        return {"done": True, "next_question": None}

    if not session["questions"]:
        return {"done": False, "next_question": None, "warning": "⚠️ No active question."}

    # 🔹 ORIGINAL (internal) question
    current_q = session["questions"][-1]
    print("\n📦 [API] Current stored question:")
    print(current_q)
    print("--------------------------------------------------")

    # 🔹 User answer
    user_answer = answers.get(current_q) or next(iter(answers.values()), None)
    if not user_answer:
        # return FRIENDLY version of same question
        return {
            "done": False,
            "next_question": rephrase_question_for_nurse(current_q),
            "warning": "⚠️ Please answer the question"
        }

    # ✅ Guardrail check (uses ORIGINAL question)
    answer_guard = SemanticAnswerGuardrail()
    guard = answer_guard.validate(current_q, user_answer)

    if not guard["is_valid"]:
        return {
            "done": False,
            "next_question": rephrase_question_for_nurse(current_q),
            "warning": f"⚠️ {guard['reason']}"
        }

    # ✅ Save valid answer
    session["answers"][current_q] = user_answer
    session["initial_text"] += f" | {current_q}: {user_answer}"
    session["current_round"] += 1

    if session["current_round"] >= session["max_rounds"]:
        session["mdt_done"] = True
        return {"done": True, "next_question": None}

    # 🔹 Get NEXT clinical question (SBERT logic)
    done, next_q, updated = router.collector.generate_next_question_api(
        collected_context=session["initial_text"],
        new_answers={},
        asked_questions=session["questions"],
        confidence_threshold=70
    )

    session["initial_text"] = updated

    if not next_q or done:
        session["mdt_done"] = True
        return {"done": True, "next_question": None}

    # 🔹 Store ORIGINAL question internally
    session["questions"].append(next_q)

    # 🔹 Send FRIENDLY version to frontend
    friendly_q = rephrase_question_for_nurse(next_q)
    print("\n [API] FRIENDLY question sent to frontend:")
    print(friendly_q)
    print("==================================================")


    return {
        "done": False,
        "next_question": friendly_q
    }


# -------------------------
# Process final answers (REST)
# -------------------------
@app.post("/api/process_final_answers", response_model=FinalOutput)
async def process_final_answers(payload: dict):

    case_id = payload.get("case_id")
    answers = payload.get("answers", {})

    session = SESSION_STORE.get(case_id)
    if not session:
        raise HTTPException(404, "Invalid case_id")

    for q, a in answers.items():
        session["initial_text"] += f" | {q}: {a}"

    collected = session["initial_text"]

    # Shortlist & complexity
    summary = router.shortlister.shortlist(collected)
    summary["vitals"] = session.get("vitals", {})
    complexity = router.complexity.assess(summary)

    # Run route (calls low/medium/high agents inside pipeline)
    final_res = await router.run_route(complexity, collected, summary, case_id)

    # Post-process: produce raw and simplified 5-section summaries (S2)
    try:
        # Defensive extraction of raw text from possible keys
        raw_text_candidates = []
        # low-case keys that might contain raw PCP/MDT content
        for k in ("advice", "advice_full", "pcp_full", "patient_friendly_advice",
                  "final_text", "final_summary_raw", "mdt_summary_raw", "moderator_reply", "discussion_text"):
            v = final_res.get(k)
            if isinstance(v, str) and v.strip():
                raw_text_candidates.append(v.strip())

        # if MDT-style structure present
        specialists = final_res.get("specialists") or final_res.get("specialists_involved") or final_res.get("specialists_involved_list") or []
        discussion_text = final_res.get("discussion_text") or final_res.get("mdt_discussion") or final_res.get("specialist_discussion") or ""

        # Choose the best raw text candidate (prefer mdt_summary_raw if available)
        # Prefer PCP text first
        pcp_raw = (
            final_res.get("pcp_full")
            or final_res.get("advice")
        )
        
        # MDT text (used only for medium cases)
        mdt_raw = (
            final_res.get("mdt_summary_raw")
            or final_res.get("moderator_technical_summary")
        )

        # Always keep MDT transcript available separately
        chosen_raw = pcp_raw or mdt_raw or raw_text_candidates[0] if raw_text_candidates else ""
        
        # Also attach discussion to final result
        final_res["specialist_discussion"] = discussion_text
        
        # If still empty and discussion_text present, use discussion_text
        if not chosen_raw and discussion_text:
            chosen_raw = discussion_text

        # Parse raw into 5 sections (attempt)
        final_summary_raw = split_into_sections(chosen_raw)

        # If medicines are present in final_res separate field, use those for raw
        raw_meds = final_res.get("medicines") or final_res.get("medicines_advised") or final_res.get("medicines_advised_raw") or final_res.get("medicines_advised_list")
        if raw_meds and isinstance(raw_meds, (list, tuple)):
            final_summary_raw["MEDICINES ADVISED"] = "\n".join(raw_meds)

        # Simplify using the simplifier if available
        final_summary_simplified = {h: "" for h in HEADINGS}
        if simplifier:
            # Mode depends on complexity
            if complexity == "low":
                # we want to simplify PCP raw text and keep headings exact
                pcp_raw_text = chosen_raw 
                simplified_text = simplifier.simplify_text(pcp_raw_text, mode="pcp")
                simplified_sections = split_into_sections(simplified_text)
                final_summary_simplified.update(simplified_sections)

            elif complexity == "medium":
                # For MDT: ensure we include specialists context plus moderator raw
                # Build a combined MDT moderator input ensuring specialists are visible
                mdt_input = ""
                if specialists:
                    mdt_input += f"Specialists involved: {', '.join(specialists)}\n\n"
                if chosen_raw:
                    mdt_input += chosen_raw
                else:
                    # fallback: attempt to reconstruct from discussion_text
                    mdt_input += discussion_text or chosen_raw or ""

                simplified_text = simplifier.simplify_text(mdt_input, mode="mdt")
                simplified_sections = split_into_sections(simplified_text)
                final_summary_simplified.update(simplified_sections)

            else:
                # For high or unknown: attempt to simplify whatever we have in PCP mode
                any_text = chosen_raw or "No detailed summary available."
                simplified_text = simplifier.simplify_text(any_text, mode="pcp")
                simplified_sections = split_into_sections(simplified_text)
                final_summary_simplified.update(simplified_sections)
        else:
            # No simplifier available — fall back to raw sections
            final_summary_simplified = final_summary_raw.copy()

        # Convert MEDICINES_ADVISED section text to a list (clean)
        meds_list = medicines_list_from_section(final_summary_simplified.get("MEDICINES ADVISED", "") or final_summary_raw.get("MEDICINES ADVISED", ""))
        final_res["final_summary_raw"] = final_summary_raw
        final_res["final_summary_simplified"] = {
            "CONDITION SUMMARY": final_summary_simplified.get("CONDITION SUMMARY", ""),
            "POSSIBLE CAUSES": final_summary_simplified.get("POSSIBLE CAUSES", ""),
            "NURSE ACTIONS": final_summary_simplified.get("NURSE ACTIONS", ""),
            "ESCALATION CRITERIA": final_summary_simplified.get("ESCALATION CRITERIA", ""),
            "MEDICINES ADVISED": meds_list
        }

        # Ensure top-level standardized fields exist
        final_res["route"] = final_res.get("route") or complexity
        final_res["specialists_involved"] = specialists
        # Only set non-empty discussion
        if discussion_text.strip():
            final_res["specialist_discussion"] = discussion_text
        final_res["moderator_technical_summary"] = final_res.get("moderator_technical_summary") or final_res.get("tech_summary") or (chosen_raw if complexity == "medium" else "")
        final_res["patient_friendly_advice"] = final_res.get("patient_friendly_advice") or final_res.get("advice") or ""
        final_res["symptoms"] = final_res.get("symptoms") or summary.get("symptoms") or []
        final_res["possible_diseases"] = final_res.get("possible_diseases") or summary.get("possible_diseases") or []
        final_res["medicines_advised"] = final_res.get("medicines_advised") or final_res.get("medicines") or meds_list

    except Exception as e:
        # Don't fail the endpoint — return what we have and log
        print("⚠️ Error during final post-processing:", e)
        traceback.print_exc()

    session["mdt_done"] = True

    if final_res.get("patient_friendly_advice"):
        final_res["patient_friendly_advice"] = sanitize_medicine_output(
            final_res["patient_friendly_advice"]
        )

    final_res["status"] = (
        "🧠 Specialists discussion completed."
        if complexity == "medium"
        else "✅ Case processed successfully."
    )

    print("\n===== FINAL OUTPUT (REST API) =====")
    print(json.dumps(final_res, indent=2, ensure_ascii=False))
    print("==================================\n")


    return final_res

# -------------------------
# WEBSOCKET MDT (progress + final)
# -------------------------
# -------------------------
# WEBSOCKET MDT (progress + final)
# -------------------------
@app.websocket("/ws/process_case")
async def process_case_websocket(websocket: WebSocket):
    await websocket.accept()
    try:
        payload = await websocket.receive_json()
        case_id = payload.get("case_id")
        answers = payload.get("answers", {})

        session = SESSION_STORE.get(case_id)
        if not session:
            await websocket.send_json({"type": "error", "message": "Invalid case_id"})
            return

        for q, a in answers.items():
            session["initial_text"] += f" | {q}: {a}"

        collected = session["initial_text"]

        # small helper to send dicts (NO RECURSION)
        async def send(msg: dict):
            await websocket.send_json(msg)

        # -------------------------
        # SHORTLISTING
        # -------------------------
        await send({"type": "progress", "message": "🧠 Shortlisting symptoms..."})

        summary = router.shortlister.shortlist(collected)
        summary["vitals"] = session.get("vitals", {})

        # ⭐ NEW — Send symptoms immediately
        await send({
            "type": "symptoms",
            "symptoms": summary.get("symptoms", [])
        })

        await send({"type": "progress", "message": "✅ Shortlisting done"})

        # -------------------------
        # COMPLEXITY
        # -------------------------
        complexity = router.complexity.assess(summary)
        await send({"type": "progress", "message": f"✅ Complexity: {complexity}"})


        # -------------------------
        # EMERGENCY SHORT-CIRCUIT
        # -------------------------
        if complexity.lower().startswith("high"):
            emergency_summary = {
                "route": "high",
                "status": "🚨 High-Risk Case Identified — Immediate Medical Attention Required",
                "symptoms": summary.get("symptoms", []),
                "specialists_involved": [],
                "specialist_discussion": "",
                "moderator_technical_summary": (
                    "This case has been assessed as HIGH-RISK based on the symptom pattern. "
                    "MDT processing is bypassed to avoid delay. Immediate escalation recommended."
                ),
                "final_summary_simplified": {
                    "CONDITION SUMMARY": (
                        "The patient's symptoms indicate a potentially serious or rapidly progressing condition "
                        "that requires urgent medical evaluation."
                    ),
                    "POSSIBLE CAUSES": (
                        "Severe infection, acute respiratory distress, systemic illness, or other emergencies. "
                        "Exact diagnosis requires clinical examination."
                    ),
                    "NURSE ACTIONS": (
                        "• Stay with the patient and ensure stability.\n"
                        "• Assess airway, breathing, circulation (ABC).\n"
                        "• Monitor vitals: temperature, SpO₂, BP, HR.\n"
                        "• Prepare for urgent escalation to an emergency doctor or unit.\n"
                        "• Keep the patient comfortable and supported."
                    ),
                    "ESCALATION CRITERIA": (
                        "• Difficulty breathing or shortness of breath.\n"
                        "• Chest pain or persistent pressure.\n"
                        "• Confusion, drowsiness, or altered mental state.\n"
                        "• Rapidly worsening symptoms.\n"
                        "• Severe vomiting or dehydration.\n"
                        "• Any major drop in vitals."
                    ),
                    "MEDICINES ADVISED": []
                }
            }

            await websocket.send_json({"type": "final", "result": emergency_summary})
            await websocket.close()
            return

        # -------------------------
        # MDT PIPELINE (ASYNC)
        # -------------------------
        async def progress_cb(m: str):
            await websocket.send_json({"type": "progress", "message": m})

        final_res = await router.run_route(
            complexity,
            collected,
            summary,
            case_id,
            progress_callback=progress_cb,
        )

        # -------------------------
        # POST-PROCESSING (same as REST)
        # -------------------------
        try:
            raw_text_candidates = []
            for k in ("advice", "advice_full", "pcp_full", "patient_friendly_advice",
                      "final_text", "final_summary_raw", "mdt_summary_raw",
                      "moderator_reply", "discussion_text"):
                v = final_res.get(k)
                if isinstance(v, str) and v.strip():
                    raw_text_candidates.append(v.strip())

            specialists = final_res.get("specialists") or final_res.get("specialists_involved") or []
            # Correct: get the actual discussion from MDT engine
            discussion_text = (
                final_res.get("discussion_text")     # always present from MDTAgentGroup
                or final_res.get("specialist_discussion")
                or final_res.get("mdt_discussion")
                or ""
            )


            raw_mdt = final_res.get("mdt_summary_raw") or final_res.get("moderator_technical_summary")
            chosen_raw = raw_mdt or (raw_text_candidates[0] if raw_text_candidates else "")
            if not chosen_raw and discussion_text:
                chosen_raw = discussion_text

            final_summary_raw = split_into_sections(chosen_raw)

            raw_meds = final_res.get("medicines") or final_res.get("medicines_advised") or final_res.get("medicines_advised_list")
            if raw_meds and isinstance(raw_meds, (list, tuple)):
                final_summary_raw["MEDICINES ADVISED"] = "\n".join(raw_meds)

            final_summary_simplified = {h: "" for h in HEADINGS}

            if simplifier:
                if complexity.lower().startswith("low"):
                    simplified = simplifier.simplify_text(chosen_raw, mode="pcp")
                    final_summary_simplified.update(split_into_sections(simplified))

                elif complexity.lower().startswith("medium"):
                    mdt_input = ""
                    if specialists:
                        mdt_input += f"Specialists involved: {', '.join(specialists)}\n\n"
                    mdt_input += chosen_raw or discussion_text or ""
                    simplified = simplifier.simplify_text(mdt_input, mode="mdt")
                    final_summary_simplified.update(split_into_sections(simplified))

                else:
                    simplified = simplifier.simplify_text(chosen_raw or "No summary", mode="pcp")
                    final_summary_simplified.update(split_into_sections(simplified))
            else:
                final_summary_simplified = final_summary_raw.copy()

            meds_list = medicines_list_from_section(
                final_summary_simplified.get("MEDICINES ADVISED", "") or
                final_summary_raw.get("MEDICINES ADVISED", "")
            )

            final_res["final_summary_raw"] = final_summary_raw
            final_res["final_summary_simplified"] = {
                "CONDITION SUMMARY": final_summary_simplified.get("CONDITION SUMMARY", ""),
                "POSSIBLE CAUSES": final_summary_simplified.get("POSSIBLE CAUSES", ""),
                "NURSE ACTIONS": final_summary_simplified.get("NURSE ACTIONS", ""),
                "ESCALATION CRITERIA": final_summary_simplified.get("ESCALATION CRITERIA", ""),
                "MEDICINES ADVISED": meds_list
            }

            final_res["route"] = final_res.get("route") or complexity
            final_res["specialists_involved"] = specialists
            final_res["specialist_discussion"] = discussion_text or ""
            final_res["moderator_technical_summary"] = (
                final_res.get("moderator_technical_summary") or chosen_raw
            )
            final_res["patient_friendly_advice"] = final_res.get("patient_friendly_advice") or ""
            final_res["symptoms"] = final_res.get("symptoms") or summary.get("symptoms") or []
            final_res["possible_diseases"] = final_res.get("possible_diseases") or summary.get("possible_diseases") or []
            final_res["medicines_advised"] = meds_list

        except Exception as e:
            print("⚠️ Error during websocket final post-processing:", e)
            traceback.print_exc()

        if final_res.get("patient_friendly_advice"):
            final_res["patient_friendly_advice"] = sanitize_medicine_output(
                final_res["patient_friendly_advice"]
            )

        print("\n===== FINAL OUTPUT (WEBSOCKET) =====")
        print(json.dumps(final_res, indent=2, ensure_ascii=False))
        print("====================================\n")

        await websocket.send_json({"type": "final", "result": final_res})

    except WebSocketDisconnect:
        print("⚠️ WebSocket disconnected")
    finally:
        try:
            await websocket.close()
        except:
            pass