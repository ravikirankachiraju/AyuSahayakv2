# =========================================
# WOUND_QUESTION_BANK.py (Perfectly aligned with model classes)
# =========================================

WOUND_QUESTION_BANK = {
    "Abrasions": [
        {
            "id": "abr_q1",
            "canonical": "Is only the top skin layer scraped with mild bleeding or redness?",
            "feature_phrases": [
                "scraped skin",
                "mild bleeding",
                "surface level wound",
                "red raw skin"
            ]
        }
    ],

    "Bruises": [
        {
            "id": "bruise_q1",
            "canonical": "Is the skin blue or purple without any open cut?",
            "feature_phrases": [
                "blue skin",
                "purple discoloration",
                "no open wound"
            ]
        }
    ],

    "Burns": [
        {
            "id": "burn_q1",
            "canonical": "Are there blisters or redness that appear due to heat exposure?",
            "feature_phrases": [
                "blistering",
                "heat burn",
                "red painful skin"
            ]
        }
    ],

    "Cut": [
        {
            "id": "cut_q1",
            "canonical": "Is the wound caused by a sharp object with mild bleeding?",
            "feature_phrases": [
                "open wound",
                "bleeding cut",
                "sharp injury"
            ]
        }
    ],

    "Diabetic Wounds": [
        {
            "id": "dia_q1",
            "canonical": "Is the wound slow to heal with black tissue or a foul smell?",
            "feature_phrases": [
                "slow healing",
                "necrotic tissue",
                "foul odor"
            ]
        }
    ],

    # ⚠️ MUST match your model spelling "Laseration"
    "Laseration": [
        {
            "id": "lac_q1",
            "canonical": "Is the wound deep with irregular edges or visible tissue?",
            "feature_phrases": [
                "deep cut",
                "irregular edges",
                "visible tissue"
            ]
        }
    ],

    "Normal": [
        {
            "id": "norm_q1",
            "canonical": "Is the skin intact with no visible wound or discoloration?",
            "feature_phrases": [
                "healthy skin",
                "no wound",
                "no redness"
            ]
        }
    ],

    "Pressure Wounds": [
        {
            "id": "pw_q1",
            "canonical": "Is the wound over a bony area like the heel or hip and getting deeper?",
            "feature_phrases": [
                "pressure sore",
                "bony areas",
                "deep crater"
            ]
        }
    ],

    "Surgical Wounds": [
        {
            "id": "sw_q1",
            "canonical": "Is the wound from a surgical incision with redness or discharge?",
            "feature_phrases": [
                "surgical incision",
                "post-operative redness",
                "wound discharge"
            ]
        }
    ],

    "Venous Wounds": [
        {
            "id": "vw_q1",
            "canonical": "Is the wound near the ankle with swelling or dark brown patches?",
            "feature_phrases": [
                "ankle ulcer",
                "leg swelling",
                "brown discoloration"
            ]
        }
    ]
}
