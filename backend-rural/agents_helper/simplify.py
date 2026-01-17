# agents_helper/simplify.py

import re


class GeminiSimplify:
    """
    This class provides a uniform simplification interface for both PCP and MDT.
    It expects an external LLM generate function (adapter) passed during initialization.
    """

    def __init__(self, llm_generate_fn):
        """
        llm_generate_fn → a callable like adapter.generate_reply(messages)
        """
        self.llm_generate = llm_generate_fn

    # ------------------------------------------------------------
    # Main method
    # ------------------------------------------------------------
    def simplify_text(self, medical_text: str, mode: str = "pcp") -> str:

        if mode == "pcp":
            prompt = self._pcp_prompt(medical_text)

        elif mode == "mdt":
            prompt = self._mdt_prompt(medical_text)

        else:
            raise ValueError("Unknown simplify mode")

        messages = [
            {"role": "user", "content": prompt}
        ]

        response = self.llm_generate(messages)
        return self._clean_response(response)

    # ------------------------------------------------------------
    # PCP PROMPT
    # ------------------------------------------------------------
    def _pcp_prompt(self, text: str) -> str:
        return f"""
You are a STRICT medical text simplification engine.

YOUR TASK:
- Simplify the text ONLY.
- DO NOT ask questions.
- DO NOT add advice, follow-ups, or conversational text.
- DO NOT add explanations outside the required sections.

MANDATORY FORMAT RULES:
1. KEEP ALL HEADINGS EXACTLY THE SAME:
   CONDITION SUMMARY
   POSSIBLE CAUSES
   NURSE ACTIONS
   ESCALATION CRITERIA
   MEDICINES ADVISED

2. Output MUST END after the last line under "MEDICINES ADVISED".
3. Any text after that makes the answer INVALID.

Here is the text to simplify:

{text}

FINAL OUTPUT:
(Only the 5 sections. Nothing else.)
""".strip()

    # ------------------------------------------------------------
    # MDT PROMPT
    # ------------------------------------------------------------
    def _mdt_prompt(self, text: str) -> str:
        return f"""
You are a STRICT MDT-to-PCP summarization engine.

TA
- Convert MDT discussion into a nurse-friendly summary.
- DO NOT continue the conversation.
- DO NOT ask questions.
- DO NOT add suggestions outside the format.

FINAL OUTPUT MUST USE EXACTLY THESE SECTIONS:

CONDITION SUMMARY:
POSSIBLE CAUSES:
NURSE ACTIONS:
ESCALATION CRITERIA:
MEDICINES ADVISED:

RULES:
- Output must STOP after "MEDICINES ADVISED".
- Any additional text makes the output INVALID.
- Use short, factual sentences only.

MDT INPUT:
{text}

FINAL OUTPUT:
(Exactly 5 sections. Nothing else.)
""".strip()

    # ------------------------------------------------------------
    # Clean LLM output
    # ------------------------------------------------------------
    def _clean_response(self, resp: str) -> str:
        if not isinstance(resp, str):
            resp = getattr(resp, "text", "") or str(resp)

        # Remove markdown fences
        resp = resp.replace("```", "").strip()

        # Normalize spacing
        resp = re.sub(r"\n{3,}", "\n\n", resp)

        # HARD STOP after MEDICINES ADVISED section
        marker = "MEDICINES ADVISED"
        if marker in resp:
            idx = resp.find(marker)
            resp = resp[: idx + len(marker)]

        print("SIMPLIFIED RESPONSE:", resp)
        return resp.strip()
