// backend/routes/patient_ai.js
console.log("🔥 patient_ai.js LOADED");

const express = require("express");
const Patient = require("../models/Patient");
const Consultation = require("../models/Consultation");
const router = express.Router();

/**
 * SAVE SKINCARE AI RESULT
 * POST /patients/save-skincare
 */
router.post("/save-skincare", async (req, res) => {
  try {
    const { patient_ref,consultation_ref, skin_result } = req.body;

    if (!patient_ref || !skin_result) {
      return res.status(400).json({ error: "Missing required fields" });
    }

    const updated = await Patient.findOneAndUpdate(
      { patientId: patient_ref },
      { skinCareAI: skin_result },
      { new: true }
    );

    // ALSO SAVE AI INTO CONSULTATION 
if (consultation_ref) {
  await Consultation.findOneAndUpdate(
    { consultationId: consultation_ref },
    {
      aiSummary: {
        type: "skin",
        ...skin_result,
        generatedAt: new Date()
      }
    }
  );
}


    if (!updated) {
      return res.status(404).json({ error: "Patient not found" });
    }

    return res.json({ success: true, patient: updated });
  } catch (err) {
    console.error("SAVE SKINCARE ERROR:", err);
    return res.status(500).json({ error: "Internal Server Error" });
  }
});

/**
 * SAVE WOUNDCARE AI RESULT
 * POST /patients/save-woundcare
 */
router.post("/save-woundcare", async (req, res) => {
  try {
    const { patient_ref, consultation_ref,wound_result } = req.body;

    if (!patient_ref || !wound_result) {
      return res.status(400).json({ error: "Missing required fields" });
    }

    const updated = await Patient.findOneAndUpdate(
      { patientId: patient_ref },
      { woundCareAI: wound_result },
      { new: true }
    );

    // ALSO SAVE AI INTO CONSULTATION 
if (consultation_ref) {
  await Consultation.findOneAndUpdate(
    { consultationId: consultation_ref },
    {
      aiSummary: {
        type: "wound",
        ...wound_result,
        generatedAt: new Date()
      }
    }
  );
}


    if (!updated) {
      return res.status(404).json({ error: "Patient not found" });
    }

    return res.json({ success: true, patient: updated });
  } catch (err) {
    console.error("SAVE WOUNDCARE ERROR:", err);
    return res.status(500).json({ error: "Internal Server Error" });
  }
});

module.exports = router;
