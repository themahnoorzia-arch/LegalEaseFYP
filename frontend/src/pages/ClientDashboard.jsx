import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Card, Button, Image } from 'react-bootstrap';
import { User } from 'lucide-react';
import ClientCases from '../components/ClientCases';
import ClientHearingSchedule from '../components/ClientHearingSchedule';
import CaseDocuments from '../components/CaseDocuments';
import Profile from '../components/ClientProfile';
import Notifications from '../components/dashboard/Notifications';
import 'bootstrap/dist/css/bootstrap.min.css';

function ClientDashboard() {
  const [activeSection, setActiveSection] = useState('cases');
  const [profileImage, setProfileImage] = useState(`/api/profile/photo/me?t=${Date.now()}`);
  const photoInputRef = React.useRef(null);
  const handlePhotoUpload = async (e) => {
    const file = e.target.files[0];
    if (!file) return;
    const fd = new FormData();
    fd.append('photo', file);
    try {
      const res = await fetch('/api/profile/photo', { method: 'POST', credentials: 'include', body: fd });
      if (res.ok) setProfileImage(`/api/profile/photo/me?t=${Date.now()}`);
    } catch { /* silent */ }
  };
  const [clientProfile, setClientProfile] = useState(null);
  const navigate = useNavigate();

  const [cases, setCases] = useState([]);
  const [loadingCases, setLoadingCases] = useState(true);
  const [caseError, setCaseError] = useState(null);

  useEffect(() => {
    // Fetch client profile once on mount
    const fetchClientProfile = async () => {
      try {
        const response = await fetch('/api/clientprofile', {
          method: 'GET',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${localStorage.getItem('userToken')}`,
          },
          credentials: 'include',
        });
        if (!response.ok) throw new Error('Failed to fetch client profile');
        const result = await response.json();
        if (result.success && result.data) {
          setClientProfile(result.data);
        } else {
          console.error('Failed to load client profile:', result.message);
        }
      } catch (err) {
        console.error('Error fetching client profile:', err);
      }
    };

    fetchClientProfile();
  }, []);

  useEffect(() => {
    // Fetch cases on mount
    const fetchCases = async () => {
      try {
        const response = await fetch('/api/cases', {
          method: 'GET',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${localStorage.getItem('userToken')}`,
          },
          credentials: 'include',
        });

        if (!response.ok) {
          throw new Error('Failed to fetch cases');
        }

        const result = await response.json();
        if (result.cases) {
          const mappedCases = result.cases.map((c) => ({
            id: c.id || c.caseid,
            title: c.title,
            description: c.description,
            caseType: c.caseType || c.casetype,
            filingDate: c.filingDate || c.filingdate,
            status: c.status,
            lawyers: c.lawyers || 'N/A',
            courtName: c.courtName || 'N/A',
            nextHearing: c.nextHearing || 'N/A',
            history: c.history || [],
            evidence: c.evidence || [],
            witnesses: c.witnesses || [],
            finalDecision: c.finalDecision || null,
          }));

          setCases(mappedCases);
        } else {
          setCaseError('No cases found.');
        }
      } catch (err) {
        console.error('Error fetching cases:', err);
        setCaseError('Error fetching cases.');
      } finally {
        setLoadingCases(false);
      }
    };

    fetchCases();
  }, []);

  const handleProfileClick = () => {
    setActiveSection('profile');
  };

  const handleLogout = () => {
    localStorage.clear();
    navigate('/login');
  };

  return (
    <div style={{ minHeight: '100vh', width: '100vw', overflow: 'hidden', background: '#f8f9fa', display: 'flex', flexDirection: 'column' }}>
      {/* Top Navigation Bar */}
      <div className="dashboard-header-gradient p-3" style={{ flex: '0 0 auto', background: 'linear-gradient(90deg, #22304a 0%, #1ec6b6 100%)' }}>
        <div className="d-flex justify-content-between align-items-center">
          <div className="d-flex align-items-center gap-3">
            <h4 className="mb-0" style={{ color: '#fff', fontWeight: 700 }}>Client Dashboard</h4>
            <span style={{ color: 'rgba(255,255,255,0.7)' }}>|</span>
            <div className="d-flex align-items-center gap-2">
              <input type="file" accept="image/*" ref={photoInputRef} onChange={handlePhotoUpload} className="d-none" />
              <Image
                src={profileImage}
                roundedCircle
                width={40}
                height={40}
                className="border"
                style={{ borderColor: '#fff', cursor: 'pointer' }}
                onClick={() => photoInputRef.current?.click()}
                onError={e => { e.target.onerror = null; e.target.src = 'https://via.placeholder.com/40'; }}
              />
              <div>
                <h6 className="mb-0" style={{ color: '#fff', fontWeight: 600 }}>
                  {clientProfile ? `${clientProfile.firstName} ${clientProfile.lastName}` : 'Client'}
                </h6>
                <small style={{ color: 'rgba(255,255,255,0.85)' }}>Client</small>
              </div>
            </div>
          </div>
          <div className="d-flex align-items-center gap-3">
            <div style={{ color: '#fff' }}><Notifications /></div>
            <button
              className="btn btn-outline-primary d-flex align-items-center gap-2"
              onClick={handleProfileClick}
              style={{ background: 'rgba(255,255,255,0.12)', color: '#fff', borderColor: '#fff', fontWeight: 600 }}
            >
              <User size={20} color="#fff" />
              Profile
            </button>
            <button
              className="btn btn-outline-danger d-flex align-items-center gap-2 logout-btn"
              onClick={handleLogout}
              style={{ background: 'rgba(255,255,255,0.12)', color: '#fff', borderColor: '#fff', fontWeight: 600 }}
            >
              Logout
            </button>
          </div>
        </div>
      </div>

      <div style={{ flex: '1 1 0', display: 'flex', width: '100%', height: '100%', minHeight: 0 }}>
        {/* Sidebar */}
        <div style={{
          background: 'linear-gradient(135deg, #1ec6b6 0%, #22304a 100%)',
          borderTopRightRadius: 18,
          borderBottomRightRadius: 18,
          boxShadow: '2px 0 16px 0 rgba(34,48,74,0.08)',
          padding: '18px 0 18px 0',
          minHeight: '100vh',
          color: '#fff',
          width: 200,
          display: 'flex',
          flexDirection: 'column',
          justifyContent: 'flex-start',
        }}>
          <div style={{ fontWeight: 700, fontSize: 20, padding: '0 24px 18px 24px', letterSpacing: 1 }}>
            <i className="bi bi-person" style={{ fontSize: 22, color: '#fff', marginRight: 8 }}></i>
            Client Panel
          </div>
          <div className="d-flex flex-column gap-1">
            {['cases', 'hearings', 'documents', 'profile'].map((section) => (
              <div
                key={section}
                className={`d-flex align-items-center sidebar-link px-3 py-2 border-0 rounded-2 ${activeSection === section ? 'bg-white text-primary fw-bold shadow-sm' : 'text-white'}`}
                style={{
                  background: activeSection === section ? '#fff' : 'transparent',
                  color: activeSection === section ? '#1ec6b6' : '#fff',
                  fontWeight: activeSection === section ? 700 : 500,
                  fontSize: 15,
                  borderLeft: activeSection === section ? '4px solid #1ec6b6' : '4px solid transparent',
                  marginBottom: 2,
                  transition: 'all 0.18s',
                  boxShadow: activeSection === section ? '0 2px 8px rgba(30,198,182,0.08)' : 'none',
                  cursor: 'pointer',
                }}
                onClick={() => setActiveSection(section)}
                onMouseEnter={e => {
                  if (activeSection !== section) {
                    e.currentTarget.style.background = 'rgba(255,255,255,0.18)';
                    e.currentTarget.style.color = '#1ec6b6';
                    e.currentTarget.style.boxShadow = '0 2px 8px rgba(30,198,182,0.12)';
                  }
                }}
                onMouseLeave={e => {
                  if (activeSection !== section) {
                    e.currentTarget.style.background = 'transparent';
                    e.currentTarget.style.color = '#fff';
                    e.currentTarget.style.boxShadow = 'none';
                  }
                }}
              >
                <span className="me-2"></span>
                <span style={{ fontSize: 14 }}>{section === 'cases' ? 'Cases' : section === 'hearings' ? 'Hearings' : section === 'documents' ? 'Documents' : 'Profile'}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Main Content */}
        <div style={{ flex: 1, overflowY: 'auto', display: 'flex', flexDirection: 'column' }}>
          <div className="container-fluid py-4">
            {activeSection === 'cases' && <ClientCases cases={cases} loading={loadingCases} error={caseError} />}
            {activeSection === 'hearings' && <ClientHearingSchedule />}
            {activeSection === 'documents' && <CaseDocuments cases={cases} userRole="Client" />}
            {activeSection === 'profile' && <Profile profile={clientProfile} />}
          </div>
        </div>
      </div>

      <style>{`
        .dashboard-heading, .dashboard-gradient, .modal-title, .card-title, .card-header h4, .card-header h5, h4.fw-bold, h5.fw-bold {
          background: linear-gradient(90deg, #22304a 0%, #1ec6b6 100%);
          -webkit-background-clip: text;
          -webkit-text-fill-color: transparent;
          background-clip: text;
          text-fill-color: transparent;
        }
        .sidebar-link.bg-white.text-primary {
          background: #fff !important;
          color: #1ec6b6 !important;
        }
        .sidebar-link.text-white:hover {
          background: rgba(255,255,255,0.18) !important;
          color: #1ec6b6 !important;
        }
        .btn-primary, .btn-outline-primary, .btn-link, .btn-info, .btn-success, .btn-warning {
          background: #1ec6b6 !important;
          border-color: #1ec6b6 !important;
          color: #fff !important;
        }
        .btn-primary:hover, .btn-outline-primary:hover, .btn-link:hover, .btn-info:hover, .btn-success:hover, .btn-warning:hover {
          background: #159e8c !important;
          border-color: #159e8c !important;
          color: #fff !important;
        }
        .badge-success, .badge-info, .badge-warning, .badge-secondary {
          background: #1ec6b6 !important;
          color: #fff !important;
        }
        .table thead th {
          color: #22304a !important;
          font-weight: 700;
        }
        .text-primary, .text-info, .text-success, .text-warning, .text-secondary {
          color: #1ec6b6 !important;
        }
        .text-muted {
          color: #6c757d !important;
        }
      `}</style>
    </div>
  );
}

export default ClientDashboard;
