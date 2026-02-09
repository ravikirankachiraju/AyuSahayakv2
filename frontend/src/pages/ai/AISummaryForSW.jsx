import { useEffect, useState } from "react";
import { useSearchParams, useNavigate } from "react-router-dom";
import NurseNav from "../../components/NurseNav";
import http from "../../api/http";
import ReactMarkdown from "react-markdown";   // ⬅️ ADDED

export default function AISummary() {
  const [params] = useSearchParams();
  const ref = params.get("ref");
  const [loading, setLoading] = useState(true);
  const [patient, setPatient] = useState(null);
  const navigate = useNavigate();

  useEffect(() => {
    load();
  }, []);

  const load = async () => {
    try {
      const { data } = await http.get("/nurse/patients");
      const found = data.find(
        (p) => p.patientId === ref || p._id === ref || p.id === ref
      );

      if (!found) {
        setLoading(false);
        return;
      }

      const ai =
  found.latestConsultation?.aiSummary ||
  found.woundCareAI ||
  found.skinCareAI ||
  null;


      setPatient({
        name:
          found.personalInfo?.firstName + " " + found.personalInfo?.lastName,
        photo:
          (Array.isArray(found.photos) && found.photos[0]?.url) ||
          found.personalInfo?.photo ||
          "",
        condition: found.conditionType,
        ai,
      });

      setLoading(false);
    } catch (e) {
      console.log(e);
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div style={{ padding: 40, fontSize: 20 }}>Loading AI Summary...</div>
    );
  }

  if (!patient || !patient.ai) {
    return (
      <div style={{ padding: 40, fontSize: 20, color: "red" }}>
        No AI Summary found for this patient.
      </div>
    );
  }

  const ai = patient.ai;

  return (
    <div className="ai-summary-page">
      <style>{`
        .ai-summary-page {
          min-height: 100vh;
          background: hsl(210 20% 98%);
        }

        .ai-summary-container {
          padding: 32px;
          max-width: 1100px;
          margin: auto;
        }

        .ai-card {
          background: white;
          border-radius: 16px;
          padding: 32px;
          box-shadow: 0 4px 10px rgba(0,0,0,0.07);
          margin-bottom: 40px;
        }

        .ai-title {
          font-size: 32px;
          font-weight: 700;
          color: hsl(215 25% 22%);
          margin-bottom: 8px;
        }

        .ai-sub {
          font-size: 18px;
          color: hsl(215 16% 47%);
          margin-bottom: 24px;
        }

        .ai-image {
          width: 260px;
          height: 260px;
          border-radius: 14px;
          object-fit: cover;
          border: 2px solid hsl(214 32% 91%);
          margin-bottom: 22px;
        }

        .section-title {
          font-size: 22px;
          font-weight: 700;
          margin: 28px 0 12px 0;
          color: hsl(215 25% 27%);
        }

        .predictions-badges {
          display: flex;
          gap: 12px;
          flex-wrap: wrap;
        }

        .prediction-badge {
          background: hsl(210 40% 98%);
          border: 1px solid hsl(214 32% 90%);
          padding: 10px 16px;
          border-radius: 30px;
          display: flex;
          gap: 10px;
          align-items: center;
          font-weight: 600;
        }

        .pred-name {
          color: hsl(215 25% 27%);
        }

        .pred-confidence {
          color: hsl(215 16% 50%);
          font-size: 14px;
        }

        .ai-box {
          background: hsl(210 40% 98%);
          padding: 20px;
          border-radius: 14px;
          border: 1px solid hsl(214 32% 90%);
          line-height: 1.7;
          font-size: 16px;
        }

        .ai-box h1, 
        .ai-box h2, 
        .ai-box h3 {
          color: hsl(215 25% 22%);
          margin-top: 18px;
        }

        .ai-box ul {
          margin-left: 20px;
        }

        .btn-back {
          padding: 14px 24px;
          color: #060c19d7;
          border-radius: 15px;
          background-color: white;
          font-weight: 600;
          cursor: pointer;
          border: 1px solid #060c194c ;
          margin-top: 30px;
        }
      `}</style>

      <NurseNav />

      <div className="ai-summary-container" style={{marginTop: "2rem"}}>
        <button className="btn-back" style={{marginBottom: "1.5rem"}} onClick={() => navigate("/nurse/patients")}>
            ← Back
          </button>
        <div className="ai-card">
          <div className="ai-title">AI Summary Report</div>
          <div className="ai-sub">Patient: {patient.name}</div>

          {patient.photo && (
            <img src={patient.photo} className="ai-image" alt="Patient" />
          )}

          {/* TOP PREDICTIONS */}
          <div className="section-title">🔍 Top Predictions</div>
          <div className="predictions-badges">
            {ai.topPredictions?.map((p, index) => (
              <div key={index} className="prediction-badge">
                <span className="pred-name">{p.name}</span>
                <span className="pred-confidence">{p.confidence}%</span>
              </div>
            ))}
          </div>

          {/* FINAL REPORT */}
          <div className="section-title">📝 Final AI Report</div>
          <div className="ai-box">
            <ReactMarkdown>{ai.aiFinalReport}</ReactMarkdown>
          </div>

          {/* RAG SUMMARY */}
          <div className="section-title">📚 RAG Summary</div>
          <div className="ai-box">
            <ReactMarkdown>{ai.ragSummary}</ReactMarkdown>
          </div>

          
        </div>
      </div>
    </div>
  );
}
