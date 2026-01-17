# backend/adapter.py

class GeminiAdapter:
    """Wraps a function to provide a .generate_reply method."""
    
    # ✅ Global guardrail system prompt injected before every Gemini call
    GUARDRAIL_SYSTEM_PROMPT = {
        "role": "system",
        "content": """
You are AyuSahayak, a safe medical triage AI.

STRICT RULES (MUST FOLLOW):
1. You may freely accept any clarification or update about existing symptoms (severity, change, worsening, improvement, timing, side, pattern, triggers). These MUST NOT trigger warnings.
2. Do NOT invent symptoms, vitals, tests, or measurements.
3. Medicines allowed ONLY as names — NO dosage (mg/ml), NO frequency, NO "take/buy/use".
4. No unrelated conversation until assessment ends.
5. No restarting or changing the case flow.
6. No hallucinated context or self-created problems.
7. If unsure, reply: “⚠️ I need more information to answer safely.”
8. Keep answers directly relevant to the nurse's question.

These rules override all other behaviors.
"""
    }

    def __init__(self, llm_callable):
        if not callable(llm_callable):
            raise ValueError("llm_callable must be callable")
        self._llm_callable = llm_callable

    def generate_reply(self, messages):
        safe_messages = [self.GUARDRAIL_SYSTEM_PROMPT] + messages
        return self._llm_callable(safe_messages)
