# agents/high.py

class HighCaseHandler:
    """
    🚨 Handles high-complexity or emergency cases.
    """

    def __init__(self, llm_config=None):
        self.llm_config = llm_config or {}

    def handle(self, symptom_summary: dict) -> str:
        """
        Simple rule-based emergency advice generator, checking raw text for specific threats.
        """
        possible_diseases = symptom_summary.get("possible_diseases", [])
        # CRITICAL FIX: Get the full collected text for direct keyword checking
        raw_text = symptom_summary.get("raw_text", "").lower() 
        
        advice = "⚠️ **EMERGENCY: CRITICAL CASE DETECTED.**\n"

        # 1. ACUTE CHOLANGITIS / SEPSIS (Charcot's Triad)
        # Check for Jaundice/Yellow AND Fever/Chills/High Temp
        is_cholangitis_risk = (
            ("jaundice" in raw_text or "yellow" in raw_text) and 
            ("fever" in raw_text or "102" in raw_text or "chills" in raw_text)
        )
        
        # 2. CARDIAC/PULMONARY THREAT
        is_pulmonary_risk = "shortness of breath" in raw_text or "chest pain" in raw_text

        if is_cholangitis_risk:
            advice += "🚑 **CALL EMERGENCY SERVICES NOW.** This patient displays signs of Acute Cholangitis (Bile Duct Infection), which is life-threatening. Urgent hospital transfer and IV antibiotics are necessary. Do not delay."
        
        elif is_pulmonary_risk:
            advice += "🚑 Possible **Cardiopulmonary Emergency**. Immediate call to emergency services and hospital transfer recommended."
            
        elif any("stroke" in d.lower() for d in possible_diseases):
            advice += "🚑 Possible stroke. Urgent brain imaging and neurologist consultation required."
        
        # Fallback for general sepsis risk, only if a disease was identified
        elif any("sepsis" in d.lower() or "infection" in d.lower() for d in possible_diseases):
            advice += "🧫 Suspected sepsis/infection. Seek hospital care for IV antibiotics immediately."
            
        # 3. DEFAULT HIGH ESCALATION
        else:
            advice += "🏥 Severe or unclear case. Escalate immediately to emergency department for evaluation."

        return advice