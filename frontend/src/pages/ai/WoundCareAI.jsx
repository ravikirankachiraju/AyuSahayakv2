import React, { useEffect, useState } from 'react';
import NurseNav from '../../components/NurseNav';
import http from '../../api/http';
import AIImageAnalysis from '../../components/AIImageAnalysis';
import { useNavigate } from 'react-router-dom';

export default function WoundCareAI() {
  const ref = new URLSearchParams(window.location.search).get('ref') || '';
  const [imageUrl, setImageUrl] = useState(null);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  useEffect(() => {
    const fetchPatientImage = async () => {
      try {
        const res = await http.get(`/patients/${ref}`);
        const photos = res.data?.photos || [];
        if (photos.length > 0) setImageUrl(photos[0].url);
      } catch (err) {
        console.error('Error fetching patient image:', err);
        if (err.response?.status === 401) window.location.href = '/login';
      } finally {
        setLoading(false);
      }
    };
    if (ref) fetchPatientImage();
  }, [ref]);

  return (
    <>
      <style>{`
        :root {
          --primary: hsl(4, 85%, 55%); /* 🔴 Red theme for wound */
          --primary-dark: hsl(4, 85%, 45%);
          --bg-surface: #F8FAFC;
          --glass-border: 1px solid rgba(255,255,255,0.5);
          --shadow-lg: 0 20px 25px -5px rgba(0, 0, 0, 0.1), 
                       0 8px 10px -6px rgba(0, 0, 0, 0.1);
        }

        .ai-page {
          min-height: 100vh;
          background: radial-gradient(circle at top left, #fef2f2, #fff);
          font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
          padding-bottom: 4rem;
        }

        .ai-header {
          max-width: 1400px;
          margin: 0 auto;
          padding: 24px 32px;
          display: flex;
          justify-content: space-between;
          align-items: center;
        }

        .header-content h1 {
          font-size: 28px;
          font-weight: 800;
          color: #7f1d1d;
          margin: 0;
          letter-spacing: -0.5px;
          display: flex;
          align-items: center;
          gap: 12px;
        }

        .badge {
          background: #fee2e2;
          color: #b91c1c;
          font-size: 12px;
          padding: 4px 12px;
          border-radius: 20px;
          text-transform: uppercase;
          font-weight: 700;
          letter-spacing: 0.5px;
        }

        .back-btn {
          background: white;
          color: #7f1d1d;
          border: 1px solid #fca5a5;
          padding: 10px 20px;
          border-radius: 10px;
          font-weight: 600;
          transition: all 0.2s;
          display: flex;
          align-items: center;
          gap: 8px;
          cursor: pointer;
        }
        .back-btn:hover {
          border-color: var(--primary);
          color: var(--primary);
          box-shadow: 0 4px 12px rgba(0,0,0,0.05);
        }

        /* GRID */
        .ai-container {
          max-width: 1400px;
          margin: 0 auto;
          padding: 0 32px;
          display: grid;
          grid-template-columns: 1fr;
          gap: 32px;
          animation: slideUp 0.6s cubic-bezier(0.16, 1, 0.3, 1);
        }
        @media (min-width: 1024px) {
          .ai-container {
            grid-template-columns: 400px 1fr;
            align-items: start;
          }
        }

        /* IMAGE CARD */
        .image-card {
          background: white;
          padding: 24px;
          border-radius: 24px;
          box-shadow: var(--shadow-lg);
          border: var(--glass-border);
          position: sticky;
          top: 24px;
          text-align: center;
        }

        .patient-img {
          width: 100%;
          border-radius: 16px;
          object-fit: cover;
          box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
          border: 4px solid white;
        }

        .img-caption {
          margin-top: 16px;
          font-size: 14px;
          color: #7f1d1d;
          font-weight: 500;
        }

        .analysis-area {
          min-width: 0;
        }

        @keyframes slideUp {
          from { opacity: 0; transform: translateY(20px); }
          to { opacity: 1; transform: translateY(0); }
        }
      `}</style>

      <div className="ai-page">
        <NurseNav />
        <div style={{ marginTop: '4rem' }}>
        <header className="ai-header">
          <div className="header-content">
            <h1>
              🩹 WoundCare AI
              <span className="badge">Version 2.0</span>
            </h1>
            <p style={{ color: '#b91c1c', margin: '4px 0 0 0' }}>
              Deep-learning wound analysis & treatment support
            </p>
          </div>
          <button className="back-btn" onClick={() => navigate('/nurse/patients')}>
            <span>←</span> Patient List
          </button>
        </header>

        <main className="ai-container">

          {/* LEFT: Image */}
          <aside className="image-card">
            {loading ? (
              <div style={{padding: '40px', color: '#be123c'}}>Loading image...</div>
            ) : imageUrl ? (
              <>
                <img src={imageUrl} alt="Patient Wound" className="patient-img" />
                <div className="img-caption">
                  Original Scan • {new Date().toLocaleDateString()}
                </div>
              </>
            ) : (
              <div style={{padding: '40px', color: '#ef4444'}}>No Image Source</div>
            )}
          </aside>

          {/* RIGHT: AI Stage UI */}
          <section className="analysis-area">
            {imageUrl && (
              <AIImageAnalysis 
                conditionType="wound" 
                imageUrl={imageUrl} 
                patientRef={ref} 
                consultationRef={ref}
              />
            )}
          </section>

        </main>
        </div>
      </div>
    </>
  );
}