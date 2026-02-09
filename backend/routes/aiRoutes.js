const router = require("express").Router();
const Patient = require("../models/Patient");
const { authenticate } = require("../middleware/authMiddleware");
const { authorize } = require("../middleware/roleMiddleware");

router.post("/save_case", authenticate, authorize("nurse"), async (req, res) => {
  try {
    const {
      patient_ref,
      case_id,
      symptoms,
      classification,
      summary,
      specialists,
      escalation_reason,
      timestamp
    } = req.body;

    console.log("Incoming save request:", req.body);

    // Normalize classification
    let cleanClass = String(classification || "").toLowerCase();
    if (cleanClass.includes("low")) cleanClass = "low";
    else if (cleanClass.includes("medium")) cleanClass = "medium";
    else if (cleanClass.includes("high")) cleanClass = "high";

    // Find patient by patientId + hospitalId
    const patient = await Patient.findOne({
      patientId: patient_ref,
      hospitalId: req.user.hospitalId
    });

    if (!patient) {
      return res.status(404).json({ message: "Patient not found" });
    }

    // Save new assessment entry
    patient.ruralCareAssessment.push({
      case_id,
      symptoms,
      classification: cleanClass,      // FIXED
      summary,
      specialists,
      escalation_reason,
      timestamp: timestamp || new Date()
    });

    await patient.save();

    res.json({
      message: "Case saved successfully",
      patientId: patient.patientId
    });

  } catch (err) {
    console.error("🔥 SAVE ERROR:", err);
    res.status(500).json({ message: err.message });
  }
});


// 👉 GET all saved rural AI cases for one patient
router.get("/cases/:patientId", authenticate, authorize("nurse"), async (req, res) => {
  try {
    const patient = await Patient.findOne({
      patientId: req.params.patientId,
      hospitalId: req.user.hospitalId
    });

    if (!patient) {
      return res.status(404).json({ message: "Patient not found" });
    }

    res.json({
      cases: patient.ruralCareAssessment || []
    });

  } catch (err) {
    res.status(500).json({ message: err.message });
  }
});


module.exports = router;
