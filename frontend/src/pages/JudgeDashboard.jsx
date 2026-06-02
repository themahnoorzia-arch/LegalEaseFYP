import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Image, Card, Row, Col, InputGroup, Form, Button, Badge, Table, Modal, ListGroup, Alert, Spinner } from 'react-bootstrap';
import { User, PlusCircle, Search, Calendar, FileText, LogOut } from 'lucide-react';
import JudgeSidebarNav from '../components/dashboard/JudgeSidebarNav';
import '../styles/dashboard.css';

const PROFILE_IMAGE_KEY = 'judgeProfileImage';

function JudgeDashboard() {
  const [activeSection, setActiveSection] = useState('assigned');
  const [profileImage, setProfileImage] = useState(null);
  const [judgeData, setJudgeData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [fallbackWarning, setFallbackWarning] = useState("");
  const navigate = useNavigate();

  const [search, setSearch] = useState('');
  const [status, setStatus] = useState('All');

  const [cases, setCases] = useState([
    
  ]);

  const [showHistoryModal, setShowHistoryModal] = useState(false);
  const [historyCase, setHistoryCase] = useState(null);
  const [showDecisionModal, setShowDecisionModal] = useState(false);
  const [selectedCase, setSelectedCase] = useState(null);
  const [showEvidenceModal, setShowEvidenceModal] = useState(false);
  const [showWitnessesModal, setShowWitnessesModal] = useState(false);
   const [showDocumentsModal, setShowDocumentsModal] = useState(false);
  const [loadingDocuments, setLoadingDocuments] = useState(false);
  const [decisionForm, setDecisionForm] = useState({
    verdict: '',
    summary: '',
    date: new Date().toISOString().split('T')[0]
  });

  const [showAddHearingModal, setShowAddHearingModal] = useState(false);
  const [hearingForm, setHearingForm] = useState({
    caseTitle: '',
    courtName: '',
    hearingDate: '',
    hearingTime: '',
    remarks: ''
  });
  const [hearings, setHearings] = useState([]);
  const today = new Date().toISOString().split('T')[0];

  const filteredCases = cases.filter(case_ => {
    const title = (case_.title || '').toLowerCase();
    const caseType = (case_.caseType || '').toLowerCase();
    const description = (case_.description || '').toLowerCase();
    const q = search.toLowerCase();
    const matchesSearch =
      title.includes(q) || caseType.includes(q) || description.includes(q);
    const matchesStatus = status === 'All' || case_.status === status;
    return matchesSearch && matchesStatus;
  });

  const [documents, setDocuments] = useState([]);
  const [docSearch, setDocSearch] = useState('');
  const [docFilter, setDocFilter] = useState('all');

  const filteredDocuments = documents.filter(doc => {
    const matchesSearch = doc.name.toLowerCase().includes(docSearch.toLowerCase());
    const matchesFilter = docFilter === 'all' || doc.type.toLowerCase() === docFilter.toLowerCase();
    return matchesSearch && matchesFilter;
  });

  const fetchAllDocuments = async () => {
  setLoadingDocuments(true);
  const allDocs = [];

  for (const case_ of cases) {
    try {
      const res = await fetch(`/api/cases/${case_.id}/documents`, {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('userToken')}`,
          'Content-Type': 'application/json',
        },
        credentials: 'include',
      });

      if (res.ok) {
        const data = await res.json();
        const docs = (data.documents || []).map(doc => ({
          id: doc.id,
          name: doc.title,
          type: doc.type,
          uploaded: doc.uploadDate || doc.submissiondate,
          path: doc.path,
        }));
        allDocs.push(...docs);
      }
    } catch (err) {
      console.error(`Failed to fetch documents for case ${case_.id}`, err);
    }
  }

  setDocuments(allDocs);
  setLoadingDocuments(false);
};

useEffect(() => {
  if (activeSection === 'documents') {
    fetchAllDocuments();
  }
}, [activeSection]);


  useEffect(() => {
    const fetchJudgeData = async () => {
      try {
        const response = await fetch('/api/judgeprofile', {
          method: 'GET',
          headers: { 'Content-Type': 'application/json' },
          credentials: 'include',
        });

        if (!response.ok) throw new Error('Failed to fetch judge data');

        const result = await response.json();

        if (result.success) {
          const { firstName, lastName, specialization, position } = result.data;
          setJudgeData({
            username: `${firstName || ''} ${lastName || ''}`.trim() || 'Judge',
            specialization: specialization || position || 'Judiciary',
          });
          const storedImage = localStorage.getItem(PROFILE_IMAGE_KEY);
          setProfileImage(storedImage || 'https://via.placeholder.com/40');
        } else {
          setError('Failed to load user data.');
        }
      } catch (err) {
        setError('Could not load judge profile.');
      } finally {
        setLoading(false);
      }
    };

    fetchJudgeData();
  }, []);

  const [loadingCases, setLoadingCases] = useState(true);
  const [caseError, setCaseError] = useState(null); 

  useEffect(() => {
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

      if (!response.ok) throw new Error('Failed to fetch cases');

      const result = await response.json();
      const caseList = Array.isArray(result.cases) ? result.cases : [];
      setCases(caseList.map(c => ({
        id: c.id || c.caseid,
        title: c.title,
        description: c.description,
        caseType: c.caseType || c.casetype,
        filingDate: c.filingDate || c.filingdate,
        status: c.status,
        lawyers: c.lawyers || 'N/A',
        clientName: c.clientName || '',
        courtName: c.courtName || c.courtname || 'N/A',
        nextHearing: c.nextHearing || 'N/A',
        remarks: c.remarks || '',
        finalDecision: c.finalDecision,
        history: c.history || [],
        evidence: c.evidence || [],
        witnesses: c.witnesses || [],
      })));
    } catch (err) {
      console.error('Error fetching cases:', err);
      setCaseError('Error fetching cases.');
    } finally {
      setLoadingCases(false);
    }
  };

  fetchCases();
}, []);

useEffect(() => {
  const fetchHearings = async () => {
    try {
      const response = await fetch('/api/hearings', {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('userToken')}`,
        },
        credentials: 'include',
      });

      if (!response.ok) {
        throw new Error('Failed to fetch hearings');
      }

      const result = await response.json();
      if (result.hearings) {
        setHearings(result.hearings.map(h => ({
          id: h.hearingid || h.id,
          casetitle: h.casename || h.casetitle || 'N/A',
          courtname: h.courtname || h.courtroomno || 'N/A',
          hearingdate: h.hearingdate,
          hearingtime: h.hearingtime,
          remarks: h.remarks || '',
        })));
      }
    } catch (err) {
      console.error('Error fetching hearings:', err);
    }
  };

  fetchHearings();
}, []);


  const handleProfileClick = () => {
    navigate('/judge-profile');
  };

  const handleViewHistory = (case_) => {
    setHistoryCase(case_);
    setShowHistoryModal(true);
  };

  const handleViewEvidence = (case_) => {
    setSelectedCase(case_);
    setShowEvidenceModal(true);
  };

  const handleViewWitnesses = (case_) => {
    setSelectedCase(case_);
    setShowWitnessesModal(true);
  };

  const handleAnnounceDecision = (case_) => {
    setSelectedCase(case_);
    setDecisionForm({
      verdict: case_.finalDecision || '',
      summary: '',
      date: new Date().toISOString().split('T')[0]
    });
    setShowDecisionModal(true);
  };

  const handleDecisionSubmit = async (e) => {
  e.preventDefault();
  if (!selectedCase) return;

  try {
    const res = await fetch(`/api/cases/${selectedCase.id}/final-decision`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${localStorage.getItem('userToken')}`,
      },
      credentials: 'include',
      body: JSON.stringify({
        verdict: decisionForm.verdict,
        decisionsummary: decisionForm.summary,
        decisiondate: decisionForm.date,
      }),
    });

    const result = await res.json();

    if (!res.ok) {
      throw new Error(result.message || 'Failed to submit final decision');
    }

    // Optionally update the case list or mark case as completed in UI
    setCases(cases.map(c =>
      c.id === selectedCase.id
        ? {
            ...c,
            finalDecision: decisionForm.verdict,
            status: 'Completed',
            history: [
              ...(c.history || []),
              {
                date: decisionForm.date,
                event: `Decision announced: ${decisionForm.verdict}`
              }
            ]
          }
        : c
    ));

    setShowDecisionModal(false);
  } catch (err) {
    alert(`Error: ${err.message}`);
  }
};


  const handleHearingFormChange = (e) => {
    const { name, value } = e.target;
    setHearingForm(prev => ({ ...prev, [name]: value }));
  };

  const handleAddHearing = async (e) => {
  e.preventDefault();
  if (hearingForm.hearingDate < today) {
    alert('Cannot schedule hearings for past dates.');
    return;
  }

  try {
    const response = await fetch('/api/hearings', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${localStorage.getItem('userToken')}`,
      },
      credentials: 'include',
      body: JSON.stringify({
        casetitle: hearingForm.caseTitle,
        courtname: hearingForm.courtName,
        hearingdate: hearingForm.hearingDate,
        hearingtime: hearingForm.hearingTime,
        remarks: hearingForm.remarks || null
      }),
    });

    const result = await response.json();

    if (!response.ok) {
      throw new Error(result.error || 'Failed to schedule hearing');
    }

    // Refresh hearings or append new one (if API returns it)
    // You can optionally re-fetch all hearings or optimistically update:
    setHearings(prev => [
      ...prev,
      {
        id: Date.now(),
        casetitle: hearingForm.caseTitle,
        courtname: hearingForm.courtName,
        hearingdate: hearingForm.hearingDate,
        hearingtime: hearingForm.hearingTime,
        remarks: hearingForm.remarks || ''
      }
    ]);

    setShowAddHearingModal(false);
    setHearingForm({ caseTitle: '', courtName: '', hearingDate: '', hearingTime: '', remarks: '' });

  } catch (err) {
    console.error('Error scheduling hearing:', err);
    alert('Error scheduling hearing: ' + err.message);
  }
};

const updateHearingRemarks = async (hearingId, remarks) => {
  try {
    const response = await fetch(`/api/hearings/remarks?hearingid=${hearingId}`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${localStorage.getItem('userToken')}`,
      },
      credentials: 'include',
      body: JSON.stringify({ remarks }),
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.error || 'Failed to update remarks');
    }

    return true;
  } catch (error) {
    console.error('Error updating hearing remarks:', error);
    return false;
  }
};


  // Documents: fetch from backend
  const handleViewDocuments = async (case_) => {
  setSelectedCase(case_);
  setShowDocumentsModal(true);
  setLoadingDocuments(true);
  try {
    const response = await fetch(`/api/cases/${case_.id}/documents`, {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('userToken')}`,
        'Content-Type': 'application/json'
      },
      credentials: 'include'
    });
    const data = await response.json();
    setDocuments(
      (data.documents || []).map(doc => ({
        id: doc.id,
        name: doc.title,
        type: doc.type,
        uploaded: doc.uploadDate || doc.submissiondate,
        path: doc.path,
      }))
    );
  } catch (err) {
    setDocuments([]);
  } finally {
    setLoadingDocuments(false);
  }
};

 const handleAddRemarks = async (hearingId) => {
  const remarks = prompt('Enter remarks for this hearing:');
  if (remarks !== null) {
    const success = await updateHearingRemarks(hearingId, remarks);
    if (success) {
      setHearings(hearings.map(h => h.id === hearingId ? { ...h, remarks } : h));
    } else {
      alert('Failed to update remarks. Please try again.');
    }
  }
};

  const handleLogout = () => {
    localStorage.clear();
    navigate('/login');
  };

  const todaysHearings = hearings.filter(
    (h) => h.hearingdate && String(h.hearingdate).startsWith(today)
  );

  const renderContent = () => {
    if (activeSection === 'assigned') {
      return (
        <Card className="mb-4 border-0 shadow-sm">
          <Card.Header className="bg-white border-bottom-0 pb-0">
            <h4 className="mb-0 fw-bold" style={{ color: '#22304a' }}>Assigned Cases</h4>
          </Card.Header>
          <Card.Body className="pt-3">
            <Row className="g-2 mb-3">
              <Col md={8}>
                <InputGroup>
                  <InputGroup.Text><Search size={16} /></InputGroup.Text>
                  <Form.Control
                    placeholder="Search by case name, type, or description..."
                    value={search}
                    onChange={(e) => setSearch(e.target.value)}
                  />
                </InputGroup>
              </Col>
              <Col md={4}>
                <Form.Select value={status} onChange={(e) => setStatus(e.target.value)}>
                  <option value="All">All Statuses</option>
                  <option value="Open">Open</option>
                  <option value="Pending">Pending</option>
                  <option value="In Progress">In Progress</option>
                  <option value="Completed">Completed</option>
                </Form.Select>
              </Col>
            </Row>
            {loadingCases ? (
              <div className="text-center py-5"><Spinner animation="border" /></div>
            ) : (
              <div className="table-responsive" style={{ maxHeight: 480, overflowY: 'auto' }}>
                <Table hover className="align-middle mb-0">
                  <thead className="table-light">
                    <tr>
                      <th>Case Title</th>
                      <th>Court</th>
                      <th>Lawyers</th>
                      <th>Filing Date</th>
                      <th>Status</th>
                      <th>Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {filteredCases.length === 0 ? (
                      <tr>
                        <td colSpan={6} className="text-center text-muted py-4">No cases assigned.</td>
                      </tr>
                    ) : (
                      filteredCases.map((case_) => (
                        <tr key={case_.id}>
                          <td>
                            <div className="fw-bold">{case_.title}</div>
                            <small className="text-muted">{case_.description}</small>
                          </td>
                          <td>{case_.courtName}</td>
                          <td>{case_.lawyers}</td>
                          <td>{case_.filingDate}</td>
                          <td>
                            <Badge bg={case_.status === 'Open' ? 'success' : case_.status === 'Completed' ? 'secondary' : 'warning'}>
                              {case_.status}
                            </Badge>
                          </td>
                          <td>
                            <div className="d-flex flex-wrap gap-1">
                              <Button variant="outline-primary" size="sm" onClick={() => handleViewHistory(case_)}>History</Button>
                              <Button variant="outline-info" size="sm" onClick={() => handleViewEvidence(case_)}>Evidence</Button>
                              <Button variant="outline-secondary" size="sm" onClick={() => handleViewWitnesses(case_)}>Witnesses</Button>
                              {case_.status !== 'Completed' && (
                                <Button variant="outline-success" size="sm" onClick={() => handleAnnounceDecision(case_)}>Decision</Button>
                              )}
                            </div>
                          </td>
                        </tr>
                      ))
                    )}
                  </tbody>
                </Table>
              </div>
            )}
          </Card.Body>
        </Card>
      );
    }

    if (activeSection === 'schedule') {
      return (
        <Row className="g-3">
          <Col lg={8}>
            <Card className="border-0 shadow-sm h-100">
              <Card.Header className="bg-white border-bottom d-flex justify-content-between align-items-center">
                <h4 className="mb-0 fw-bold" style={{ color: '#22304a' }}>Hearing Schedule</h4>
                <Button
                  size="sm"
                  className="d-flex align-items-center gap-2"
                  style={{ background: 'linear-gradient(90deg, #22304a 0%, #1ec6b6 100%)', border: 'none' }}
                  onClick={() => setShowAddHearingModal(true)}
                >
                  <PlusCircle size={16} /> Schedule Hearing
                </Button>
              </Card.Header>
              <Card.Body>
                <Table responsive hover className="align-middle">
                  <thead className="table-light">
                    <tr>
                      <th>Case</th>
                      <th>Court</th>
                      <th>Date</th>
                      <th>Time</th>
                      <th>Remarks</th>
                      <th>Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {hearings.length === 0 ? (
                      <tr>
                        <td colSpan={6} className="text-center text-muted py-4">No hearings scheduled.</td>
                      </tr>
                    ) : (
                      hearings.map((hearing) => (
                        <tr key={hearing.id}>
                          <td>{hearing.casetitle}</td>
                          <td>{hearing.courtname}</td>
                          <td>{hearing.hearingdate}</td>
                          <td>{hearing.hearingtime}</td>
                          <td>{hearing.remarks || <span className="text-muted">—</span>}</td>
                          <td>
                            <Button variant="outline-warning" size="sm" onClick={() => handleAddRemarks(hearing.id)}>
                              {hearing.remarks ? 'Edit Remarks' : 'Add Remarks'}
                            </Button>
                          </td>
                        </tr>
                      ))
                    )}
                  </tbody>
                </Table>
              </Card.Body>
            </Card>
          </Col>
          <Col lg={4}>
            <Card className="border-0 shadow-sm h-100">
              <Card.Header className="bg-white border-bottom">
                <h5 className="mb-0 fw-bold" style={{ color: '#22304a' }}>Today&apos;s Hearings</h5>
              </Card.Header>
              <Card.Body>
                {todaysHearings.length === 0 ? (
                  <div className="text-center text-muted py-4">
                    <Calendar size={40} className="mb-2 opacity-50" />
                    <p className="mb-0">No hearings today</p>
                  </div>
                ) : (
                  todaysHearings.map((hearing) => (
                    <div key={hearing.id} className="mb-3 p-3 border rounded-3">
                      <h6 className="mb-1">{hearing.casetitle}</h6>
                      <small className="text-muted d-block">{hearing.courtname}</small>
                      <small className="text-muted d-block">{hearing.hearingtime}</small>
                      {hearing.remarks && <p className="mb-0 mt-2 small">{hearing.remarks}</p>}
                    </div>
                  ))
                )}
              </Card.Body>
            </Card>
          </Col>
        </Row>
      );
    }

    if (activeSection === 'documents') {
      return (
        <Card className="border-0 shadow-sm">
          <Card.Header className="bg-white border-bottom">
            <h4 className="mb-0 fw-bold" style={{ color: '#22304a' }}>Documents</h4>
          </Card.Header>
          <Card.Body>
            <InputGroup className="mb-3">
              <InputGroup.Text><Search size={16} /></InputGroup.Text>
              <Form.Control
                placeholder="Search documents..."
                value={docSearch}
                onChange={(e) => setDocSearch(e.target.value)}
              />
              <Form.Select value={docFilter} onChange={(e) => setDocFilter(e.target.value)} style={{ maxWidth: 160 }}>
                <option value="all">All Types</option>
                <option value="pdf">PDF</option>
                <option value="docx">DOCX</option>
              </Form.Select>
            </InputGroup>
            {loadingDocuments ? (
              <div className="text-center py-4"><Spinner animation="border" /></div>
            ) : filteredDocuments.length > 0 ? (
              <ListGroup variant="flush">
                {filteredDocuments.map((doc, idx) => (
                  <ListGroup.Item key={doc.id || idx} className="d-flex justify-content-between align-items-center py-3">
                    <div className="d-flex align-items-center gap-2">
                      <FileText size={20} className="text-secondary" />
                      <span className="fw-medium">{doc.name}</span>
                    </div>
                    <Button variant="outline-primary" size="sm" onClick={() => doc.path && window.open(doc.path, '_blank')}>
                      View
                    </Button>
                  </ListGroup.Item>
                ))}
              </ListGroup>
            ) : (
              <p className="text-center text-muted mb-0">No documents found.</p>
            )}
          </Card.Body>
        </Card>
      );
    }

    return null;
  };

  if (loading) {
    return (
      <div className="d-flex justify-content-center align-items-center" style={{ height: '100vh' }}>
        <Spinner animation="border" />
      </div>
    );
  }

  return (
    <div style={{ minHeight: '100vh', width: '100vw', overflow: 'hidden', background: '#f8f9fa', display: 'flex', flexDirection: 'column' }}>
      {(fallbackWarning || caseError) && (
        <Alert variant="warning" className="mb-0 rounded-0 text-center py-2">
          {fallbackWarning || caseError}
        </Alert>
      )}
      {error && (
        <Alert variant="danger" className="mb-0 rounded-0 text-center py-2">{error}</Alert>
      )}

      <div className="dashboard-header-gradient p-3" style={{ flex: '0 0 auto', background: 'linear-gradient(90deg, #22304a 0%, #1ec6b6 100%)' }}>
        <div className="d-flex justify-content-between align-items-center">
          <div className="d-flex align-items-center gap-3">
            <h4 className="mb-0" style={{ color: '#fff', fontWeight: 700 }}>Judge Dashboard</h4>
            <span style={{ color: 'rgba(255,255,255,0.7)' }}>|</span>
            <div className="d-flex align-items-center gap-2">
              <Image
                src={profileImage || 'https://via.placeholder.com/40'}
                roundedCircle
                width={40}
                height={40}
                className="border"
                style={{ borderColor: '#fff' }}
              />
              <div>
                <h6 className="mb-0" style={{ color: '#fff', fontWeight: 600 }}>{judgeData?.username}</h6>
                <small style={{ color: 'rgba(255,255,255,0.85)' }}>{judgeData?.specialization}</small>
              </div>
            </div>
          </div>
          <div className="d-flex align-items-center gap-3">
            <button
              type="button"
              className="btn d-flex align-items-center gap-2"
              onClick={handleProfileClick}
              style={{ background: 'rgba(255,255,255,0.12)', color: '#fff', borderColor: '#fff', fontWeight: 600 }}
            >
              <User size={20} color="#fff" />
              Profile
            </button>
            <button
              type="button"
              className="btn d-flex align-items-center gap-2"
              onClick={handleLogout}
              style={{ background: 'rgba(255,255,255,0.12)', color: '#fff', borderColor: '#fff', fontWeight: 600 }}
            >
              <LogOut size={20} color="#fff" />
              Logout
            </button>
          </div>
        </div>
      </div>

      <div style={{ flex: '1 1 0', display: 'flex', width: '100%', minHeight: 0 }}>
        <div className="border-end bg-white" style={{ width: 250, flex: '0 0 250px', minHeight: 0 }}>
          <JudgeSidebarNav activeView={activeSection} onViewChange={setActiveSection} />
        </div>
        <div style={{ flex: 1, overflowY: 'auto', padding: '1.25rem' }}>
          {renderContent()}
        </div>
      </div>

      {/* Add Hearing Modal */}
      <Modal show={showAddHearingModal} onHide={() => setShowAddHearingModal(false)} centered>
        <Modal.Header closeButton>
          <Modal.Title>Schedule New Hearing</Modal.Title>
        </Modal.Header>
        <Form onSubmit={handleAddHearing}>
          <Modal.Body>
            <Form.Group className="mb-3">
              <Form.Label>Case Title</Form.Label>
              <Form.Control type="text" name="caseTitle" value={hearingForm.caseTitle} onChange={handleHearingFormChange} required />
            </Form.Group>
            <Form.Group className="mb-3">
              <Form.Label>Court Name</Form.Label>
              <Form.Control type="text" name="courtName" value={hearingForm.courtName} onChange={handleHearingFormChange} required />
            </Form.Group>
            <Form.Group className="mb-3">
              <Form.Label>Hearing Date</Form.Label>
              <Form.Control type="date" name="hearingDate" value={hearingForm.hearingDate} onChange={handleHearingFormChange} min={today} required />
            </Form.Group>
            <Form.Group className="mb-3">
              <Form.Label>Hearing Time</Form.Label>
              <Form.Control type="time" name="hearingTime" value={hearingForm.hearingTime} onChange={handleHearingFormChange} required />
            </Form.Group>
            <Form.Group className="mb-3">
              <Form.Label>Remarks (optional)</Form.Label>
              <Form.Control as="textarea" name="remarks" value={hearingForm.remarks} onChange={handleHearingFormChange} rows={3} />
            </Form.Group>
          </Modal.Body>
          <Modal.Footer>
            <Button variant="secondary" onClick={() => setShowAddHearingModal(false)}>Cancel</Button>
            <Button type="submit" style={{ background: '#1ec6b6', border: 'none' }}>Schedule</Button>
          </Modal.Footer>
        </Form>
      </Modal>
<Modal 
  show={showHistoryModal} 
  onHide={() => setShowHistoryModal(false)}
  centered
  className="event-modal"
>
  <Modal.Header closeButton className="border-0">
    <Modal.Title>Case History: {historyCase?.title || 'Untitled Case'}</Modal.Title>
  </Modal.Header>
  <Modal.Body>
    <ListGroup variant="flush">
      {historyCase?.history && historyCase.history.length > 0 ? (
        historyCase.history.map((event, index) => (
          <ListGroup.Item key={index} className="border-0 mb-3 p-3 rounded-3 shadow-sm">
            <div className="d-flex align-items-center gap-2 mb-2">
              <Badge bg={event.type === 'Hearing' ? 'primary' : 'info'}>
                {event.type || 'Event'}
              </Badge>
              <span className="fw-bold">{event.date}</span>
            </div>
            <p className="mb-0">{event.event}</p>
          </ListGroup.Item>
        ))
      ) : (
        <div className="text-muted text-center">No history available for this case.</div>
      )}
    </ListGroup>
  </Modal.Body>
  <Modal.Footer className="border-0">
    <Button variant="light" onClick={() => setShowHistoryModal(false)}>
      Close
    </Button>
  </Modal.Footer>
</Modal>


      {/* Witnesses Modal */}
      <Modal 
        show={showWitnessesModal} 
        onHide={() => setShowWitnessesModal(false)}
        centered
        className="event-modal"
      >
        <Modal.Header closeButton className="border-0">
          <Modal.Title>Case Witnesses</Modal.Title>
        </Modal.Header>
        <Modal.Body>
          <ListGroup variant="flush">
            {selectedCase?.witnesses.map((witness, index) => (
              <ListGroup.Item key={index} className="border-0 mb-3 p-3 rounded-3 shadow-sm">
                <div className="d-flex align-items-center gap-2 mb-2">
                  <Badge bg="info">Witness</Badge>
                  <span className="fw-bold">{witness.firstName} {witness.lastName}</span>
                </div>
                <div className="mb-2">
                  <strong>CNIC:</strong> {witness.cnic}<br />
                  <strong>Phone:</strong> {witness.phone}<br />
                  <strong>Email:</strong> {witness.email}<br />
                  <strong>Address:</strong> {witness.address}
                </div>
                <div>
                  <strong>Past History:</strong>
                  <p className="mb-0">{witness.pastHistory}</p>
                </div>
              </ListGroup.Item>
            ))}
          </ListGroup>
        </Modal.Body>
        <Modal.Footer className="border-0">
          <Button variant="light" onClick={() => setShowWitnessesModal(false)}>
            Close
          </Button>
        </Modal.Footer>
      </Modal>

      {/* Evidence Modal */}
      <Modal 
        show={showEvidenceModal} 
        onHide={() => setShowEvidenceModal(false)}
        centered
        className="event-modal"
      >
        <Modal.Header closeButton className="border-0">
          <Modal.Title>Case Evidence</Modal.Title>
        </Modal.Header>
        <Modal.Body>
          <ListGroup variant="flush">
            {selectedCase?.evidence.map((item, index) => (
              <ListGroup.Item key={index} className="border-0 mb-3 p-3 rounded-3 shadow-sm">
                <div className="d-flex align-items-center gap-2 mb-2">
                  <Badge bg="secondary">{item.type}</Badge>
                  <span className="fw-bold">{item.submittedDate}</span>
                </div>
                <p className="mb-2">{item.description}</p>
                <div className="d-flex align-items-center gap-2">
                  <small className="text-muted">Path: {item.evidencePath}</small>
                  <Button 
                    variant="outline-primary" 
                    size="sm"
                    onClick={() => window.open(item.evidencePath, '_blank')}
                  >
                    View Evidence
                  </Button>
                </div>
              </ListGroup.Item>
            ))}
          </ListGroup>
        </Modal.Body>
        <Modal.Footer className="border-0">
          <Button variant="light" onClick={() => setShowEvidenceModal(false)}>
            Close
          </Button>
        </Modal.Footer>
      </Modal>

      {/* Decision Modal */}
      <Modal 
        show={showDecisionModal} 
        onHide={() => setShowDecisionModal(false)}
        centered
        className="event-modal"
      >
        <Modal.Header closeButton className="border-0">
          <Modal.Title>Announce Final Decision</Modal.Title>
        </Modal.Header>
        <Form onSubmit={handleDecisionSubmit}>
          <Modal.Body>
            <Form.Group className="mb-3">
              <Form.Label>Verdict</Form.Label>
              <Form.Select
                name="verdict"
                value={decisionForm.verdict}
                onChange={(e) => setDecisionForm({...decisionForm, verdict: e.target.value})}
                required
              >
                <option value="">Select Verdict</option>
                <option value="Guilty">Guilty</option>
                <option value="Not Guilty">Not Guilty</option>
                <option value="Dismissed">Dismissed</option>
              </Form.Select>
            </Form.Group>
            <Form.Group className="mb-3">
              <Form.Label>Decision Date</Form.Label>
              <Form.Control
                type="date"
                name="date"
                value={decisionForm.date}
                onChange={(e) => setDecisionForm({...decisionForm, date: e.target.value})}
                required
              />
            </Form.Group>
            <Form.Group className="mb-3">
              <Form.Label>Summary</Form.Label>
              <Form.Control
                as="textarea"
                name="summary"
                value={decisionForm.summary}
                onChange={(e) => setDecisionForm({...decisionForm, summary: e.target.value})}
                rows={4}
                placeholder="Provide a detailed summary of the decision..."
                required
              />
            </Form.Group>
          </Modal.Body>
          <Modal.Footer className="border-0">
            <Button variant="light" onClick={() => setShowDecisionModal(false)}>
              Cancel
            </Button>
            <Button variant="primary" type="submit">
              Announce Decision
            </Button>
          </Modal.Footer>
        </Form>
      </Modal>

      <style>{`
        .table thead th { color: #22304a !important; font-weight: 700; }
        .btn-primary { background: #1ec6b6 !important; border-color: #1ec6b6 !important; }
      `}</style>
    </div>
  );
}

export default JudgeDashboard;
