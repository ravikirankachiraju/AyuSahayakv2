# backend/agents/low.py

from agents.pcp_agent import build_plan

class DeterministicPCP:
    def __init__(self, rag_store):
        self.rag_store = rag_store

    def generate_reply(self, patient_text: str, vitals: dict = None):
        vitals = vitals or {}
        plan = build_plan(patient_text, vitals, self.rag_store)
        print("🧠 PCP INPUT TEXT:", patient_text)
        print("🧠 PCP PLAN OUTPUT:", plan)


        if "error" in plan:
            text = (
                "CONDITION SUMMARY:\nEscalation required.\n\n"
                "POSSIBLE CAUSES:\nUnable to safely assess.\n\n"
                "NURSE ACTIONS:\n• Keep patient stable.\n\n"
                "ESCALATION CRITERIA:\n• Immediate medical review.\n\n"
                "MEDICINES ADVISED:\nNone"
            )
            return {"advice": text, "pcp_full": text, "medicines": []}

        def fmt(lst): return "\n".join(f"• {x}" for x in lst)

        text = (
            f"CONDITION SUMMARY:\n{plan['condition_summary']}\n\n"
            f"POSSIBLE CAUSES:\n{fmt(plan['possible_causes'])}\n\n"
            f"NURSE ACTIONS:\n{fmt(plan['nurse_actions'])}\n\n"
            f"ESCALATION CRITERIA:\n{fmt(plan['escalation_criteria'])}\n\n"
            f"MEDICINES ADVISED:\n{fmt(plan['medicines_advised'])}"
        )

        return {"advice": text, "pcp_full": text, "medicines": plan["medicines_advised"]}
