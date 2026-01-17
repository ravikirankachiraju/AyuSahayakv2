# run_v2.py (FIXED to replicate original detailed printing)

from modules.routing_pipeline import RoutingPipeline

def print_final_report(result_dict: dict):
    """Prints the final structured dictionary output exactly like the original routing_pipeline."""
    
    # --- Start of RESTORED Printing Block ---
    print("\n✅ Routing Complete.\n") # Status message
    print("--- FINAL OUTPUT ---\n")
    print(f"📂 Case ID: {result_dict.get('case_id')}")
    print(f"🕒 Time: {result_dict.get('timestamp')}\n")

    # Symptoms
    if result_dict.get("symptoms"):
        print("🩺 **Symptoms:**") # Note: Use ** for Markdown bold if desired
        for s in result_dict["symptoms"]:
            print(f"- {s}")
    else:
        # Match the original output's wording
        print("🩺 No symptoms identified.") 

    # Possible diseases
    if result_dict.get("possible_diseases"):
        print("\n💊 **Possible Diseases (Verified):**")
        for d in result_dict["possible_diseases"]:
            print(f"- {d}")
    else:
        # Match the original output's wording
        print("\n💊 No reliable disease inference available yet — further testing advised.") 

    # Route & specialists
    print(f"\n🛣️ **Route:** {result_dict.get('route', 'Unknown')}")
    if result_dict.get("specialists_involved"):
        print("\n👩‍⚕️ **Specialists Involved:**")
        for sp in result_dict["specialists_involved"]:
            print(f"- {sp}")

    # Specialist discussion (Only present in Medium cases)
    if result_dict.get("specialist_discussion"):
        print("\n🧠 **Specialist Discussion:**")
        print(result_dict["specialist_discussion"])

    # Moderator summary
    if result_dict.get("moderator_technical_summary"):
        print("\n📋 **Moderator Summary:**") # Using simple bold text
        print(result_dict["moderator_technical_summary"])

    # Patient advice
    if result_dict.get("patient_friendly_advice"):
        print("\n💡 **Patient Advice:**") # Using simple bold text
        print(result_dict["patient_friendly_advice"])

    print("\n✅ End of Report\n")
    # --- End of RESTORED Printing Block ---


if __name__ == "__main__":
    # Take patient input
    patient_input = input("👨‍⚕️ Describe patient (age, gender, main complaints):\n> ")

    # Initialize the router
    router = RoutingPipeline()

    # Process the case and capture the final result dictionary
    # Note: process_case still prints its internal steps (like "Starting pipeline...")
    final_result_dict = router.process_case(patient_input)

    # Print the full, structured report using the dictionary and the restored logic
    print_final_report(final_result_dict)