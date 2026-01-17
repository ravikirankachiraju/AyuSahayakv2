# backend/gemini_llm_wrapper_mdt.py
# Clean Gemini wrapper ONLY for MDT specialists (no guardrails, no triage)


import time
import google.generativeai as genai
from google.api_core.exceptions import GoogleAPIError


class GeminiMDTWrapper:
    """Wrapper for MDT-only responses without triage behaviour."""

    def __init__(self, api_key: str, model: str = "gemini-2.5-flash"):
        try:
            genai.configure(api_key=api_key)
            self.model = genai.GenerativeModel(model)
            print(f"✅ Gemini MDT Wrapper initialized: {model}")
        except Exception as e:
            print(f"❌ Gemini MDT init failed: {e}")
            raise

    def generate_reply(self, messages: list, retries: int = 2, **kwargs) -> str:
        """Generate a clean reply for MDT roundtable discussions."""

        # Build a simple chat-like prompt (NO guardrails)
        prompt = ""
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            if role == "system":
                prompt += f"System: {content}\n"
            elif role == "assistant":
                prompt += f"Assistant: {content}\n"
            else:
                prompt += f"User: {content}\n"

        attempt = 0
        while attempt <= retries:
            try:
                response = self.model.generate_content(
                    prompt,
                    generation_config=genai.GenerationConfig(
                        temperature=kwargs.get("temperature", 0.4),
                        max_output_tokens=kwargs.get("max_tokens", 2048),
                    ),
                    safety_settings=[
                        {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"}
                    ],
                )

                # Prefer clean .text
                if hasattr(response, "text") and response.text:
                    return response.text.strip()

                # Fallback: read candidate parts
                if hasattr(response, "candidates") and response.candidates:
                    cand = response.candidates[0]
                    if hasattr(cand, "content") and hasattr(cand.content, "parts"):
                        parts = cand.content.parts
                        combined = " ".join([p.text for p in parts if hasattr(p, "text")])
                        if combined.strip():
                            return combined.strip()

                raise ValueError("Empty MDT response")

            except Exception as e:
                attempt += 1
                print(f"⚠️ MDT Gemini attempt {attempt} failed: {e}")
                if attempt <= retries:
                    time.sleep(0.5)
                else:
                    return "[MDT] Unable to produce response."

        return "[MDT] No valid response."
