import time
import google.generativeai as genai
from google.api_core.exceptions import GoogleAPIError

class GeminiLLMWrapper:
    """
    Updated for January 2026 stable models.
    Model 'gemini-2.5-flash-lite' offers the highest free quota (1,000 RPD).
    """

    def __init__(self, api_key: str, model: str = "gemini-2.5-flash-lite"):
        try:
            genai.configure(api_key=api_key)
            
            # Use the official system_instruction parameter
            system_prompt = "You are a helpful assistant. Respond clearly and concisely."
            
            self.model = genai.GenerativeModel(
                model_name=model,
                system_instruction=system_prompt
            )
            print(f"✅ Gemini LLM Wrapper initialized: {model}")
        except Exception as e:
            print(f"❌ Failed to initialize Gemini: {e}")
            raise

    def generate_reply(self, messages: list, retries: int = 1, **kwargs) -> str:
        # Gemini 2.5+ expects a specific 'role' mapping
        gemini_messages = []
        for m in messages:
            role = "user" if m.get("role") == "user" else "model"
            gemini_messages.append({"role": role, "parts": [m.get("content", "")]})

        attempt = 0
        while attempt <= retries:
            try:
                response = self.model.generate_content(
                    gemini_messages,
                    generation_config=genai.GenerationConfig(
                        temperature=kwargs.get("temperature", 0.3),
                        max_output_tokens=kwargs.get("max_tokens", 512),
                    ),
                    safety_settings=[
                        {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
                        {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
                        {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
                        {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
                    ]
                )

                if response.text:
                    return response.text.strip()
                
                raise ValueError("Response empty or blocked")

            except Exception as e:
                attempt += 1
                error_msg = str(e)
                
                # If you hit the 429 quota error, we wait longer
                if "429" in error_msg:
                    print(f"⚠️ Rate limit hit. Waiting 5s... (Attempt {attempt})")
                    time.sleep(5.0)
                else:
                    print(f"⚠️ Gemini error: {error_msg}")
                
                if attempt <= retries:
                    continue
                return ""

        return ""