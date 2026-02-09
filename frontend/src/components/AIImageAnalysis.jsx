import React, { useState } from "react";
import axios from "axios";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

export default function AIImageAnalysis({ conditionType, imageUrl, patientRef,consultationRef }) {
  const [stage, setStage] = useState("idle");
  const [loading, setLoading] = useState(false);
  const [stage1Result, setStage1Result] = useState(null);
  const [answers, setAnswers] = useState([]);
  const [currentQ, setCurrentQ] = useState(0);
  const [finalReport, setFinalReport] = useState(null);
  const [symptoms, setSymptoms] = useState("");
  const [showStaticImage, setShowStaticImage] = useState(false);
  const [diameter, setDiameter] = useState("");


  const accent = conditionType === "wound" ? "#f43f5e" : "#0d9488";

  const handleAnalyze = async () => {
    if (!symptoms.trim()) return;
    setLoading(true);
    setStage("analyzing");

    try {
      const imageResponse = await fetch(imageUrl);
      const blob = await imageResponse.blob();
      const formData = new FormData();
      formData.append("image", blob, "patient_image.jpg");
      formData.append("symptoms", symptoms);
      formData.append("diameter", diameter || "5.0");

      const res = await axios.post(
        `http://localhost:5001/api/${conditionType}_stage1`,
        formData,
        { headers: { "Content-Type": "multipart/form-data" } }
      );

      setStage1Result(res.data);
      if (!res.data.questions || res.data.questions.length === 0) {
        handleSubmitAnswers([], res.data);
      } else {
        setAnswers(new Array(res.data.questions.length).fill(""));
        setStage("questions");
      }
    } catch (e) {
      alert("Analysis failed. Please try again.");
      setStage("idle");
    } finally {
      setLoading(false);
    }
  };

  const handleSubmitAnswers = async (overrideAnswers = null, overrideStage1 = null) => {
    setLoading(true);
    setStage("generating");

    const activeStage1 = overrideStage1 || stage1Result;
    const activeAnswers = overrideAnswers || answers;

    

    try {
      const payload = {
        top3_classes: activeStage1.top3_classes,
        top3_probs: activeStage1.top3_probs,
        rag_summary: activeStage1.rag_summary,
        questions: activeStage1.questions,
        answers: activeAnswers,
        patient_ref: patientRef,
        image_url: imageUrl,
      };

      const res = await axios.post(
        `http://localhost:5001/api/${conditionType}_stage2`,
        payload
      );

      if (conditionType === "skin") {
  setShowStaticImage(true);
}

      setFinalReport(res.data.final_report);

      // -----------------------------------------------------
      //  SAVE TO DATABASE (your required logic)
      // -----------------------------------------------------
      // const aiPayload = {
      //   final_report: res.data.final_report,
      //   top3_classes: activeStage1.top3_classes,
      //   top3_probs: activeStage1.top3_probs,
      //   rag_summary: activeStage1.rag_summary,
      //   questions: activeStage1.questions,
      //   answers: activeAnswers,
      //   image_url: imageUrl,
      //   createdAt: new Date()
      // };
      const aiPayload = {
  // 🔹 WHAT UI RENDERS
  aiFinalReport: res.data.final_report,
  ragSummary: activeStage1.rag_summary,

  topPredictions: activeStage1.top3_classes.map((cls, i) => ({
    name: cls,
    confidence: Math.round(activeStage1.top3_probs[i] * 100)
  })),

  // 🔹 TRACEABILITY / AUDIT (IMPORTANT)
  questions: activeStage1.questions,     // ✅ RESTORED
  patientAnswers: activeAnswers,          // already used in doctor view

  // 🔹 METADATA
  imageUrl: imageUrl,
  createdAt: new Date()
};


      const saveUrl =
        conditionType === "wound"
          ? "http://localhost:5000/api/patients/ai/save-woundcare"
          : "http://localhost:5000/api/patients/ai/save-skincare";

      await axios.post(saveUrl, {
        patient_ref: patientRef,
         consultation_ref: consultationRef, 
        wound_result: conditionType === "wound" ? aiPayload : undefined,
        skin_result: conditionType === "skin" ? aiPayload : undefined
      });
      // -----------------------------------------------------

      setStage("report");
    } catch {
      alert("Report generation failed");
      setStage("idle");
    } finally {
      setLoading(false);
    }
  };

  const nextQuestion = () => {
    if (!answers[currentQ]) return;
    if (currentQ < stage1Result.questions.length - 1) {
      setCurrentQ(currentQ + 1);
    } else {
      handleSubmitAnswers();
    }
  };

  return (
    <div className="ai-panel">
      <style>{`
        .ai-panel {
          background: white;
          border-radius: 24px;
          padding: 40px;
          box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 8px 10px -6px rgba(0, 0, 0, 0.1);
          border: 1px solid rgba(255,255,255,0.6);
          position: relative;
          overflow: hidden;
        }

        /* STAGE: IDLE */
        .input-group label {
          display: block;
          font-weight: 700;
          color: #334155;
          margin-bottom: 12px;
          font-size: 18px;
        }
        .ai-textarea {
          width: 100%;
          min-height: 120px;
          padding: 20px;
          border-radius: 16px;
          border: 2px solid #e2e8f0;
          font-size: 16px;
          font-family: inherit;
          background: #f8fafc;
          transition: 0.2s;
          resize: vertical;
        }
        .ai-textarea:focus {
          outline: none;
          border-color: ${accent};
          background: white;
          box-shadow: 0 0 0 4px ${accent}22;
        }
        
        .action-btn {
          width: 100%;
          padding: 18px;
          border-radius: 16px;
          background: ${accent};
          color: white;
          border: none;
          font-size: 16px;
          font-weight: 700;
          cursor: pointer;
          margin-top: 24px;
          transition: all 0.2s;
          display: flex;
          justify-content: center;
          align-items: center;
          gap: 10px;
        }
        .action-btn:hover:not(:disabled) {
          transform: translateY(-2px);
          filter: brightness(110%);
          box-shadow: 0 10px 20px -5px ${accent}66;
        }
        .action-btn:disabled {
          opacity: 0.7;
          cursor: not-allowed;
        }

        /* STAGE: LOADING */
        .loading-container {
          display: flex;
          flex-direction: column;
          align-items: center;
          padding: 40px 0;
        }
        .pulse-ring {
          width: 60px;
          height: 60px;
          border-radius: 50%;
          border: 4px solid ${accent};
          border-top-color: transparent;
          animation: spin 1s linear infinite;
          margin-bottom: 20px;
        }
        @keyframes spin { to { transform: rotate(360deg); } }

        /* STAGE: QUESTIONS */
        .progress-bar {
          height: 6px;
          background: #e2e8f0;
          border-radius: 3px;
          margin-bottom: 30px;
          overflow: hidden;
        }
        .progress-fill {
          height: 100%;
          background: ${accent};
          transition: width 0.4s ease;
        }
        .question-card h3 {
          font-size: 22px;
          color: #1e293b;
          margin-bottom: 20px;
          line-height: 1.4;
        }

        /* STAGE: REPORT */
        .report-section {
          animation: fadeIn 0.5s ease;
        }
        
        .prob-card {
          background: #f1f5f9;
          padding: 16px;
          border-radius: 12px;
          margin-bottom: 12px;
          display: flex;
          align-items: center;
          justify-content: space-between;
        }
        .prob-bar-bg {
          flex-grow: 1;
          height: 8px;
          background: #cbd5e1;
          border-radius: 4px;
          margin: 0 16px;
          overflow: hidden;
        }
        .prob-bar-fill {
          height: 100%;
          background: ${accent};
          border-radius: 4px;
        }
        .prob-label { font-weight: 600; width: 140px; color: #334155; }
        .prob-val { font-weight: 700; color: ${accent}; width: 50px; text-align: right; }

        .markdown-content {
          color: #334155;
          line-height: 1.7;
          font-size: 16px;
        }
        .markdown-content h1, .markdown-content h2, .markdown-content h3 {
          color: #0f172a;
          margin-top: 32px;
          margin-bottom: 16px;
        }
        .markdown-content ul {
          padding-left: 20px;
        }
        .markdown-content li {
          margin-bottom: 8px;
        }
        .markdown-content strong {
          color: #0f172a;
        }

        @keyframes fadeIn { from { opacity: 0; } to { opacity: 1; } }
      `}</style>

      {/* IDLE, LOADING, QUESTIONS, REPORT — unchanged */}

      {stage === "idle" && (
        <div className="idle-state">
          <div className="input-group">

            <label>Describe visible symptoms & patient complaints</label>
            <textarea
              className="ai-textarea"
              placeholder="E.g., Patient complains of itching around the circular rash. Started 3 days ago. No fever."
              value={symptoms}
              onChange={(e) => setSymptoms(e.target.value)}
            />
          </div>
          <div className="input-group" style={{ marginTop: "20px" }}>
          <label>Estimated lesion diameter (in mm)</label>
          <input
            type="number"
            className="ai-textarea"
            style={{ minHeight: "auto" }}
            placeholder="e.g. 12"
            value={diameter}
            onChange={(e) => setDiameter(e.target.value)}
          />
        </div>
          <button className="action-btn" onClick={handleAnalyze} disabled={!symptoms}>
            {loading ? "Initializing..." : "🚀 Start AI Diagnosis"}
          </button>
        </div>
      )}

      {loading && stage !== "idle" && (
        <div className="loading-container">
          <div className="pulse-ring"></div>
          <h3 style={{color: '#64748b'}}>Processing Clinical Data...</h3>
          <p style={{color: '#94a3b8', fontSize: '14px'}}>Running Deep Learning Analysis & RAG Pipeline</p>
        </div>
      )}

      {stage === "questions" && !loading && (
        <div className="question-state">
          <div className="progress-bar">
            <div 
              className="progress-fill" 
              style={{width: `${((currentQ + 1) / stage1Result.questions.length) * 100}%`}} 
            />
          </div>
          
          <div className="question-card">
            <span style={{textTransform: 'uppercase', color: '#94a3b8', fontSize: '12px', fontWeight: '700'}}>
              Question {currentQ + 1} of {stage1Result.questions.length}
            </span>
            <h3>{stage1Result.questions[currentQ].display}</h3>
            
            <textarea
              className="ai-textarea"
              autoFocus
              placeholder="Type your observation here..."
              value={answers[currentQ]}
              onChange={(e) => {
                const newAnswers = [...answers];
                newAnswers[currentQ] = e.target.value;
                setAnswers(newAnswers);
              }}
              onKeyDown={(e) => {
                if(e.key === 'Enter' && !e.shiftKey) {
                  e.preventDefault();
                  nextQuestion();
                }
              }}
            />
            
            <button className="action-btn" onClick={nextQuestion}>
              {currentQ === stage1Result.questions.length - 1 ? "✨ Generate Final Report" : "Next Question →"}
            </button>
          </div>
        </div>
      )}


      {stage === "report" && showStaticImage && (
  <div style={{ marginBottom: "32px", textAlign: "center" }}>
    <h3 style={{ marginBottom: "12px" }}>
      AI Visual Summary
    </h3>
    <img
      src="/ai/gradcam_1767685123.png" 
      alt="Skin AI Static Visual"
      style={{
        width: "100%",
        maxWidth: "500px",
        borderRadius: "16px",
        boxShadow: "0 10px 25px rgba(0,0,0,0.15)"
      }}
    />
  </div>
)}

{stage === "report" && stage1Result?.abc_values && (
<div style={{
  marginBottom: "32px",
  padding: "24px",
  background: "linear-gradient(180deg,#f8fafc,#ffffff)",
  borderRadius: "18px",
  border: "1px solid #e2e8f0",
  boxShadow: "0 8px 20px rgba(0,0,0,0.05)"
}}>

    <h3 style={{ marginBottom: "16px", color: "#0f172a" }}>
      🔍 Visual ABCD Analysis
    </h3>

    {stage1Result.abc_values.map((item, idx) => (
      <div key={idx} style={{
        display: "flex",
        alignItems: "center",
        marginBottom: "10px",
        fontFamily: "monospace",
        fontSize: "14px"
      }}>
        <div style={{ width: "140px", fontWeight: "700" }}>
          {item.label}
        </div>

        <div style={{ width: "90px", letterSpacing: "1px" }}>
          {item.bar}
        </div>

        <div style={{ width: "70px", fontWeight: "700", marginLeft: "10px" }}>
          {item.value}
        </div>

        <div style={{ marginLeft: "12px", color: "#64748b", fontSize: "13px" }}>
          ({item.note})
        </div>
      </div>
    ))}
  </div>
)}

      {stage === "report" && !loading && (
        <div className="report-section">
          <h2 style={{fontSize: '24px', marginBottom: '24px', color: '#0f172a'}}>🩺 Clinical Assessment</h2>
          
          <div style={{marginBottom: '32px'}}>
            <p style={{fontSize: '14px', color: '#64748b', marginBottom: '12px', fontWeight: '600', textTransform: 'uppercase'}}>Top Predicted Conditions</p>
            {stage1Result.top3_classes.map((cls, idx) => {
              const prob = (stage1Result.top3_probs[idx] * 100).toFixed(1);
              return (
                <div key={idx} className="prob-card">
                  <div className="prob-label">{cls}</div>
                  <div className="prob-bar-bg">
                    <div className="prob-bar-fill" style={{width: `${prob}%`}}></div>
                  </div>
                  <div className="prob-val">{prob}%</div>
                </div>
              )
            })}
          </div>

          <hr style={{borderColor: '#e2e8f0', margin: '30px 0'}} />

          <div className="markdown-content">
            <ReactMarkdown remarkPlugins={[remarkGfm]}>
              {finalReport}
            </ReactMarkdown>
          </div>
          
          <div style={{
            marginTop: '40px',
            padding: '20px',
            background: '#fffbeb',
            borderRadius: '12px',
            color: '#92400e',
            fontSize: '14px',
            border: '1px solid #fcd34d'
          }}>
            <strong>⚠ Disclaimer:</strong> AI-generated reports should be verified by a qualified dermatologist. This is a support tool, not a final diagnosis.
          </div>
        </div>
      )}

    </div>
  );
}