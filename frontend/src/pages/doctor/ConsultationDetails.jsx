import { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import DoctorNav from '../../components/DoctorNav';
import http from '../../api/http';
import ReactMarkdown from "react-markdown";




export default function ConsultationDetails() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [data, setData] = useState(null);
  const [err, setErr] = useState('');

  const load = async () => {
    setErr('');
    try {
      const res = await http.get(`/doctor/consultations/${id}/details`);
      const consultationData = res.data;

      // 🌾 Fetch RuralCareAssessment cases
      consultationData.ruralCases = consultationData.patient?.ruralCases || [];

      setData(consultationData);

    } catch (e) {
      setErr(e.response?.data?.message || 'Failed to load');
    }
  };

  useEffect(() => { load(); /* eslint-disable-next-line */ }, [id]);

  useEffect(() => {
    if (!data || data.video?.enabled) return;
    const t = setInterval(() => load(), 4000);
    return () => clearInterval(t);
  }, [data]);

  const accept = async () => {
    try {
      await http.patch(`/doctor/consultations/${id}/accept`);
      navigate('/doctor/in-progress');
    } catch (e) {
      alert(e.response?.data?.message || 'Accept failed');
    }
  };

  const decline = async () => {
    const reason = prompt('Reason for decline?') || 'no reason';
    try {
      await http.patch(`/doctor/consultations/${id}/decline`, { reason });
      navigate('/doctor/queue');
    } catch (e) {
      alert(e.response?.data?.message || 'Decline failed');
    }
  };

  // Local animation states for accept/decline actions
  const [acceptState, setAcceptState] = useState('idle'); // idle | pending | success | error
  const [declineState, setDeclineState] = useState('idle');

  const acceptWithAnimation = async () => {
    setAcceptState('pending');
    try {
      await http.patch(`/doctor/consultations/${id}/accept`);
      setAcceptState('success');
      // brief success animation then navigate
      setTimeout(()=> navigate('/doctor/in-progress'), 700);
    } catch (e) {
      setAcceptState('error');
      setTimeout(()=> setAcceptState('idle'), 900);
      alert(e.response?.data?.message || 'Accept failed');
    }
  };

  const declineWithAnimation = async () => {
    const reason = prompt('Reason for decline?') || 'no reason';
    setDeclineState('pending');
    try {
      await http.patch(`/doctor/consultations/${id}/decline`, { reason });
      setDeclineState('success');
      setTimeout(()=> navigate('/doctor/queue'), 700);
    } catch (e) {
      setDeclineState('error');
      setTimeout(()=> setDeclineState('idle'), 900);
      alert(e.response?.data?.message || 'Decline failed');
    }
  };

  return (
    <div className="details-page">

      {/* ---------------- CSS ---------------- */}
      <style>{`

  :root{
    --primary-1: #0d48a1da;
    --primary-2: #0d48a1a8;
    --accent: #1f66d987;
    --glass-strong: rgba(255,255,255,0.97);
    --glass-soft: rgba(255,255,255,0.92);
    --muted: rgba(0,0,0,0.52);
    --text: rgba(0,0,0,0.78);
    --shadow-1: 0 12px 40px -18px rgba(0,0,0,0.28);
    --shadow-2: 0 22px 60px -28px rgba(0,0,0,0.32);
    --radius-lg: 20px;
  }

  /* Page base */
  .details-page{ min-height:100vh; background: linear-gradient(180deg,#f8fbff 0%, #ffffff 100%); }
  .details-container{ padding:28px 24px 64px; max-width:1180px; margin:0 auto; position:relative; }
  .details-container::before{ content:""; position:absolute; inset:24px -8px 0; margin:0 auto; max-width:1160px; border-radius:28px; background: linear-gradient(180deg, rgba(255,255,255,0.995), rgba(255,255,255,0.96)); border:1px solid rgba(255,255,255,0.9); box-shadow: var(--shadow-1); backdrop-filter: blur(14px); z-index:-1; }

  @keyframes fadeInUp{ from{opacity:0;transform:translateY(18px)} to{opacity:1;transform:translateY(0)} }

  /* Back */
  .btn-back{ padding:0.55rem 1.2rem; background:rgba(255,255,255,0.98); border:1px solid rgba(0,0,0,0.06); border-radius:999px; color:var(--text); display:inline-flex; align-items:center; gap:8px; cursor:pointer; transition:all 180ms ease; }
  .btn-back:hover{ transform:translateY(-2px); box-shadow:0 10px 30px -18px rgba(0,0,0,0.14); }

  .page-header{ margin:14px 0 22px; }
  .page-header h1{ font-size:clamp(1.9rem,2.6vw,2.2rem); font-weight:800; color:var(--text); display:inline-flex; align-items:center; gap:10px; }

  .error-alert{ background:#ffebee; color:var(--text); border:1px solid rgba(0,0,0,0.08); padding:12px 14px; border-radius:12px; }
  .loading{ text-align:center; padding:44px 20px; color:var(--muted); }

  /* HERO - strong gradient using requested blues */
  .hero-section{ position:relative; background: linear-gradient(120deg, var(--primary-1) 0%, var(--primary-2) 100%); border-radius:22px; padding:20px; margin-bottom:22px; color: #fff; box-shadow: var(--shadow-2); overflow:hidden; border:1px solid rgba(255,255,255,0.06); }
  .hero-section::before{ content:""; position:absolute; inset:-20%; background: radial-gradient(circle at 10% 10%, rgba(255,255,255,0.12), transparent 35%); pointer-events:none; }
  .hero-section::after{ content:""; position:absolute; inset:0; background: linear-gradient(180deg, rgba(0,0,0,0.06), transparent 35%); pointer-events:none; }

  .patient-hero{ display:flex; gap:18px; align-items:center; z-index:1; }
  .patient-avatar-large{ width:96px; height:96px; border-radius:50%; object-fit:cover; border:4px solid rgba(255,255,255,0.14); box-shadow: 0 10px 30px -12px rgba(0,0,0,0.45); background:#fff; color:var(--primary-1); font-weight:800; display:flex; align-items:center; justify-content:center; font-size:36px }
  .patient-info h2{ margin:0; font-size:1.5rem; font-weight:800; color:#fff; letter-spacing:-0.02em }
  .patient-meta{ display:flex; gap:10px; color:rgba(255,255,255,0.9); font-size:0.92rem; flex-wrap:wrap }

  /* Chief complaint - softened on gradient */
  .complaint-highlight{ margin-top:10px; background: rgba(255,255,255,0.08); color: #fff; padding:12px; border-radius:14px; border-left:4px solid rgba(255,255,255,0.14); box-shadow: 0 8px 30px -16px rgba(0,0,0,0.32); }
  .complaint-label{ font-size:0.72rem; font-weight:600; text-transform:uppercase; color:rgba(255,255,255,0.85); margin-bottom:6px }
  .complaint-text{ font-size:0.95rem; line-height:1.55; color: rgba(255,255,255,0.95) }

  /* Content grid and cards (glass) */
  .content-grid{ display:grid; grid-template-columns: minmax(0,2fr) minmax(0,1.1fr); gap:20px; margin-top:20px }
  .card{ background:var(--glass-strong); border-radius:16px; padding:16px; box-shadow:0 10px 30px -14px rgba(0,0,0,0.12); border:1px solid rgba(0,0,0,0.04); }
  .card h3{ font-size:1rem; margin:0 0 12px; font-weight:700; color:var(--text) }

  .info-grid{ display:grid; gap:8px }
  .info-row{ display:flex; justify-content:space-between; padding:8px 0; border-bottom:1px solid rgba(0,0,0,0.04); font-size:0.95rem }
  .info-row:last-child{ border-bottom:none }
  .info-label{ color:var(--muted); font-weight:600; font-size:0.82rem }
  .info-value{ color:var(--text); font-weight:700 }

  .badge{ display:inline-flex; align-items:center; padding:6px 12px; border-radius:999px; font-weight:700; font-size:0.8rem }
  .badge-queue{ background: rgba(255,255,255,0.9); color:var(--text) }
  .badge-progress{ background: rgba(255,255,255,0.9); color:var(--text) }

  .images-gallery{ display:grid; grid-template-columns: repeat(auto-fill,minmax(140px,1fr)); gap:12px }
  .gallery-image{ width:100%; height:140px; object-fit:cover; border-radius:12px; border:1px solid rgba(0,0,0,0.04); transition: transform .22s ease, box-shadow .22s ease }
  .gallery-image:hover{ transform: translateY(-4px); box-shadow: 0 18px 40px -18px rgba(0,0,0,0.28) }

  /* Action bar: sticky with modern buttons */
  .action-bar{ position:sticky; bottom:0; display:flex; gap:12px; padding:12px; background: linear-gradient(180deg, rgba(255,255,255,0.98), rgba(255,255,255,0.98)); border-radius:14px; box-shadow: 0 -12px 36px -18px rgba(0,0,0,0.12); }
  .btn{ flex:1; padding:10px 14px; border-radius:999px; font-weight:700; font-size:0.95rem; cursor:pointer; border:none; display:inline-flex; align-items:center; justify-content:center; gap:8px }
  .btn-primary{ background: linear-gradient(135deg, var(--primary-1), var(--primary-2)); color:#fff; box-shadow: 0 12px 36px -14px rgba(13,71,161,0.22) }
  .btn-primary::before{ content:'' }
  .btn-success{ background: #e8f5e9; color:var(--text); border:1px solid rgba(0,0,0,0.04) }
  .btn-danger{ background:#ffebee; color:var(--text); border:1px solid rgba(0,0,0,0.06) }
  .btn:disabled{ opacity:0.6; cursor:not-allowed }

  .video-status{ margin-top:12px; padding:12px; background:#fff6f6; border-radius:10px; border:1px solid rgba(0,0,0,0.04); color:var(--muted) }

  /* Action animations */
  .anim-pending { animation: pulse 1000ms infinite; transform-origin: center; }
  @keyframes pulse {
    0% { box-shadow: 0 6px 18px -8px rgba(13,71,161,0.18); transform: translateY(0) scale(1); }
    50% { box-shadow: 0 18px 40px -18px rgba(13,71,161,0.28); transform: translateY(-2px) scale(1.03); }
    100% { box-shadow: 0 6px 18px -8px rgba(13,71,161,0.18); transform: translateY(0) scale(1); }
  }

  .anim-success { position: relative; }
  .anim-success .action-feedback { margin-left:10px; color: #1ec28b; font-weight:800; animation: pop 420ms ease both; }
  @keyframes pop { 0% { transform: scale(0.2) rotate(-20deg); opacity:0 } 60% { transform: scale(1.12) rotate(5deg); opacity:1 } 100% { transform: scale(1) rotate(0deg); opacity:1 } }

  .anim-error { animation: shake 520ms cubic-bezier(.36,.07,.19,.97); }
  @keyframes shake { 10%, 90% { transform: translateX(-1px); } 20%, 80% { transform: translateX(2px); } 30%,50%,70% { transform: translateX(-4px); } 40%,60% { transform: translateX(4px); } }
  .anim-error .action-feedback { margin-left:10px; color: #e54b4b; font-weight:800 }

  /* Responsive */
@media (max-width: 1024px) {
  .content-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 768px) {
  .details-container {
    padding: 22px 16px 48px;
  }

  .details-container::before {
    inset: 24px -4px 0;
  }

  .patient-hero {
    flex-direction: column;
    text-align: center;
  }

  .patient-meta {
    justify-content: center;
  }

  .action-bar {
    flex-direction: column;
    border-radius: 18px 18px 0 0;
  }
}
  .images-gallery {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(160px, 1fr));
  gap: 14px;
}
.gallery-image {
  height: 130px;
  border-radius: 12px;
  object-fit: cover;
  border: 1px solid #e4e4e4;
}

/* ---------------- RURALCARE AI BLOCK ---------------- */
.rural-box {
  padding: 14px;
  background: #f8faff;
  border-radius: 12px;
  border: 1px solid #e4e7ec;
  margin-bottom: 14px;
}

.rural-row {
  display: flex;
  justify-content: space-between;
  margin-bottom: 6px;
}

.rural-label { font-weight: 500; color: #555; }
.rural-value { font-weight: 600; color: #222; }

.rural-summary {
  background: #f1f3f5;
  padding: 10px;
  border-radius: 8px;
  font-size: 13px;
  margin-top: 10px;
}

.rural-summary pre {
  white-space: pre-wrap; /* FIX long text collapse */
  font-size: 13px;
  line-height: 1.4;
}
  .video-status {
  text-align: center;
  margin-top: 10px;
  font-size: 14px;
  color: #666;
}
.rural-ai section {
  margin-bottom: 14px;
}

.rural-ai h4 {
  font-size: 14px;
  font-weight: 700;
  margin-bottom: 6px;
  color: #1f2937;
}

.rural-ai p {
  font-size: 13px;
  line-height: 1.5;
  color: #374151;
}

.rural-ai ul {
  padding-left: 18px;
  font-size: 13px;
  color: #374151;
}

.rural-ai li {
  margin-bottom: 4px;
}

.rural-warning {
  background: #fff7ed;
  border: 1px solid #fed7aa;
  padding: 10px;
  border-radius: 8px;
}

.rural-warning h4 {
  color: #b45309;
}

  `}</style>
      
      <DoctorNav />
      <div className="details-container" style={{marginTop: "80px"}}>
        {/* <button onClick={()=>navigate(-1)} className="btn-back">← Back</button> */}

        <button onClick={() => navigate(-1)} className="btn-back">← Back</button>
        <div className="page-header">
          <h1>📋 Consultation Details</h1>
        </div>

        {err && <div className="error-alert">⚠ {err}</div>}

        {!data ? (
          <div className="loading">⏳ Loading...</div>
        ) : (
          <>
            {/* ---------------- HERO ---------------- */}
            <div className="hero-section">
              <div className="patient-hero">
                {data.patient.photo ? (
                  <img src={data.patient.photo} className="patient-avatar-large" alt="" />
                ) : (
                  <div className="patient-avatar-large" style={{
                    background: 'white', color: 'hsl(261 47% 58%)',
                    display: 'flex', alignItems: 'center', justifyContent: 'center',
                    fontSize: 40, fontWeight: 700
                  }}>
                    {data.patient.name?.[0] || "?"}
                  </div>
                )}

                <div className="patient-info">
                  <h2>{data.patient.name}</h2>
                  <div className="patient-meta">
                    <span>{data.patient.gender}</span>
                    <span>•</span>
                    <span>{data.patient.age} yrs</span>
                    <span>•</span>
                    <span>{data.patient.conditionType}</span>
                  </div>
                </div>
              </div>

              {data.consultation.chiefComplaint && (
                <div className="complaint-highlight">
                  <div className="complaint-label">Chief Complaint</div>
                  <div className="complaint-text">{data.consultation.chiefComplaint}</div>
                </div>
              )}
            </div>

            {/* ---------------- BODY GRID ---------------- */}
            <div className="content-grid">

              {/* LEFT SIDE */}
              <div>

                <div className="card" style={{ marginBottom: 24 }}>
                  <h3>📊 Consultation Information</h3>
                  <div className="info-grid">
                    <div className="info-row"><span className="info-label">Consultation ID</span><span className="info-value" style={{ fontFamily: 'monospace' }}>{data.consultation.consultationId}</span></div>
                    <div className="info-row"><span className="info-label">Status</span><span className={`badge badge-${data.consultation.status === 'in_progress' ? 'progress' : 'queue'}`}>{data.consultation.status}</span></div>
                    <div className="info-row"><span className="info-label">Condition</span><span className="info-value">{data.consultation.conditionType}</span></div>
                  </div>
                </div>

                {/* ---------------- PATIENT IMAGES ---------------- */}
                {(data.patient?.photos?.length > 0 || data.consultationImages?.length > 0) && (
                  <div className="card">
                    <h3>📸 Patient Images</h3>
                    <div className="images-gallery">
                      {data.patient.photos?.map((p, i) => (
                        <img key={i} src={p.url} className="gallery-image" alt="" />
                      ))}
                      {data.consultationImages?.map((p, i) => (
                        <img key={i} src={p.url} className="gallery-image" alt="" />
                      ))}
                    </div>
                  </div>
                )}

                {/* 🌾 ---------------- RURALCARE AI BLOCK ---------------- */}
                {data.ruralCases?.length > 0 && (
                  <div className="card" style={{ marginTop: 24 }}>
                    <h3>🌾 RuralCare AI Assessments</h3>

                    {data.ruralCases.map((caseItem, index) => (
                      <div key={index} className="rural-box">
                        <div className="rural-row">
                          <span className="rural-label">Case ID</span>
                          <span className="rural-value">{caseItem.case_id}</span>
                        </div>

                        <div className="rural-row">
                          <span className="rural-label">Classification</span>
                          <span className={`badge ${caseItem.classification === "high" ? "badge-danger" : "badge-progress"}`}>
                            {caseItem.classification}
                          </span>
                        </div>

                        <div className="rural-row">
                          <span className="rural-label">Symptoms</span>
                          <span className="rural-value">{caseItem.symptoms?.join(", ")}</span>
                        </div>

                        <div className="rural-row">
                          <span className="rural-label">Specialists</span>
                          <span className="rural-value">{caseItem.specialists?.join(", ")}</span>
                        </div>

                        <div className="rural-ai">

  {/* 🧠 CONDITION SUMMARY */}
  {caseItem.summary?.["CONDITION SUMMARY"] && (
    <section>
      <h4>🧠 Clinical Summary</h4>
      <p>{caseItem.summary["CONDITION SUMMARY"]}</p>
    </section>
  )}

  {/* 🩺 POSSIBLE CAUSES */}
  {caseItem.summary?.["POSSIBLE CAUSES"] && (
    <section>
      <h4>🩺 Possible Causes</h4>
      <ul>
        {caseItem.summary["POSSIBLE CAUSES"]
          .split(".")
          .filter(Boolean)
          .map((c, i) => (
            <li key={i}>{c.trim()}</li>
          ))}
      </ul>
    </section>
  )}

  {/* 👩‍⚕️ NURSE ACTIONS */}
  {caseItem.summary?.["NURSE ACTIONS"] && (
    <section>
      <h4>👩‍⚕️ Nurse Recommended Actions</h4>
      <ul>
        {caseItem.summary["NURSE ACTIONS"]
          .split("\n- ")
          .filter(Boolean)
          .map((a, i) => (
            <li key={i}>✓ {a.replace("-", "").trim()}</li>
          ))}
      </ul>
    </section>
  )}

  {/* 🚨 ESCALATION CRITERIA */}
  {caseItem.summary?.["ESCALATION CRITERIA"] && (
    <section className="rural-warning">
      <h4>🚨 Escalation Criteria</h4>
      <ul>
        {caseItem.summary["ESCALATION CRITERIA"]
          .split("\n- ")
          .filter(Boolean)
          .map((e, i) => (
            <li key={i}>⚠ {e.replace("-", "").trim()}</li>
          ))}
      </ul>
    </section>
  )}

  {/* 💊 MEDICINES ADVISED */}
  {caseItem.summary?.["MEDICINES ADVISED"]?.length > 0 && (
    <section>
      <h4>💊 Medicines (Doctor Decision)</h4>
      <ul>
        {caseItem.summary["MEDICINES ADVISED"].map((m, i) => (
          <li key={i}>{m}</li>
        ))}
      </ul>
    </section>
  )}

</div>

                      </div>
                    ))}
                  </div>
                )}

                {/* ================================
      AI SUMMARY — SKIN + WOUND
================================= */}
{(data.patient?.skinCareAI || data.patient?.woundCareAI) && (
  <div className="card" style={{ marginTop: "24px" }}>
    <h3>🤖 AI Summary</h3>

    {["skinCareAI", "woundCareAI"].map((key) => {
      const ai = data.patient?.[key];
      if (!ai) return null;

      const title = key === "skinCareAI" ? "Skin Analysis" : "Wound Analysis";
      const color = key === "skinCareAI" ? "#3B82F6" : "#EF4444";

      return (
        <div
          key={key}
          style={{
            borderLeft: `4px solid ${color}`,
            paddingLeft: "16px",
            marginBottom: "24px"
          }}
        >
          <h4 style={{ marginBottom: "12px" }}>{title}</h4>

          {/* Top Predictions */}
          {ai.topPredictions && (
            <div style={{ marginBottom: "16px" }}>
              <strong style={{ fontSize: "14px", color: "#555" }}>
                Top Predictions
              </strong>
              <ul style={{ marginTop: "8px", paddingLeft: "20px" }}>
                {ai.topPredictions.map((p, i) => (
                  <li key={i} style={{ marginBottom: "4px" }}>
                    <span style={{ fontWeight: "600" }}>{p.name}</span>{" "}
                    — {p.confidence}%
                  </li>
                ))}
              </ul>
            </div>
          )}

{ai.aiFinalReport && (
  <div
    style={{
      background: "#f8f9fc",
      padding: "14px",
      borderRadius: "10px",
      marginBottom: "16px",
      lineHeight: "1.6",
      fontSize: "14px"
    }}
  >
    <ReactMarkdown>{ai.aiFinalReport}</ReactMarkdown>
  </div>
)}


          {/* RAG Summary */}
          {ai.ragSummary && (
            <details
              style={{
                marginBottom: "16px",
                background: "#fafafa",
                padding: "10px 14px",
                borderRadius: "8px",
                border: "1px solid #eee"
              }}
            >
              <summary
                style={{
                  fontWeight: "600",
                  cursor: "pointer",
                  fontSize: "14px"
                }}
              >
                📚 Clinical Reference Summary (RAG)
              </summary>
              <div
                style={{
                  marginTop: "12px",
                  whiteSpace: "pre-wrap",
                  fontSize: "13px",
                  lineHeight: "1.5"
                }}
              >
                {ai.ragSummary}
              </div>
            </details>
          )}

          {/* Patient Answers
          {ai.patientAnswers && (
            <div style={{ marginTop: "12px" }}>
              <strong style={{ fontSize: "14px", color: "#555" }}>
                Patient Answers
              </strong>
              <ul style={{ marginTop: "6px", paddingLeft: "20px" }}>
                {ai.patientAnswers.map((ans, idx) => (
                  <li key={idx} style={{ fontSize: "14px", marginBottom: "4px" }}>
                    {ans}
                  </li>
                ))}
              </ul>
            </div>
          )} */}
        </div>
      );
    })}
  </div>
)}


              </div>

              {/* RIGHT SIDE */}
              <div>

                <div className="card">
                  <h3>👤 Patient Details</h3>
                  <div className="info-grid">
                    <div className="info-row"><span className="info-label">Patient ID</span><span className="info-value" style={{ fontFamily: 'monospace' }}>{data.patient.patientId}</span></div>
                    <div className="info-row"><span className="info-label">Phone</span><span className="info-value">{data.patient.phone}</span></div>
                    <div className="info-row"><span className="info-label">Height</span><span className="info-value">{data.patient.height ? `${data.patient.height} cm` : "—"}</span></div>
                    <div className="info-row"><span className="info-label">Weight</span><span className="info-value">{data.patient.weight ? `${data.patient.weight} kg` : "—"}</span></div>
                  </div>
                </div>

              </div>
            </div>

            {/* ---------------- ACTION BUTTONS ---------------- */}
            <div className="action-bar">

              {data.consultation.status === 'in_queue' && (
                <>
                  <button
                    className={`btn btn-success ${acceptState==='pending' ? 'anim-pending' : acceptState==='success' ? 'anim-success' : acceptState==='error' ? 'anim-error' : ''}`}
                    onClick={acceptWithAnimation}
                    disabled={acceptState==='pending'}
                  >
                    <span>✓</span>
                    <span style={{marginLeft:8}}>Accept Case</span>
                    <span className="action-feedback" aria-hidden>
                      {acceptState==='success' ? '✔' : acceptState==='error' ? '✖' : ''}
                    </span>
                  </button>

                  <button
                    className={`btn btn-danger ${declineState==='pending' ? 'anim-pending' : declineState==='success' ? 'anim-success' : declineState==='error' ? 'anim-error' : ''}`}
                    onClick={declineWithAnimation}
                    disabled={declineState==='pending'}
                  >
                    <span>✕</span>
                    <span style={{marginLeft:8}}>Decline</span>
                    <span className="action-feedback" aria-hidden>
                      {declineState==='success' ? '✔' : declineState==='error' ? '✖' : ''}
                    </span>
                  </button>

                </>
              )}

              {data.consultation.status === 'in_progress' && (
                <>
                  <button className="btn btn-primary" onClick={() => navigate(`/doctor/prescription?ref=${encodeURIComponent(data.consultation.consultationId)}`)}>📝 Write Prescription</button>
                  <button className="btn btn-primary" disabled={!data.video?.enabled} onClick={() => window.location.href = `/video?ref=${data.consultation.consultationId}`}>📹 {data.video?.enabled ? "Join Video" : "Video Not Ready"}</button>
                </>
              )}

            </div>

            {!data.video?.enabled && data.consultation.status === "in_progress" && (
              <div className="video-status">⏳ Waiting for nurse to enable video call...</div>
            )}

          </>
        )}

      </div>
    </div>
  );
}
