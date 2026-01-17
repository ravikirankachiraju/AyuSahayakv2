import { useEffect, useState } from "react";
import { useSearchParams, useNavigate, useLocation } from "react-router-dom";
import NurseNav from "../../components/NurseNav";
import http from "../../api/http";

export default function AISummary() {
  const [params] = useSearchParams();
  const navigate = useNavigate();
  const location = useLocation();

  const ref = params.get("ref");

  // Patient object passed from Patients.jsx
  const passedPatient = location.state?.patient || null;
  console.log("🎒 Router state:", location.state);
console.log("🎒 Passed patient:", passedPatient);


  const [loading, setLoading] = useState(true);
  const [aiData, setAiData] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!passedPatient) {
      setError("No patient data received.");
      setLoading(false);
      return;
    }

    const loadAI = async () => {
      try {
        console.log("🧩 Loaded patient from navigation state:", passedPatient);

        // WOUND or SKIN → AI summary already available
        if (passedPatient.conditionType === "wound" || passedPatient.conditionType === "skin") {
          console.log("⚕️ Using wound/skin AI summary:", passedPatient.aiSummary);
          setAiData(passedPatient.aiSummary);
        }

        // RURAL → Need to fetch cases separately
        else {
          console.log("🌾 Fetching rural AI cases for:", ref);

          const res = await http.get(`/cases/${ref}`);
          console.log("🌾 Raw cases response:", res.data);

          const cases = res.data.cases || [];
          const latest = cases.length > 0 ? cases[cases.length - 1] : null;

          console.log("🌾 Latest RuralCare summary:", latest);

          setAiData(latest);
        }
      } catch (err) {
        console.error("❌ Error loading AI summary:", err);
        setError("Failed to load AI Summary.");
      } finally {
        setLoading(false);
      }
    };

    loadAI();
  }, [ref, passedPatient]);

  if (loading) return <div className="loading">Loading...</div>;

  if (error)
    return (
      <div style={{ padding: 40, textAlign: "center", color: "red" }}>
        {error}
      </div>
    );

  const patient = passedPatient; // already normalized from main table

  return (
    <>
  <NurseNav />

  <div className="summary-container">

    <button className="back-btn" onClick={() => navigate(-1)}>
      ← Back
    </button>

    <h1 className="page-title">🤖 AI Report</h1>

    {/* Patient Card */}
    <div className="patient-box">
      <img
        className="patient-photo"
        src={patient.photo || "/default-avatar.png"}
        alt=""
      />

      <div className="patient-info">
        <h2>{patient.firstName} {patient.lastName}</h2>
        <p><b>ID:</b> {patient.patientId}</p>
        <p><b>Gender:</b> {patient.gender}</p>
        <p><b>Age:</b> {patient.age}</p>
        <p><b>Condition:</b> {patient.conditionType}</p>
      </div>
    </div>

    {/* AI Summary */}
    <div className="summary-card">

      {!aiData && <p>No AI summary available.</p>}

      {aiData && (
        <>
          {/* AI TYPE TITLE */}
          <h2 className="section-title">
            {patient.conditionType === "wound" && "🩹 WoundCare AI Results"}
            {patient.conditionType === "skin" && "🧴 SkinCare AI Results"}
            {patient.conditionType === "other" && "🩺 RuralCare AI Results"}
          </h2>

          {/* WOUND */}
          {patient.conditionType === "wound" && (
            <div className="summary-grid">
              <p><b>Top Predictions:</b> {aiData.topPredictions?.map(p => p.name).join(", ")}</p>
              <p><b>Symptoms:</b> {aiData.symptoms?.join(", ")}</p>
              <p><b>Medications:</b> {aiData.medications?.join(", ")}</p>
              <p><b>Wound Care:</b> {aiData.woundCare}</p>
              <p><b>Home Care:</b> {aiData.homeCare}</p>
              <p><b>Red Flags:</b> {aiData.redFlags?.join(", ")}</p>
            </div>
          )}

          {/* SKIN */}
          {patient.conditionType === "skin" && (
            <div className="summary-grid">
              <p><b>Top Predictions:</b> {aiData.topPredictions?.map(p => p.name).join(", ")}</p>
              <p><b>Diagnosis:</b> {aiData.mostLikelyDiagnosis}</p>
              <p><b>Recommended Action:</b> {aiData.recommendedAction}</p>
              <p><b>Red Flags:</b> {aiData.redFlags?.join(", ")}</p>
            </div>
          )}

          {/* RURAL */}
          {patient.conditionType === "other" && (
            <>
              <div className="summary-grid">
                <p><b>Case ID:</b> {aiData.case_id}</p>
                <p><b>Classification:</b> {aiData.classification}</p>
                <p><b>Symptoms:</b> {aiData.symptoms?.join(", ")}</p>
                <p><b>Specialists:</b> {aiData.specialists?.join(", ")}</p>
              </div>
              {/* BEAUTIFUL DETAILED SUMMARY UI */}
<h3 className="ds-title">📝 Detailed Summary</h3>

<div className="ds-card">
  {Object.entries(aiData.summary).map(([key, value], index) => (
    value && value.length !== 0 && (  // hide empty sections
      <div key={index} className="ds-section">
        <h4 className="ds-heading">{key.replace(/_/g, " ")}</h4>

        {/* If value is a list → render bullet points */}
        {Array.isArray(value) ? (
          <ul className="ds-list">
            {value.map((item, i) => (
              <li key={i}>{item}</li>
            ))}
          </ul>
        ) : (
          <p className="ds-text">{value}</p>
        )}
      </div>
    )
  ))}
</div>

              
            </>
          )}
        </>
      )}
    </div>
  </div>


  {/* STYLES */}
  <style>{`
    .summary-container {
      padding: 40px;
      max-width: 900px;
      margin: 0 auto;
      animation: fadeIn 0.4s ease;
    }

    .page-title {
      font-size: 32px;
      font-weight: 800;
      background: linear-gradient(135deg, #0099ff, #00cc88);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
      margin-bottom: 20px;
    }

    .back-btn {
      background: none;
      border: none;
      font-size: 18px;
      cursor: pointer;
      margin-bottom: 18px;
      color: #333;
    }

    /* Patient Card */
    .patient-box {
      display: flex;
      gap: 20px;
      align-items: center;
      padding: 25px;
      border-radius: 20px;
      background: rgba(255,255,255,0.8);
      backdrop-filter: blur(10px);
      box-shadow: 0 8px 18px rgba(0,0,0,0.1);
      margin-bottom: 35px;
    }

    .patient-photo {
      width: 90px;
      height: 90px;
      border-radius: 50%;
      object-fit: cover;
      box-shadow: 0 4px 10px rgba(0,0,0,0.15);
    }

    .patient-info h2 {
      font-size: 24px;
      font-weight: 700;
      margin: 0 0 6px;
    }

    /* Summary Card */
    .summary-card {
      padding: 30px;
      background: white;
      border-radius: 18px;
      box-shadow: 0 8px 22px rgba(0,0,0,0.1);
    }

    .section-title {
      font-size: 22px;
      font-weight: 700;
      margin-bottom: 20px;
      color: #0066aa;
    }

    .summary-grid p {
      padding: 10px 0;
      border-bottom: 1px solid #eee;
      font-size: 16px;
    }

    /* JSON Summary */
    .json-title {
      margin-top: 20px;
      font-size: 18px;
      font-weight: 600;
    }

    .json-box {
      padding: 16px;
      background: #f5f7fa;
      border-radius: 12px;
      overflow-x: auto;
      border: 1px solid #e3e3e3;
      margin-top: 8px;
      font-size: 14px;
    }

    /* Animations */
    @keyframes fadeIn {
      from { opacity: 0; transform: translateY(10px); }
      to   { opacity: 1; transform: translateY(0); }
    }

    /* Detailed Summary Styles */
.ds-title {
  margin-top: 25px;
  font-size: 22px;
  font-weight: 700;
  color: #333;
  margin-bottom: 14px;
}

.ds-card {
  background: #ffffff;
  border-radius: 14px;
  padding: 20px;
  border: 1px solid #e6e6e6;
  box-shadow: 0 4px 16px rgba(0,0,0,0.06);
}

.ds-section {
  margin-bottom: 20px;
  padding-bottom: 12px;
  border-bottom: 1px solid #f0f0f0;
}

.ds-heading {
  font-size: 17px;
  font-weight: 700;
  margin-bottom: 6px;
  color: #555;
  text-transform: capitalize;
}

.ds-text {
  font-size: 15px;
  color: #444;
  line-height: 1.6;
  background: #f9fafc;
  padding: 10px 12px;
  border-radius: 8px;
  border: 1px solid #ececec;
}

.ds-list {
  margin-left: 18px;
  margin-top: 5px;
  color: #444;
}

.ds-list li {
  margin-bottom: 6px;
  line-height: 1.5;
  padding: 6px 10px;
  background: #f9fafc;
  border-radius: 6px;
  border: 1px solid #ececec;
  list-style-type: disc;
}

  `}</style>
</>

  );
}
