import React, { useState, useEffect, useRef } from 'react';
import { Container, Row, Col, Card, Button, Modal, Form, ListGroup, Nav, Badge, Tab, Toast, Spinner, InputGroup, Table } from 'react-bootstrap';
import { Plus, Building2, Users, Gavel, Briefcase, DollarSign, UserCheck, FileText, Search, Trash2, Edit2, ArrowLeft, Bell, User, Eye, Mail, Phone, MapPin, Award, Upload, Edit3, Save, ChevronLeft, ChevronRight, CalendarIcon, Clock } from 'lucide-react';
import 'bootstrap/dist/css/bootstrap.min.css';
import lawImage from '../assets/law.png'
import { useLocation, useNavigate } from 'react-router-dom';
import Notifications from '../components/dashboard/Notifications';
import CalendarSummary from '../components/dashboard/CalendarSummary';
import moment from 'moment';
import '../components/dashboard/CalendarSummary.css';
import RegistrarHearingSchedule from '../components/dashboard/RegistrarHearingSchedule';


const RegistrarDashboard = () => {
  // Courts state
  const [courts, setCourts] = useState([]);
  const [selectedCourt, setSelectedCourt] = useState(null);
  const [loadingCourts, setLoadingCourts] = useState(true);
  const [courtError, setCourtError] = useState('');
  const [showCourtModal, setShowCourtModal] = useState(false);
  const [courtForm, setCourtForm] = useState({ name: '', location: '', type: '' });
  const [editingCourt, setEditingCourt] = useState(null);
  const [activeTab, setActiveTab] = useState('dashboard');
  const [searchCourt, setSearchCourt] = useState('');
  
  const [judges, setJudges] = useState([]);
  const [activityLogs, setActivityLogs] = useState([]);

  const [showVerifyModal, setShowVerifyModal] = useState(false);
  const [verifyingCase, setVerifyingCase] = useState(null);
  const [verifyForm, setVerifyForm] = useState({
    casename: '',
    type: '',
    filingdate: '',
    clientname: '',
    lawyername: '',
    judgename: '',
    prosecutorname: ''
  });
  const [respondentLawyerId, setRespondentLawyerId] = useState('');
  const [lawyerOptions, setLawyerOptions] = useState([]);
  const [verifyLoading, setVerifyLoading] = useState(false);
  const [verifyError, setVerifyError] = useState('');
  const [verifySuccess, setVerifySuccess] = useState('');
  const [judgeOptions, setJudgeOptions] = useState([]);
  const [prosecutorOptions, setProsecutorOptions] = useState([]);

useEffect(() => {
  const fetchActivityLogs = async () => {
    try {
      const response = await fetch('/api/logs/activity', {
        credentials: 'include',
      });
      if (!response.ok) throw new Error('Failed to fetch activity logs');
      const data = await response.json();
      setActivityLogs(data);
    } catch (err) {
      console.error(err);
      showToast('Error loading activity feed', 'danger');
    }
  };

  fetchActivityLogs();
}, []);


  // Toast state
  const [toast, setToast] = useState({ show: false, message: '', variant: 'success' });

  // Court management state
  const [courtRooms, setCourtRooms] = useState([]);
  const [loadingRooms, setLoadingRooms] = useState(true);
  const [roomError, setRoomError] = useState('');
  const [showRoomModal, setShowRoomModal] = useState(false);
  const [roomForm, setRoomForm] = useState({ number: '', name: '', capacity: '', type: '', status: '' });
  const [editingRoom, setEditingRoom] = useState(null);
  const [searchRoom, setSearchRoom] = useState('');

  const [courtJudges, setCourtJudges] = useState([
    { id: 1, name: 'Judge Judy', position: 'Chief Judge', experience: 15, appointmentDate: '2010-05-01', specialization: 'Criminal Law', assignedCases: ['State v. Smith'] },
    { id: 2, name: 'Judge Dredd', position: 'Senior Judge', experience: 10, appointmentDate: '2015-03-15', specialization: 'Civil Law', assignedCases: ['People v. Doe'] },
  ]);
  const [searchJudge, setSearchJudge] = useState('');
  const [showJudgeModal, setShowJudgeModal] = useState(false);
  const [editingJudge, setEditingJudge] = useState(null);
  const [judgeForm, setJudgeForm] = useState({
    name: '',
    position: '',
    experience: '',
    appointmentDate: '',
    specialization: '',
    assignedCases: []
  });

  const [courtProsecutors, setCourtProsecutors] = useState([
    { id: 1, name: 'Alex Mason', experience: 5, status: 'Active', assignedCases: ['State v. Smith'] },
    { id: 2, name: 'Sam Fisher', experience: 3, status: 'Active', assignedCases: ['People v. Doe'] },
    { id: 3, name: 'Lara Croft', experience: 7, status: 'Active', assignedCases: [] },
  ]);
  const [searchProsecutor, setSearchProsecutor] = useState('');
  const [courtPayments, setCourtPayments] = useState([
  ]);
  const [searchPayment, setSearchPayment] = useState('');
  const [showPaymentModal, setShowPaymentModal] = useState(false);
  const [editingPayment, setEditingPayment] = useState(null);
  const [paymentForm, setPaymentForm] = useState({
    caseid: '',
    purpose: '',
    balance: '',
    paymenttype: 'Court Fee',
  });
  const [paymentSubmitting, setPaymentSubmitting] = useState(false);
  const [paymentSubmitError, setPaymentSubmitError] = useState('');
  const [loadingPayments, setLoadingPayments] = useState(true);  
useEffect(() => {
  const fetchPayments = async () => {
    try {
      setLoadingPayments(true);
      const response = await fetch('/api/payments', {
        method: 'GET',
        credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
      });

      if (!response.ok) throw new Error('Failed to fetch payments');

      const data = await response.json();

      const mappedPayments = (data.payments || []).map((p, index) => ({
        id: p.paymentid || index + 1,
        caseName: p.casename || '',
        lawyerName: p.lawyer_name || p.lawyername || '—',
        clientName: '—',
        paymentType: p.paymenttype || 'Court Fee',
        purpose: p.purpose || '',
        amount: p.balance || 0,
        mode: p.mode || '',
        paymentDate: p.paymentdate || '',
        status: p.status || 'Pending',
      }));

      setCourtPayments(mappedPayments);
    } catch (err) {
  console.error('Error fetching payments:', err);
} finally {
      setLoadingPayments(false);
    }
  };

  fetchPayments();
}, []);


  const handleSubmitPayment = async (e) => {
    e.preventDefault();
    setPaymentSubmitting(true);
    setPaymentSubmitError('');
    try {
      const response = await fetch('/api/payments', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          caseid: paymentForm.caseid,
          purpose: paymentForm.purpose,
          balance: paymentForm.balance,
          paymenttype: paymentForm.paymenttype,
        }),
        credentials: 'include',
      });
      const data = await response.json();
      if (!response.ok) throw new Error(data.message || 'Failed to create payment request');
      showToast('Payment request created — lawyer will be notified.', 'success');
      setShowPaymentModal(false);
      setPaymentForm({ caseid: '', purpose: '', balance: '', paymenttype: 'Court Fee' });
      // Refresh payments list
      const refreshed = await fetch('/api/payments', { credentials: 'include' });
      const refreshedData = await refreshed.json();
      const mapped = (refreshedData.payments || []).map((p, i) => ({
        id: p.paymentid || i + 1,
        caseName: p.casename || '',
        lawyerName: p.lawyer_name || p.lawyername || '—',
        clientName: '—',
        paymentType: p.paymenttype || 'Court Fee',
        purpose: p.purpose || '',
        amount: p.balance || 0,
        mode: p.mode || '',
        paymentDate: p.paymentdate || '',
        status: p.status || 'Pending',
      }));
      setCourtPayments(mapped);
    } catch (err) {
      setPaymentSubmitError(err.message);
    } finally {
      setPaymentSubmitting(false);
    }
  };


  
  const [courtAppeals, setCourtAppeals] = useState([]);
  const [courtCases, setCourtCases] = useState([]);
  const [errorCases, setErrorCases] = useState(null);
  const [loadingCases, setLoadingCases] = useState(true);
  const [error, setError] = useState(null);
  const [joinRequests, setJoinRequests] = useState([]);
  const [joinRequestsLoading, setJoinRequestsLoading] = useState(false);

  // Fetch court cases for CourtRegistrar role
  useEffect(() => {
  const fetchCourtCases = async () => {
    try {
      const response = await fetch('/api/cases', {
        credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
      });
      if (!response.ok) {
        throw new Error('Failed to fetch cases');
      }
      const data = await response.json();
      const mappedCases = (data.cases || []).map(c => ({
        ...c,
        clientName: c.clientName ?? c.clientname ?? 'N/A',
        lawyername: c.lawyername ?? c.lawyerName ?? 'N/A',
        prosecutor: c.prosecutorName ?? c.prosecutor ?? 'N/A',
      }));
      setCourtCases(mappedCases);
      setLoadingCases(false); 
    } catch (err) {
      setError(err.message);
      setLoadingCases(false); 
    }
  };

  fetchCourtCases();
}, []);

// Fetch pending join requests for registrar
const fetchJoinRequests = async () => {
  try {
    setJoinRequestsLoading(true);
    const res = await fetch('/api/registrar/join-requests', {
      method: 'GET',
      credentials: 'include',
      headers: { 'Content-Type': 'application/json' },
    });
    if (!res.ok) throw new Error('Failed to fetch join requests');
    const data = await res.json();
    setJoinRequests(data || []);
  } catch (err) {
    console.error('Error fetching join requests:', err);
    setJoinRequests([]);
  } finally {
    setJoinRequestsLoading(false);
  }
};

useEffect(() => {
  fetchJoinRequests();
}, []);

// Approve a join request
const handleApproveJoinRequest = async (lawyerid, caseid) => {
  try {
    setJoinRequestsLoading(true);
    const res = await fetch(`/api/registrar/join-requests/${lawyerid}/${caseid}/approve`, {
      method: 'POST',
      credentials: 'include',
      headers: { 'Content-Type': 'application/json' },
    });
    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.message || 'Failed to approve');
    }
    showToast('Join request approved', 'success');
    await fetchJoinRequests();
  } catch (err) {
    console.error(err);
    showToast(err.message || 'Error approving join request', 'danger');
  } finally {
    setJoinRequestsLoading(false);
  }
};

// Reject a join request
const handleRejectJoinRequest = async (lawyerid, caseid) => {
  if (!window.confirm('Reject this join request?')) return;
  try {
    setJoinRequestsLoading(true);
    const res = await fetch(`/api/registrar/join-requests/${lawyerid}/${caseid}/reject`, {
      method: 'POST',
      credentials: 'include',
      headers: { 'Content-Type': 'application/json' },
    });
    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.message || 'Failed to reject');
    }
    showToast('Join request rejected', 'success');
    await fetchJoinRequests();
  } catch (err) {
    console.error(err);
    showToast(err.message || 'Error rejecting join request', 'danger');
  } finally {
    setJoinRequestsLoading(false);
  }
};

  const [searchCase, setSearchCase] = useState('');

  // Loading state
  const [loading, setLoading] = useState(false);
  
  const [confirm, setConfirm] = useState({ show: false, type: '', payload: null });

  // Add state for tab selection
  const [selectedPage, setSelectedPage] = useState('dashboard');

  // Add state and handlers for appeals management at the top of the component
  const [showAppealModal, setShowAppealModal] = useState(false);
  const [editingAppeal, setEditingAppeal] = useState(null);
  const [appealForm, setAppealForm] = useState({ appealNumber: '', originalCaseId: '', appellant: '', respondent: '', dateFiled: '', status: '' });
  const [searchAppeal, setSearchAppeal] = useState('');
  // Appeals state: update to include lawyerName, caseName, clientName, appealDate, status, decisionDate, decision
  const [appeals, setAppeals] = useState([]);
const getAppeals = async () => {
  try {
    const response = await fetch('/api/appeals', {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
      credentials: 'include',
    });
    if (!response.ok) throw new Error(`Error ${response.status}`);
    const data = await response.json();

    // Map backend fields to frontend fields
  const mappedAppeals = data.appeals.map(appeal => ({
  appealId: appeal.appealid,             
  appealDate: appeal.appealdate,
  status: appeal.status,
  caseName: appeal.casename,
  courtName: appeal.courtname,
  decision: appeal.decision,
  decisionDate: appeal.decisiondate,
  lawyerName: appeal.lawyername,
  clientName: appeal.clientname
}));


    setAppeals(mappedAppeals);
  } catch (err) {
    console.error('Failed to fetch appeals:', err.message);
  }
};

const fetchProsecutors = async () => {
  try {
    const res = await fetch('/api/prosecutors', {
      credentials: 'include',
    });
    const data = await res.json();
    return data.prosecutors || [];
  } catch (err) {
    console.error('Failed to fetch prosecutors:', err);
    return [];
  }
};

useEffect(() => {
  if (selectedPage === 'judges') {
    const fetchJudges = async () => {
      try {
        const res = await fetch('/api/judges', {
          method: 'GET',
          headers: { 'Content-Type': 'application/json' },
          credentials: 'include'
        });
        if (!res.ok) throw new Error('Failed to fetch judges');
        const data = await res.json();
        setJudges(data.judges || []);
      } catch (err) {
        console.error('Error fetching judges:', err);
      }
    };

    fetchJudges();
  }
}, [selectedPage]);

useEffect(() => {
  if (selectedPage === 'remands') {
    const fetchRemands = async () => {
      try {
        const res = await fetch('/api/remands', {
          method: 'GET',
          headers: { 'Content-Type': 'application/json' },
          credentials: 'include'
        });
        if (!res.ok) throw new Error('Failed to fetch remands');
        const data = await res.json();
        setRemands(data || []);
      } catch (err) {
        console.error('Error fetching remands:', err);
      }
    };

    fetchRemands();
  }
}, [selectedPage]);


const addProsecutor = async (prosecutor) => {
  try {
    const res = await fetch('/api/prosecutor', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'include',
      body: JSON.stringify(prosecutor),
    });
    return await res.json();
  } catch (err) {
    console.error('Failed to add prosecutor:', err);
  }
};

const updateProsecutor = async (id, prosecutor) => {
  try {
    const res = await fetch('/api/prosecutor', {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'include',
      body: JSON.stringify({ id, ...prosecutor }),
    });
    return await res.json();
  } catch (err) {
    console.error('Failed to update prosecutor:', err);
  }
};

const deleteProsecutor = async (id) => {
  try {
    await fetch(`/api/prosecutor/${id}`, {
      method: 'DELETE',
      credentials: 'include',
    });
  } catch (err) {
    console.error('Failed to delete prosecutor:', err);
  }
};

  const filteredAppeals = appeals.filter(a =>
  a.lawyerName?.toLowerCase().includes(searchAppeal.toLowerCase()) ||
  a.caseName?.toLowerCase().includes(searchAppeal.toLowerCase()) ||
  a.clientName?.toLowerCase().includes(searchAppeal.toLowerCase()) ||
  a.status?.toLowerCase().includes(searchAppeal.toLowerCase())
);

  // Add state for modals and forms for rooms and cases
  const [showRoomViewModal, setShowRoomViewModal] = useState(false);
  const [viewingRoom, setViewingRoom] = useState(null);
  const [showCaseModal, setShowCaseModal] = useState(false);
  const [editingCase, setEditingCase] = useState(null);
  const [caseForm, setCaseForm] = useState({
    title: '',
    description: '',
    caseType: '',
    clientName: '',
    lawyerName: '',
    prosecutor: ''
  });
  const [showCaseViewModal, setShowCaseViewModal] = useState(false);
  const [viewingCase, setViewingCase] = useState(null);
  const [loadingTimeline, setLoadingTimeline] = useState(false);
  const [cases, setCases] = useState([
    {
      id: 1,
      title: 'State v. Smith',
      description: 'Criminal case involving theft',
      caseType: 'Criminal',
      filingDate: '2024-01-15',
      status: 'Open',
      decisionDate: '',
      decisionSummary: '',
      verdict: '',
      lawyerName: 'Adeel Khan',
      clientName: 'John Smith',
      judgeName: 'Judge Judy',
    },
    {
      id: 2,
      title: 'People v. Doe',
      description: 'Civil case regarding property dispute',
      caseType: 'Civil',
      filingDate: '2024-02-01',
      status: 'Pending',
      decisionDate: '',
      decisionSummary: '',
      verdict: '',
      lawyerName: 'Sara Malik',
      clientName: 'Jane Doe',
      judgeName: 'Judge Dredd',
    },
    {
      id: 3,
      title: 'Acme Corp v. Beta',
      description: 'Corporate case about contract breach',
      caseType: 'Corporate',
      filingDate: '2024-01-20',
      status: 'Closed',
      decisionDate: '2024-03-15',
      decisionSummary: 'The court found in favor of the plaintiff based on the evidence presented.',
      verdict: 'Plaintiff wins',
      lawyerName: 'Bilal Ahmed',
      clientName: 'Acme Corp',
      judgeName: 'Judge Amy',
    }
  ]);
useEffect(() => {
  setLoadingCourts(true);
  fetch('/api/court', {
    method: 'GET',
    credentials: 'include',
    headers: {
      'Content-Type': 'application/json',
    },
  })
    .then(async (res) => {
      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.message || 'Failed to fetch court');
      }
      return res.json();
    })
    .then((response) => {
      const court = response.data;
      setSelectedCourt(court);
      setLoadingCourts(false);
    })
    .catch((err) => {
      console.error('Error fetching court:', err.message);
      setCourtError('Could not load court details.');
      setLoadingCourts(false);
    });
}, []);

useEffect(() => {
  if (selectedPage === 'courtRooms' && selectedCourt?.id) {
    setLoadingRooms(true);
    fetch(`/api/courtrooms/${selectedCourt.id}`, {
      method: 'GET',
      credentials: 'include',
      headers: { 'Content-Type': 'application/json' },
    })
      .then(async (res) => {
        if (!res.ok) throw new Error('Failed to fetch courtrooms');
        return res.json();
      })
      .then((response) => {
        setCourtRooms(response.data || []);
        setLoadingRooms(false);
      })
      .catch((err) => {
        console.error('Error fetching courtrooms:', err.message);
        setRoomError('Could not load court rooms.');
        setLoadingRooms(false);
      });
  }
}, [selectedPage, selectedCourt]);


const fetchCourtRooms = (courtId) => {
  setLoadingRooms(true);
  fetch(`/api/courtrooms/${courtId}`, {
    method: 'GET',
    credentials: 'include',
    headers: { 'Content-Type': 'application/json' },
  })
    .then(async (res) => {
      if (!res.ok) throw new Error('Failed to fetch courtrooms');
      return res.json();
    })
    .then((response) => {
      setCourtRooms(response.data || []);
      setLoadingRooms(false);
    })
    .catch((err) => {
      console.error('Error fetching courtrooms:', err.message);
      setRoomError('Could not load court rooms.');
      setLoadingRooms(false);
    });
};

useEffect(() => {
  const fetchRegistrarProfile = async () => {
    try {
      const response = await fetch('/api/registrarprofile', {
        method: 'GET',
        credentials: 'include',
      });

      if (!response.ok) throw new Error('Failed to fetch registrar profile');
      const result = await response.json();

      if (result.success) {
        const fullName = `${result.data.firstName} ${result.data.lastName}`;
        const profile = {
          name: fullName,
          email: result.data.email,
          phone: result.data.phone,
          court: result.data.court,
          dob: result.data.dob,
          position: result.data.position,
        };
        setProfileData(profile);
        localStorage.setItem('registrarProfile', JSON.stringify(profile));
      } else {
        showToast(result.message || 'Error loading profile', 'danger');
      }
    } catch (err) {
      console.error('Profile fetch error:', err);
      showToast(err.message || 'Error loading profile', 'danger');
    }
  };

  fetchRegistrarProfile();
}, []);


  const filteredCases = courtCases.filter(c => {
    if (!searchCase.trim()) return true;
    return (
      (c.title || '').toLowerCase().includes(searchCase.toLowerCase()) ||
      (c.description || '').toLowerCase().includes(searchCase.toLowerCase()) ||
      (c.caseType || '').toLowerCase().includes(searchCase.toLowerCase())
    );
  });
  const [showProfileModal, setShowProfileModal] = useState(false);
  const [profileData, setProfileData] = useState(() => {
    const saved = localStorage.getItem('registrarProfile');
    return saved ? JSON.parse(saved) : { name: '', email: '', phone: '', court: '' };
  });
  const [isEditingProfile, setIsEditingProfile] = useState(false);

  const [profileImage, setProfileImage] = useState(`/api/profile/photo/me?t=${Date.now()}`);
  const fileInputRef = useRef(null);

  // Add these state variables at the top with other state declarations
  const [showFinalDecisionModal, setShowFinalDecisionModal] = useState(false);
  const [selectedCase, setSelectedCase] = useState(null);

 const [evidence, setEvidence] = useState([]);
const [searchEvidence, setSearchEvidence] = useState('');
const filteredEvidence = evidence.filter(e =>
  (e.caseName || '').toLowerCase().includes(searchEvidence.toLowerCase()) ||
  (e.evidenceType || '').toLowerCase().includes(searchEvidence.toLowerCase()) ||
  (e.description || '').toLowerCase().includes(searchEvidence.toLowerCase()) ||
  (e.lawyerName || '').toLowerCase().includes(searchEvidence.toLowerCase()) ||
  (e.file || e.filepath || '').toLowerCase().includes(searchEvidence.toLowerCase())
);

const [witnesses, setWitnesses] = useState([]);
const [searchWitness, setSearchWitness] = useState('');
const filteredWitnesses = witnesses.filter(w =>
  (w.witness?.firstname || '').toLowerCase().includes(searchWitness.toLowerCase()) ||
  (w.witness?.lastname || '').toLowerCase().includes(searchWitness.toLowerCase()) ||
  (w.witness?.caseName || '').toLowerCase().includes(searchWitness.toLowerCase()) ||
  (w.witness?.contact || w.witness?.phone || '').toLowerCase().includes(searchWitness.toLowerCase()) ||
  (w.witness?.statement || '').toLowerCase().includes(searchWitness.toLowerCase())
);


useEffect(() => {
  const fetchWitnesses = async () => {
    try {
      const response = await fetch('/api/witnesses', { credentials: 'include' });
      if (!response.ok) throw new Error('Failed to fetch witnesses');
      const data = await response.json();
      setWitnesses(data.witnesses || []);
    } catch (error) {
      console.error('Error fetching witnesses:', error);
    }
  };

  fetchWitnesses();
}, []);


useEffect(() => {
  const fetchEvidence = async () => {
    try {
      const response = await fetch('/api/evidence', { credentials: 'include' });
      if (!response.ok) throw new Error('Failed to fetch evidence');
      const data = await response.json();
      setEvidence(data.evidence || []);
    } catch (error) {
      console.error('Error fetching evidence:', error);
    }
  };

  fetchEvidence();
}, []);

  
  const location = useLocation();
  const navigate = useNavigate();

  const handleProfileImageUpload = async (event) => {
    const file = event.target.files[0];
    if (!file) return;
    const fd = new FormData();
    fd.append('photo', file);
    try {
      const res = await fetch('/api/profile/photo', { method: 'POST', credentials: 'include', body: fd });
      if (res.ok) setProfileImage(`/api/profile/photo/me?t=${Date.now()}`);
    } catch { /* silent */ }
  };
  const triggerProfileImageUpload = () => fileInputRef.current?.click();

  // Toast helpers
  const showToast = (message, variant = 'success') => {
    setToast({ show: true, message, variant });
    setTimeout(() => setToast({ show: false, message: '', variant: 'success' }), 2500);
  };

  // COURT CRUD
  const handleCourtFormChange = (e) => setCourtForm({ ...courtForm, [e.target.name]: e.target.value });
  const handleCourtSubmit = (e) => {
    e.preventDefault();
      if (editingCourt) {
      setCourts(courts.map(c => c.id === editingCourt.id ? { ...editingCourt, ...courtForm } : c));
        showToast('Court updated!');
      setShowCourtModal(false);
      setEditingCourt(null);
      setCourtForm({ name: '', location: '', type: '' });
    } else {
      setCourts([...courts, { ...courtForm, id: Date.now() }]);
      localStorage.setItem('courtRegistered', 'true');
      setIsCourtRegistered(true);
      showToast('Court registered successfully!');
      setShowCourtModal(false);
      setEditingCourt(null);
      setCourtForm({ name: '', location: '', type: '' });
    }
  };
  const handleEditCourt = (court) => {
    setEditingCourt(court);
    setCourtForm({ name: court.name, location: court.location, type: court.type });
    setShowCourtModal(true);
  };
  const handleDeleteCourt = (court) => {
    setConfirm({ show: true, type: 'deleteCourt', payload: court });
  };
  const confirmDeleteCourt = () => {
    setCourts([]);
    setConfirm({ show: false, type: '', payload: null });
    showToast('Court deleted!', 'danger');
    setSelectedCourt(null);
    setActiveTab('dashboard');
  };

  // COURT SELECTION
  const handleSelectCourt = (court) => {
    setSelectedCourt(court);
    setCourtRooms(court.rooms || []);
    setCourtJudges(court.judges || []);
    setCourtProsecutors(court.prosecutors || []);
    setCourtPayments(court.payments || []);
    setCourtAppeals(court.appeals || []);
    setCourtCases(court.cases || []);
    setActiveTab('courtRooms');
  };

  
  
  // COURT ROOMS CRUD
  const handleRoomFormChange = (e) => setRoomForm({ ...roomForm, [e.target.name]: e.target.value });
  const handleRoomSubmit = async (e) => {
  e.preventDefault();
  setLoading(true);

  const isEditing = !!editingRoom;
  const url = isEditing 
    ? `/api/courtrooms/${editingRoom.id}` 
    : '/api/courtrooms';
  const method = isEditing ? 'PUT' : 'POST';

  try {
    const response = await fetch(url, {
      method,
      headers: { 'Content-Type': 'application/json' },
      credentials: 'include',
      body: JSON.stringify(roomForm),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.message || (isEditing ? 'Failed to update room' : 'Failed to add room'));
    }

    showToast(isEditing ? 'Room updated!' : 'Room added!');
    setShowRoomModal(false);
    setEditingRoom(null);
    setRoomForm({
      number: '',
      name: '',
      capacity: '',
      type: '',
      status: 'Available',
    });

    // Optionally refresh room list
    if (selectedCourt?.id) {
      fetchCourtRooms(selectedCourt.id);
    }

  } catch (err) {
    console.error('Room error:', err);
    showToast(err.message || 'Error submitting room', 'danger');
  } finally {
    setLoading(false);
  }
};


  const handleRoomView = (room) => {
  setViewingRoom(room);
  setShowRoomViewModal(true);
};

const handleConfirmDeleteRoom = async () => {
  const room = confirm.payload;
  if (!room || !room.id) {
    console.warn('No room or room.id to delete');
    return;
  }

  try {
    const response = await fetch(`/api/courtrooms/${room.id}`, {
      method: 'DELETE',
      credentials: 'include',
    });

    if (!response.ok) {
      const err = await response.json();
      throw new Error(err.message || 'Failed to delete room');
    }

    // Update UI
    setCourtRooms(prev => prev.filter(r => r.id !== room.id));
    showToast('Room deleted successfully');
  } catch (err) {
    console.error('Error deleting room:', err);
    showToast(err.message, 'danger');
  } finally {
    setConfirm({ show: false, type: '', payload: null });
  }
};


const handleRoomEdit = (room) => {
  setEditingRoom(room);
  setRoomForm({
    number: room.number || '',
    name: room.name || '',
    capacity: room.capacity || '',
    type: room.type || '',
    availability: room.availability,
    id: room.id || null,  // keep id for update
  });
  setShowRoomModal(true);
};

const handleRoomDelete = (room) => {
  setConfirm({ show: true, type: 'deleteRoom', payload: room });
};

const handleRoomAdd = () => {
  setEditingRoom(null);
  setRoomForm({
    number: '',
    name: '',
    capacity: '',
    type: '',
    availability: 'Available',
    id: null,
  });
  setShowRoomModal(true);
};

  // JUDGES
  const handleAssignJudge = (judge) => {
    if (!courtJudges.find(j => j.id === judge.id)) setCourtJudges([...courtJudges, judge]);
  };
  const handleUnassignJudge = (judge) => setCourtJudges(courtJudges.filter(j => j.id !== judge.id));

  // PROSECUTORS
  const handleAssignProsecutor = (prosecutor) => {
    if (!courtProsecutors.find(p => p.id === prosecutor.id)) setCourtProsecutors([...courtProsecutors, prosecutor]);
  };
  const handleUnassignProsecutor = (prosecutor) => setCourtProsecutors(courtProsecutors.filter(p => p.id !== prosecutor.id));

  // PAYMENTS
  const handleAddPayment = async () => {
  try {
    const response = await fetch('/api/payments', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'include',
      body: JSON.stringify({
        casename: paymentForm.casename,         // e.g., "State v. John Doe"
        purpose: paymentForm.purpose,           // e.g., "Filing Fee"
        balance: paymentForm.balance,           // e.g., "250.00"
        mode: paymentForm.mode,                 // e.g., "Online"
        paymenttype: paymentForm.paymenttype,   // e.g., "Initial"
        paymentdate: paymentForm.paymentdate || new Date().toISOString().split("T")[0] // fallback to today
      }),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.message || 'Failed to add payment');
    }

    const data = await response.json();

    // Add returned payment data to UI list
    setCourtPayments([...courtPayments, {
      id: Date.now(),
      amount: data.payment.balance,
      date: data.payment.paymentdate,
      purpose: data.payment.purpose,
      mode: data.payment.mode,
      casename: data.payment.casename,
      paymenttype: data.payment.paymenttype
    }]);

    showToast('Payment added!');
  } catch (err) {
    console.error('Error adding payment:', err);
    showToast(err.message || 'Error adding payment', 'danger');
  }
};


  // APPEALS
  const handleAddAppeal = () => {
    setCourtAppeals([...courtAppeals, { id: Date.now(), title: `Appeal #${courtAppeals.length+1}` }]);
    showToast('Appeal added!');
  };

  // CASES
  const handleGrantCase = (courtCase) => {
    if (!courtCases.find(c => c.id === courtCase.id)) setCourtCases([...courtCases, courtCase]);
  };
  const handleRevokeCase = (courtCase) => setCourtCases(courtCases.filter(c => c.id !== courtCase.id));

  // Save changes to selected court
  const handleSaveCourt = () => {
    setCourts(courts.map(c => c.id === selectedCourt.id ? {
      ...selectedCourt,
      rooms: courtRooms,
      judges: courtJudges,
      prosecutors: courtProsecutors,
      payments: courtPayments,
      appeals: courtAppeals,
      cases: courtCases,
    } : c));
    setSelectedCourt();
    setActiveTab('dashboard');
    showToast('Court updated!');
  };

  // Add a helper to check if a court is registered
  const isCourtRegistered = courts.length === 1;

  // Sidebar navigation (dynamic based on registration)
  const navItems = [
    { key: 'dashboard', label: 'Dashboard', icon: <Building2 size={16} /> },
    { key: 'courtRooms', label: 'Court Rooms', icon: <Users size={16} /> },
    { key: 'cases', label: 'Cases', icon: <Briefcase size={16} /> },
    { key: 'hearingSchedule', label: 'Hearing Schedule', icon: <Gavel size={16} /> },
    { key: 'caseHistory', label: 'Manage Case History', icon: <FileText size={16} /> },
    { key: 'appeals', label: 'Appeals', icon: <FileText size={16} /> },
    { key: 'evidence', label: 'Evidence', icon: <FileText size={16} /> },
    { key: 'witnesses', label: 'Witnesses', icon: <Users size={16} /> },
    { key: 'payments', label: 'Payments', icon: <DollarSign size={16} /> },
    { key: 'prosecutors', label: 'Prosecutors', icon: <Users size={16} /> },
    { key: 'judges', label: 'Judges', icon: <Users size={16} /> },
    { key: 'remands', label: 'Remands', icon: <Gavel size={16} /> },
  ];

  // Filter helpers
  const filteredCourts = courts.filter(c => c.name.toLowerCase().includes(searchCourt.toLowerCase()));
  const filteredRooms = courtRooms.filter(r => r.name.toLowerCase().includes(searchRoom.toLowerCase()));

  // Add after other useState hooks
  const handleAppealFormChange = e => setAppealForm({ ...appealForm, [e.target.name]: e.target.value });
  const handleAppealSubmit = e => {
    e.preventDefault();
    if (editingAppeal) {
      setAppeals(appeals.map(a => a.id === editingAppeal.id ? { ...editingAppeal, ...appealForm } : a));
      showToast('Appeal updated!');
    } else {
      setAppeals([
        ...appeals,
        { ...appealForm, id: Date.now() }
      ]);
      showToast('Appeal added!');
    }
    setShowAppealModal(false);
    setEditingAppeal(null);
    setAppealForm({ appealNumber: '', originalCaseId: '', appellant: '', respondent: '', dateFiled: '', status: '' });
  };
  const handleEditAppeal = appeal => {
    setEditingAppeal(appeal);
    setAppealForm({ ...appeal });
    setShowAppealModal(true);
  };
  const handleViewAppeal = appeal => {
    setEditingAppeal(appeal);
    setAppealForm({ ...appeal });
    setShowAppealModal(true); // For now, reuse the modal for view/edit
  };

  // Case handlers
  const handleDeleteCase = (caseid) => {
    setCourtCases(prev => prev.filter(c => c.caseid !== caseid));
    showToast('Case removed from view', 'success');
  };
  const handleCaseView = async (c) => {
    setViewingCase(c);
    setCaseHistory([]);
    setLoadingTimeline(true);
    setShowCaseViewModal(true);
    const history = await getCaseHistory(c.caseid);
    setCaseHistory(history);
    setLoadingTimeline(false);
  };
  const handleCaseEdit = (c) => { setEditingCase(c); setCaseForm({ ...c }); setShowCaseModal(true); };
  const handleCaseDelete = (c) => setCases(cases.filter(x => x.id !== c.id));
  const handleCaseAdd = () => { setEditingCase(null); setCaseForm({ number: '', title: '', parties: '', type: '', status: '' }); setShowCaseModal(true); };
  const handleCaseFormChange = (e) => setCaseForm({ ...caseForm, [e.target.name]: e.target.value });
  const handleCaseSubmit = (e) => {
    e.preventDefault();
    if (editingCase) {
      setCourtCases(courtCases.map(c => 
        c.id === editingCase.id ? { ...c, ...caseForm } : c
      ));
    } else {
      const newCase = {
        id: Date.now(),
        ...caseForm,
        filingDate: new Date().toLocaleDateString(),
        status: 'Pending'
      };
      setCourtCases([newCase, ...courtCases]);
    }
    setShowCaseModal(false);
    setEditingCase(null);
    setCaseForm({
      title: '',
      description: '',
      caseType: '',
      clientName: '',
      lawyerName: '',
      prosecutor: ''
    });
  };

  useEffect(() => {
  const loadProsecutors = async () => {
    const prosecutors = await fetchProsecutors();
    setCourtProsecutors(prosecutors); // Assuming you have this state
  };

  loadProsecutors();
}, []);

useEffect(() => {
  if (showVerifyModal) {
    fetch('/api/judges', { credentials: 'include' })
      .then(res => res.json())
      .then(data => setJudgeOptions(data.judges || []))
      .catch(() => setJudgeOptions([]));
    fetch('/api/prosecutors', { credentials: 'include' })
      .then(res => res.json())
      .then(data => setProsecutorOptions(data.prosecutors || []))
      .catch(() => setProsecutorOptions([]));
    // fetch lawyers for opposing selection
    fetch('/api/lawyers', { credentials: 'include' })
      .then(res => res.json())
      .then(data => setLawyerOptions(data.lawyers || data || []))
      .catch(() => setLawyerOptions([]));
  }
}, [showVerifyModal]);

const handleVerifyCase = (caseObj) => {
  setVerifyingCase(caseObj);
  setRespondentLawyerId('');
  setVerifyForm({
    casename: caseObj.title || '',
    type: caseObj.casetype || '',
    filingdate: caseObj.filingdate || '',
    clientname: caseObj.clientName || caseObj.clientname || '',
    lawyername: caseObj.lawyername || caseObj.lawyerName || '',
    judgename: caseObj.judgeName || '',
    prosecutorname: caseObj.prosecutor || ''
  });
  setVerifyError('');
  setVerifySuccess('');
  setShowVerifyModal(true);
};

const handleVerifyFormChange = (e) => {
  setVerifyForm({ ...verifyForm, [e.target.name]: e.target.value });
};

const refreshCourtCases = async () => {
  const response = await fetch('/api/cases', {
    credentials: 'include',
    headers: { 'Content-Type': 'application/json' },
  });
  if (!response.ok) throw new Error('Failed to refresh cases');
  const data = await response.json();
  const mappedCases = (data.cases || []).map(c => ({
    ...c,
    clientName: c.clientName ?? c.clientname ?? 'N/A',
    lawyername: c.lawyername ?? c.lawyerName ?? 'N/A',
    prosecutor: c.prosecutorName ?? c.prosecutor ?? 'N/A',
  }));
  setCourtCases(mappedCases);
};

const handleVerifySubmit = async (e) => {
  e.preventDefault();
  setVerifyLoading(true);
  setVerifyError('');
  setVerifySuccess('');
  try {
    const payload = {
      ...verifyForm,
      caseid: verifyingCase?.caseid,
      respondent_lawyer_id: respondentLawyerId || null,
    };
    const res = await fetch('/api/verifycases', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'include',
      body: JSON.stringify(payload),
    });
    const data = await res.json();
    if (!res.ok) {
      setVerifyError(data.error || data.message || 'Verification failed');
    } else {
      setVerifySuccess('Case verified and relationships created.');
      setShowVerifyModal(false);
      setRespondentLawyerId('');
      showToast(
        data.casenumber
          ? `Case verified! Assigned number: ${data.casenumber}`
          : 'Case verified!',
        'success'
      );
      await refreshCourtCases();
    }
  } catch (err) {
    setVerifyError(err.message || 'Verification failed');
  } finally {
    setVerifyLoading(false);
  }
};


  // Profile handlers
  const handleProfileSave = () => {
    setIsEditingProfile(false);
    showToast('Profile updated!');
  };
  const handleProfileChange = (e) => setProfileData({ ...profileData, [e.target.name]: e.target.value });

  // Logout handler
  const handleLogout = () => {
    localStorage.clear();
    navigate('/login');
  };

  // Helper to get CourtRegistrar info from localStorage (from signup)
  const getCourtRegistrarInfo = () => {
    return { name: '', email: '', phone: '', cnic: '', dob: '' };
  };
  const [courtRegistrarInfo] = useState(getCourtRegistrarInfo());

  // Add this handler function with other handlers
  const handleViewFinalDecision = (case_) => {
    setSelectedCase(case_);
    setShowFinalDecisionModal(true);
  };

  // Add handlers for evidence
  const handleEvidenceAdd = () => {
    setShowEvidenceModal(true);
    setEditingEvidence(null);
    setEvidenceForm({
      caseTitle: '',
      type: '',
      description: '',
      dateAdded: '',
      status: 'Pending'
    });
  };

  const handleEvidenceEdit = (evidence) => {
    setEditingEvidence(evidence);
    setEvidenceForm({ ...evidence });
    setShowEvidenceModal(true);
  };

  const handleEvidenceView = (evidence) => {
    setViewingEvidence(evidence);
    setShowEvidenceViewModal(true);
  };

  const handleEvidenceDelete = (evidence) => {
    setEvidence(evidence.filter(e => e.id !== evidence.id));
    showToast('Evidence deleted!', 'danger');
  };

  // Add handlers for witnesses
  const handleWitnessAdd = () => {
    setShowWitnessModal(true);
    setEditingWitness(null);
    setWitnessForm({
      name: '',
      caseTitle: '',
      contact: '',
      status: 'Pending'
    });
  };

  const handleWitnessEdit = (witness) => {
    setEditingWitness(witness);
    setWitnessForm({ ...witness });
    setShowWitnessModal(true);
  };

  const handleWitnessView = (witness) => {
    setViewingWitness(witness);
    setShowWitnessViewModal(true);
  };

  const handleWitnessDelete = (witness) => {
    setWitnesses(witnesses.filter(w => w.id !== witness.id));
    showToast('Witness deleted!', 'danger');
  };

  // Add state variables for evidence and witness modals
  const [showEvidenceModal, setShowEvidenceModal] = useState(false);
  const [showEvidenceViewModal, setShowEvidenceViewModal] = useState(false);
  const [editingEvidence, setEditingEvidence] = useState(null);
  const [viewingEvidence, setViewingEvidence] = useState(null);
  const [evidenceForm, setEvidenceForm] = useState({
    caseTitle: '',
    type: '',
    description: '',
    dateAdded: '',
    status: 'Pending'
  });

  const [showWitnessModal, setShowWitnessModal] = useState(false);
  const [showWitnessViewModal, setShowWitnessViewModal] = useState(false);
  const [editingWitness, setEditingWitness] = useState(null);
  const [viewingWitness, setViewingWitness] = useState(null);
  const [witnessForm, setWitnessForm] = useState({
    name: '',
    caseTitle: '',
    contact: '',
    status: 'Pending'
  });

  // Add handlers for evidence form
  const handleEvidenceFormChange = (e) => setEvidenceForm({ ...evidenceForm, [e.target.name]: e.target.value });
  const handleEvidenceSubmit = (e) => {
    e.preventDefault();
    if (editingEvidence) {
      setEvidence(evidence.map(e => e.id === editingEvidence.id ? { ...editingEvidence, ...evidenceForm } : e));
      showToast('Evidence updated!');
    } else {
      setEvidence([...evidence, { ...evidenceForm, id: Date.now() }]);
      showToast('Evidence added!');
    }
    setShowEvidenceModal(false);
    setEditingEvidence(null);
    setEvidenceForm({
      caseTitle: '',
      type: '',
      description: '',
      dateAdded: '',
      status: 'Pending'
    });
  };

  // Add handlers for witness form
  const handleWitnessFormChange = (e) => setWitnessForm({ ...witnessForm, [e.target.name]: e.target.value });
  const handleWitnessSubmit = (e) => {
    e.preventDefault();
    if (editingWitness) {
      setWitnesses(witnesses.map(w => w.id === editingWitness.id ? { ...editingWitness, ...witnessForm } : w));
      showToast('Witness updated!');
    } else {
      setWitnesses([...witnesses, { ...witnessForm, id: Date.now() }]);
      showToast('Witness added!');
    }
    setShowWitnessModal(false);
    setEditingWitness(null);
    setWitnessForm({
      name: '',
      caseTitle: '',
      contact: '',
      status: 'Pending'
    });
  };

  // Add state for editing appeal decision
  const [showDecisionModal, setShowDecisionModal] = useState(false);
  const [decisionAppeal, setDecisionAppeal] = useState(null);
  const [decisionForm, setDecisionForm] = useState({ status: '', decisionDate: '', decision: '' });

  const handleOpenDecisionModal = (appeal) => {
    setDecisionAppeal(appeal);
    setDecisionForm({
      status: appeal.status || '',
      decisionDate: appeal.decisionDate || '',
      decision: appeal.decision || '',
    });
    setShowDecisionModal(true);
  };
  const handleCloseDecisionModal = () => {
    setShowDecisionModal(false);
    setDecisionAppeal(null);
  };
  const handleDecisionFormChange = (e) => {
    setDecisionForm({ ...decisionForm, [e.target.name]: e.target.value });
  };
  const handleDecisionSubmit = async (e) => {
  e.preventDefault();

  try {
    const response = await fetch(`/api/appealdecision?appealId=${decisionAppeal.appealId}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'include',
      body: JSON.stringify({
        appealStatus: decisionForm.status,
        decisionDate: decisionForm.decisionDate,
        decision: decisionForm.decision
      }),
    });

    if (!response.ok) throw new Error('Failed to update appeal decision');

    showToast('Appeal decision updated!');
    await getAppeals(); // Refresh list
    setShowDecisionModal(false);
    setDecisionAppeal(null);
  } catch (err) {
    console.error('Error updating decision:', err);
    showToast(err.message || 'Failed to update decision', 'danger');
  }
};
  // Add after other state declarations
  const [showProsecutorModal, setShowProsecutorModal] = useState(false);
  const [editingProsecutor, setEditingProsecutor] = useState(null);
  const [prosecutorForm, setProsecutorForm] = useState({
    name: '',
    experience: '',
    status: 'Active',
    assignedCases: []
  });

  // Add after other handlers
  const handleProsecutorFormChange = (e) => {
    setProsecutorForm({ ...prosecutorForm, [e.target.name]: e.target.value });
  };
const handleProsecutorSubmit = async (e) => {
  e.preventDefault();

  const url = editingProsecutor ? '/api/prosecutor' : '/api/prosecutor';
  const method = editingProsecutor ? 'PUT' : 'POST';

  try {
    const response = await fetch(url, {
      method,
      headers: { 'Content-Type': 'application/json' },
      credentials: 'include',
      body: JSON.stringify({
        id: prosecutorForm.id,
        name: prosecutorForm.name,
        experience: prosecutorForm.experience,
        status: prosecutorForm.status,
        case_names: prosecutorForm.assignedCases,
      }),
    });

    if (!response.ok) throw new Error('Failed to save prosecutor');
    const result = await response.json();

    if (editingProsecutor) {
      setCourtProsecutors(courtProsecutors.map(p =>
        p.id === prosecutorForm.id
          ? {
              ...p,
              name: prosecutorForm.name,
              experience: prosecutorForm.experience,
              status: prosecutorForm.status,
              assignedCases: prosecutorForm.assignedCases,
            }
          : p
      ));
      showToast('Prosecutor updated!');
    } else {
      const newProsecutor = result;
      setCourtProsecutors([...courtProsecutors, {
        id: newProsecutor.id,
        name: newProsecutor.name,
        experience: newProsecutor.experience,
        status: newProsecutor.status,
        assignedCases: newProsecutor.assigned_cases || [],
      }]);
      showToast('Prosecutor added!');
    }
  } catch (err) {
    console.error('Error submitting prosecutor:', err);
    showToast(err.message || 'Submission failed', 'danger');
  } finally {
    setShowProsecutorModal(false);
    setEditingProsecutor(null);
    setProsecutorForm({
      name: '',
      experience: '',
      status: '',
      assignedCases: [],
    });
  }
};

  const handleEditProsecutor = (prosecutor) => {
  setEditingProsecutor(prosecutor);
  setProsecutorForm({
    name: prosecutor.name,
    experience: prosecutor.experience,
    status: prosecutor.status,
    assignedCases: prosecutor.assignedCases || [],
    id: prosecutor.id
  });
  setShowProsecutorModal(true);
};


 const handleDeleteProsecutor = async (prosecutorId) => {
  try {
    const res = await fetch(`/api/prosecutor/${prosecutorId}`, {
      method: 'DELETE',
      credentials: 'include',
    });

    if (!res.ok) throw new Error('Failed to delete prosecutor');

    setCourtProsecutors(courtProsecutors.filter(p => p.id !== prosecutorId));
    showToast('Prosecutor deleted!');
  } catch (err) {
    console.error('Error deleting prosecutor:', err);
    showToast('Error deleting prosecutor', 'danger');
  }
};


  // JUDGES
  const handleJudgeFormChange = (e) => {
    setJudgeForm({ ...judgeForm, [e.target.name]: e.target.value });
  };
 const handleJudgeSubmit = async (e) => {
  e.preventDefault();
  try {
    let response;

    if (editingJudge) {
      // Editing: send PUT to update profile
    response = await fetch('/api/judge', {
    method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'include',
    body: JSON.stringify({
  name: judgeForm.name,
  specialization: judgeForm.specialization,
  appointmentDate: judgeForm.appointmentDate, // FIXED
  experience: judgeForm.experience,           // FIXED
  position: judgeForm.position,
})
,
});
    } else {
      // Adding new judge: send POST
      response = await fetch('/api/judges', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify(judgeForm),
      });
    }

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.message || 'Failed to submit judge');
    }

    const data = await response.json();

    if (editingJudge) {
      // Update judge in list
      setCourtJudges(courtJudges.map(j =>
        j.id === editingJudge.id
          ? {
              ...j,
              position: judgeForm.position,
              experience: judgeForm.experience,
              appointmentDate: judgeForm.appointmentDate,
              specialization: judgeForm.specialization,
              // assignedCases stay unchanged or update if needed
            }
          : j
      ));
      showToast('Judge profile updated!');
    } else {
      // Add new judge to list
      setCourtJudges([
        ...courtJudges,
        {
          id: data.judgeid,
          name: data.name,
          position: data.position,
          experience: data.expyears,
          appointmentDate: data.appointmentdate,
          specialization: data.specialization,
          assignedCases: data.assigned_cases || [],
        }
      ]);
      showToast('Judge added!');
    }
  } catch (err) {
    console.error('Error submitting judge:', err);
    showToast(err.message || 'Error submitting judge', 'danger');
  } finally {
    setShowJudgeModal(false);
    setEditingJudge(null);
    setJudgeForm({
      name: '',
      position: '',
      experience: '',
      appointmentDate: '',
      specialization: '',
      assignedCases: []
    });
  }
};

const handleEditJudge = (judge) => {
  // Defensive: handle both backend and frontend judge object shapes
  setEditingJudge(judge);

  setJudgeForm({
    name: judge.name || `${judge.firstname || ''} ${judge.lastname || ''}`.trim(),
    position: judge.position || '',
    experience: judge.expyears || judge.experience || '',
    appointmentDate: judge.appointmentdate || judge.appointmentDate || '',
    specialization: judge.specialization || '',
    assignedCases: judge.assigned_cases || judge.assignedCases || [],
    id: judge.judgeid || judge.id || undefined
  });

  setShowJudgeModal(true);
};

  const handleDeleteJudge = (judge) => {
    setCourtJudges(courtJudges.filter(j => j.id !== judge.id));
  };

  // Remands
  const [remands, setRemands] = useState([
    { id: 1, caseName: 'State v. Smith', lawyerName: 'John Doe', clientName: 'Jane Smith', remandType: 'Police', remandDate: '2024-06-10', remandReason: 'Further investigation', status: 'Active', duration: '7 days' },
    { id: 2, caseName: 'People v. Doe', lawyerName: 'John Doe', clientName: 'John Doe', remandType: 'Judicial', remandDate: '2024-06-12', remandReason: 'Awaiting trial', status: 'Completed', duration: '14 days' },
  ]);
  const [showRemandModal, setShowRemandModal] = useState(false);
  const [editingRemand, setEditingRemand] = useState(null);
  const [remandForm, setRemandForm] = useState({
    caseName: '',
    lawyerName: '',
    clientName: '',
    remandType: '',
    remandDate: '',
    remandReason: '',
    status: '',
    duration: ''
  });

  // Remand handlers
  const handleRemandFormChange = (e) => {
    setRemandForm({ ...remandForm, [e.target.name]: e.target.value });
  };
  const handleRemandSubmit = async (e) => {
  e.preventDefault();
  try {
    const response = await fetch('/api/remands', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'include',
      body: JSON.stringify(remandForm),
    });

    if (!response.ok) throw new Error('Failed to submit remand');

    const newRemand = await response.json();
    setRemands([newRemand, ...remands]);  // Add to top
    showToast('Remand added!');
  } catch (err) {
    console.error('Error submitting remand:', err);
    showToast('Error adding remand', 'danger');
  } finally {
    setShowRemandModal(false);
    setEditingRemand(null);
    setRemandForm({
      caseName: '',
      lawyerName: '',
      clientName: '',
      remandType: '',
      remandDate: '',
      remandReason: '',
      status: '',
      duration: ''
    });
  }
};

  const handleEditRemand = (remand) => {
    setEditingRemand(remand);
    setRemandForm({ ...remand });
    setShowRemandModal(true);
  };
  const handleDeleteRemand = (remand) => {
    setRemands(remands.filter(r => r.id !== remand.id));
  };

  // Add state for case history
  const [caseHistory, setCaseHistory] = useState([]);
  const [showCaseHistoryModal, setShowCaseHistoryModal] = useState(false);
  const [editingCaseHistory, setEditingCaseHistory] = useState(null);
  const [caseHistoryForm, setCaseHistoryForm] = useState({
    caseName: '',
    judgeName: '',
    clientName: '',
    lawyerName: '',
    remarks: '',
    actionDate: '',
    actionTaken: '',
    status: '',
  });


  const getCaseHistory = async (caseId) => {
    try {
      const response = await fetch(`/api/cases/${caseId}/history`, {
        method: 'GET',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
      });
      const data = await response.json();
      if (!response.ok) {
        console.error('Case history error:', data.error || data.message);
        return [];
      }
      return data.history || [];
    } catch (error) {
      console.error('Failed to fetch case history:', error.message);
      return [];
    }
  };

  const getAllCaseHistory = async () => {
    try {
      const response = await fetch('/api/cases/history', {
        method: 'GET',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
      });
      if (!response.ok) {
        throw new Error(`Error ${response.status}: ${response.statusText}`);
      }
      const data = await response.json();
      return data.history || [];
    } catch (error) {
      console.error('Failed to fetch all case history:', error.message);
      return [];
    }
  };

const handleViewCase = async (caseId) => {
  const selectedCase = cases.find((caseItem) => caseItem.id === caseId);
  setViewingCase(selectedCase);
  const history = await getCaseHistory(caseId);  // Await result
  setCaseHistory(history);                       // Save to state
  setShowCaseViewModal(true);
};

  // Case History handlers
  const handleCaseHistoryFormChange = (e) => setCaseHistoryForm({ ...caseHistoryForm, [e.target.name]: e.target.value });
  const handleCaseHistorySubmit = async (e) => {
  e.preventDefault();

  // Prepare entry to save (merge editing entry + form data)
  const entryToSave = editingCaseHistory
    ? { ...editingCaseHistory, ...caseHistoryForm }
    : { ...caseHistoryForm };

  try {
    // Call backend save
    const method = entryToSave.id ? 'PUT' : 'POST';
    const activeCaseId = viewingCase?.caseid || viewingCase?.id;
    const url = entryToSave.id
      ? `/api/cases/history/${entryToSave.id}`      // Update
      : `/api/cases/${activeCaseId}/history`;       // Add new

    const response = await fetch(url, {
      method,
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        actiontaken: entryToSave.actiontaken,
        remarks: entryToSave.remarks,
      }),
    });

    const result = await response.json();

    if (!response.ok) {
      alert(result.message || 'Failed to save case history');
      return;
    }

    // On success, update local state:
    if (method === 'POST') {
      // If server returns the new entry with ID, add it:
      // (if not returned, you may need to fetch history again)
      // For now, just add local with a temporary ID or refresh
      setCaseHistory((prev) => [{ ...entryToSave, id: result.new_id || Date.now() }, ...prev]);
    } else {
      // For update, replace existing item with updated data
      setCaseHistory((prev) =>
        prev.map((h) => (h.id === entryToSave.id ? { ...h, ...entryToSave } : h))
      );
    }

    // Clear modal and form
    setShowCaseHistoryModal(false);
    setEditingCaseHistory(null);
    setCaseHistoryForm({
      caseName: '',
      judgeName: '',
      clientName: '',
      lawyerName: '',
      remarks: '',
      actionDate: '',
      actionTaken: '',
      status: '',
    });

  } catch (error) {
    alert('Error: ' + error.message);
  }
};

  const handleEditCaseHistory = (entry) => {
    setEditingCaseHistory(entry);
    setCaseHistoryForm({ ...entry });
    setShowCaseHistoryModal(true);
  };
  // const handleDeleteCaseHistory = (id) => {
  //   setCaseHistory(caseHistory.filter(h => h.id !== id));
  // };

  // Assuming `caseId` is available in your component scope

const handleSaveCaseHistory = async (entry) => {
  try {
    const method = entry.id ? 'PUT' : 'POST';
    const activeCaseId = viewingCase?.caseid || viewingCase?.id;
    const url = entry.id
      ? `/api/cases/history/${entry.id}`              // Update existing entry
      : `/api/cases/${activeCaseId}/history`;         // Add new entry

    const response = await fetch(url, {
      method,
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        actiontaken: entry.actiontaken,
        remarks: entry.remarks,
      }),
    });

    const result = await response.json();

    if (response.ok) {
      // Success - update your local state accordingly
      if (method === 'POST') {
        // Optionally refresh case history list or append new entry with server-assigned id
        console.log('Added new case history:', result);
      } else {
        console.log('Updated case history:', result);
      }
      setShowCaseHistoryModal(false);
      // Refresh the caseHistory state from API or update it locally here
    } else {
      alert(result.message || 'Failed to save case history');
    }
  } catch (error) {
    alert('Error: ' + error.message);
  }
};

const handleDeleteCaseHistory = async (id) => {
  if (!window.confirm('Are you sure you want to delete this history entry?')) return;

  try {
    const response = await fetch(`/api/cases/history/${id}`, {
      method: 'DELETE',
    });
    const result = await response.json();

    if (response.ok) {
      setCaseHistory((prev) => prev.filter(h => h.id !== id));
      console.log('Deleted case history:', result);
    } else {
      alert(result.message || 'Failed to delete history');
    }
  } catch (error) {
    alert('Error: ' + error.message);
  }
};




  // caseHistory state is used only for the timeline modal (populated by handleCaseView)

useEffect(() => {
  if (selectedPage === 'appeals') {
    getAppeals();
  }
}, [selectedPage]);

  return (
    <div style={{ minHeight: '100vh', width: '100vw', height: '100vh', overflow: 'hidden', background: '#f4f6fa', display: 'flex', flexDirection: 'column' }}>
      {/* Header */}
      <div className="d-flex justify-content-between align-items-center px-4 py-3 bg-white border-bottom" style={{ minHeight: 64, flex: '0 0 auto' }}>
        <div style={{ fontWeight: 600, fontSize: 22 }}>Court Central</div>
        <div className="d-flex align-items-center gap-4">
          <Notifications />
          <Button 
            variant="link" 
            className="text-decoration-none d-flex align-items-center gap-2" 
            onClick={() => setShowProfileModal(true)}
            style={{ color: '#25304a' }}
          >
            <User size={28} />
            <span>Profile</span>
          </Button>
          <Button 
            variant="link" 
            className="text-decoration-none d-flex align-items-center gap-2" 
            onClick={handleLogout}
            style={{ color: '#25304a' }}
          >
            <i className="bi bi-box-arrow-right" style={{ fontSize: 24 }}></i>
            <span>Logout</span>
          </Button>
        </div>
      </div>
      {/* Main Content Flex Row */}
      <div style={{ flex: '1 1 0', display: 'flex', width: '100%', height: '100%', minHeight: 0 }}>
          {/* Sidebar */}
        <div style={{
          width: 200,
          background: 'linear-gradient(135deg, #1ec6b6 0%, #22304a 100%)',
          color: '#fff',
          display: 'flex',
          flexDirection: 'column',
          justifyContent: 'space-between',
          minHeight: 0,
          flex: '0 0 200px',
          borderTopRightRadius: 18,
          borderBottomRightRadius: 18,
          boxShadow: '2px 0 16px 0 rgba(34,48,74,0.08)',
        }}>
          <div>
            <div className="d-flex align-items-center gap-2 px-4 py-4" style={{ fontWeight: 700, fontSize: 22 }}>
              <i className="bi bi-bank2" style={{ fontSize: 20, color: '#fff' }}></i>
              <span style={{ color: '#fff', fontSize: 16 }}>Court Central</span>
            </div>
            <Nav className="flex-column gap-1 px-1">
              {navItems.map(item => (
                <Nav.Link
                  key={item.key}
                  className={`d-flex align-items-center gap-1 sidebar-link${selectedPage === item.key ? ' active' : ''}`}
                  onClick={() => setSelectedPage(item.key)}
                  style={{
                    background: selectedPage === item.key ? 'rgba(255,255,255,0.12)' : 'transparent',
                    color: selectedPage === item.key ? '#1ec6b6' : '#fff',
                    fontWeight: selectedPage === item.key ? 600 : 500,
                    borderRadius: 8,
                    marginBottom: 1,
                    padding: '6px 8px',
                    fontSize: 14,
                    transition: 'all 0.18s',
                    boxShadow: selectedPage === item.key ? '0 2px 8px rgba(30,198,182,0.08)' : 'none',
                    borderLeft: selectedPage === item.key ? '3px solid #fff' : '3px solid transparent',
                  }}
                  onMouseEnter={e => e.currentTarget.style.background = 'rgba(255,255,255,0.08)'}
                  onMouseLeave={e => e.currentTarget.style.background = selectedPage === item.key ? 'rgba(255,255,255,0.12)' : 'transparent'}
                >
                  {React.cloneElement(item.icon, { size: 16 })}
                  <span style={{ fontSize: 13 }}>{item.label}</span>
                </Nav.Link>
              ))}
            </Nav>
          </div>
        </div>
        {/* Main Area */}
        <div style={{ flex: 1, minHeight: 0, display: 'flex', flexDirection: 'column', width: '100%' }}>
          <div className="p-4" style={{ flex: 1, overflowY: 'auto', minHeight: 0 }}>
            {selectedPage === 'dashboard' && (
              <>
                <div className="mb-4">
                  <Card className="shadow-sm border-0" style={{ borderRadius: 16 }}>
                    <Card.Body>
                      <h1 className="fw-bold mb-1" style={{ color: '#22304a' }}>Welcome, Registrar!</h1>
                      <div className="text-muted" style={{ fontSize: 18 }}>Your central hub for court management tasks.</div>
                    </Card.Body>
                  </Card>
                </div>
                <Row className="g-4">
                  <Col md={8}>
                    <Card className="shadow-sm border-0 mb-4" style={{ borderRadius: 16 }}>
                      <Card.Body>
                        <h3 className="fw-bold mb-3" style={{ color: '#22304a' }}><i className="bi bi-bank2 me-2"></i>Assigned Court Details</h3>
                                
            {loadingCourts ? (
  <div className="text-center py-4">
    <Spinner animation="border" variant="primary" />
    <div>Loading court data...</div>
  </div>
) : courtError ? (
  <div className="alert alert-danger">{courtError}</div>
) : selectedCourt ? (
  <>
    <div className="mb-3">
      <img src={lawImage} alt="court" style={{ width: '100%', borderRadius: 12, objectFit: 'cover', maxHeight: 180 }} />
    </div>
    <h4 className="fw-bold mb-2">{selectedCourt.courtname}</h4>
    <Row className="mb-2">
      <Col md={6}><i className="bi bi-geo-alt me-1"></i> <b>Location:</b> {selectedCourt.location}</Col>
      <Col md={6}><i className="bi bi-building me-1"></i> <b>Type:</b> {selectedCourt.type}</Col>
    </Row>
  </>
) : (
  <p className="text-muted">No court assigned.</p>
)}

                        <div className="text-muted mt-2" style={{ fontSize: 15 }}>
                          This is your primary assigned courthouse. For details on other assignments, please check your profile or contact administration.
                        </div>
                      </Card.Body>
                    </Card>
                    <Card className="shadow-sm border-0" style={{ borderRadius: 16 }}>
  <Card.Body>
    <h3 className="fw-bold mb-3" style={{ color: '#22304a' }}>
      <i className="bi bi-clock-history me-2"></i>Recent Activity
    </h3>
    <div className="table-responsive">
      <table className="table table-borderless align-middle mb-0">
        <thead style={{ background: '#f4f6fa' }}>
          <tr style={{ color: '#22304a', fontWeight: 600 }}>
            <th>Activity</th>
            <th>Type</th>
            <th>Timestamp</th>
          </tr>
        </thead>
        <tbody>
          {activityLogs.length > 0 ? activityLogs.map((a, i) => (
            <tr key={i}>
              <td>{a.activity}</td>
              <td>{a.type}</td>
              <td>{a.timestamp}</td>
            </tr>
          )) : (
            <tr>
              <td colSpan="3" className="text-muted text-center">No recent activity</td>
            </tr>
          )}
        </tbody>
      </table>
    </div>
  </Card.Body>
</Card>

          </Col>
                  <Col md={4}>
                    <Card className="shadow-sm border-0 mb-4" style={{ borderRadius: 16 }}>
                      <Card.Body>
                        <h3 className="fw-bold mb-3" style={{ color: '#22304a' }}><i className="bi bi-bar-chart me-2"></i>Quick Actions</h3>
                        <div className="mb-3 text-muted">Access key functionalities quickly.</div>
                        <div className="d-grid gap-2">
                          <Button variant="light" className="d-flex align-items-center gap-2 justify-content-start text-start border" style={{ fontWeight: 500 }}>
                            <i className="bi bi-buildings me-2" style={{ color: '#1ec6b6', fontSize: 20 }}></i> Manage Court Rooms
                            <div className="ms-auto small text-muted">View and update court room details.</div>
                                  </Button>
                          <Button variant="light" className="d-flex align-items-center gap-2 justify-content-start text-start border" style={{ fontWeight: 500 }}>
                            <i className="bi bi-file-earmark-text me-2" style={{ color: '#1ec6b6', fontSize: 20 }}></i> Manage Cases
                            <div className="ms-auto small text-muted">Access and manage case information.</div>
                                  </Button>
                          <Button variant="light" className="d-flex align-items-center gap-2 justify-content-start text-start border" style={{ fontWeight: 500 }}>
                            <i className="bi bi-person me-2" style={{ color: '#1ec6b6', fontSize: 20 }}></i> View Appeals
                            <div className="ms-auto small text-muted">Monitor and process appeals.</div>
                                  </Button>
                                </div>
                              </Card.Body>
                            </Card>
                          </Col>
                      </Row>
              </>
            )}
            {selectedPage === 'courtRooms' && (
              <Card className="shadow-sm border-0" style={{ borderRadius: 16 }}>
                <Card.Body>
                  <div className="d-flex justify-content-between align-items-center mb-3">
                    <div>
                      <h2 className="fw-bold mb-1" style={{ color: '#22304a' }}><i className="bi bi-buildings me-2"></i>Court Room Management</h2>
                      <div className="text-muted mb-2">View, add, or edit court rooms for the assigned courthouse.</div>
                    </div>
                    <Button variant="primary" className="d-flex align-items-center gap-2 px-4 py-2" style={{ fontWeight: 500, fontSize: '1.1rem', borderRadius: 8 }} onClick={handleRoomAdd}>
                      <i className="bi bi-plus-lg"></i> Add New Room
                    </Button>
                  </div>
                  <InputGroup className="mb-3" style={{ maxWidth: 400 }}>
                    <InputGroup.Text><i className="bi bi-search"></i></InputGroup.Text>
                    <Form.Control placeholder="Search rooms by number..." value={searchRoom} onChange={e => setSearchRoom(e.target.value)} />
                  </InputGroup>
                  <div className="table-responsive">
                    <table className="table align-middle mb-0">
                      <thead style={{ background: '#f4f6fa' }}>
                        <tr style={{ color: '#22304a', fontWeight: 600 }}>
                          <th>Room Number</th>
                          <th>Capacity</th>
                          <th>Status</th>
                          <th>Actions</th>
                        </tr>
                      </thead>
                      <tbody>
  {loadingRooms ? (
    <tr>
      <td colSpan={4} className="text-center py-4">
        <Spinner animation="border" variant="primary" />
        <div>Loading rooms...</div>
      </td>
    </tr>
  ) : roomError ? (
    <tr>
      <td colSpan={4} className="text-danger text-center py-4">{roomError}</td>
    </tr>
  ) : courtRooms.length === 0 ? (
    <tr>
      <td colSpan={4} className="text-muted text-center py-4">No court rooms found.</td>
    </tr>
  ) : (
    courtRooms.map((room, i) => (
      <tr key={i}>
        <td>{room.number}</td>
        <td>{room.capacity}</td>
        <td>
          <span className={`badge ${room.status === 'Available' ? 'bg-primary' : 'bg-danger'}`}>
  {room.status}
</span>

        </td>
        <td>
          <Button variant="outline-secondary" size="sm" className="me-2 p-1 lh-1" onClick={() => handleRoomView(room)}><Eye size={16} /></Button>
          <Button variant="outline-secondary" size="sm" className="me-2 p-1 lh-1" onClick={() => handleRoomEdit(room)}><Edit2 size={16} /></Button>
          {/* <Button
  variant="outline-danger"
  size="sm"
  className="p-1 lh-1"
  onClick={() =>
    setConfirm({ show: true, type: 'deleteRoom', payload: room })
  }
>
  <Trash2 size={16} />
</Button> */}

        </td>
      </tr>
    ))
  )}
</tbody>

                    </table>
                  </div>
                </Card.Body>
              </Card>
            )}{selectedPage === 'cases' && (
  <Card className="shadow-sm border-0" style={{ borderRadius: 16 }}>
    <Card.Body>
      {/* Header Section */}
      <div className="d-flex justify-content-between align-items-center mb-3">
        <div>
          <h2 className="fw-bold mb-1" style={{ color: '#22304a' }}><i className="bi bi-file-earmark-text me-2"></i>Case Management</h2>
          <div className="text-muted mb-2">View and manage cases in your court.</div>
        </div>
      </div>

      {/* Search Box */}
      <InputGroup className="mb-3" style={{ maxWidth: 400 }}>
        <InputGroup.Text><i className="bi bi-search"></i></InputGroup.Text>
        <Form.Control placeholder="Search cases..." value={searchCase} onChange={e => setSearchCase(e.target.value)} />
      </InputGroup>

      {/* Loading and Error Handling */}
      {loadingCases ? (
        <div>Loading...</div>
      ) : errorCases ? (
        <div>Error: {errorCases}</div>
      ) : (
        <div className="table-responsive">
          <Table hover className="align-middle mb-0">
            <thead className="table-light">
              <tr>
                <th>Case Name</th>
                          <th>Case Number</th>
                          <th>Type</th>
                          <th>Filing Date</th>
                          <th>Client</th>
                          <th>Lawyer</th>
                          <th>Prosecutor</th>
                          <th>Judge</th>
                          <th>Status</th>
                          <th>Verify</th>
              </tr>
            </thead>
            <tbody>
              {courtCases.length === 0 ? (
                <tr>
                  <td colSpan={5} className="text-center text-muted py-4">No cases found.</td>
                </tr>
              ) : (
                courtCases.map((case_) => (
                  <tr key={case_.caseid}>
                    <td>{case_.title}</td>
                            <td>{case_.casenumber || '—'}</td>
                            <td>{case_.casetype}</td>
                            <td>{case_.filingdate}</td>
                              <td>{case_.clientName}</td>
                              <td>{case_.lawyername}</td>
                              <td>{case_.prosecutor}</td>
                              <td>{case_.judgeName}</td>
                    <td>
                      <Badge bg={case_.status === 'In Progress' ? 'warning' : case_.status === 'Closed' ? 'success' : 'secondary'} className="px-3 py-1 fs-6">
                        {case_.status}
                      </Badge>
                    </td>
                    <td>
                      <div className="d-flex gap-2 flex-wrap">
                        <Button
                          variant="outline-success"
                          size="sm"
                          onClick={() => handleVerifyCase(case_)}
                        >
                          Verify
                        </Button>
                        <Button
                          variant="outline-primary"
                          size="sm"
                          onClick={() => {
                            setEditingCase(case_);
                            setCaseForm(case_);
                            setShowCaseModal(true);
                          }}
                        >
                          Edit
                        </Button>
                        <Button
                          variant="outline-danger"
                          size="sm"
                          onClick={() => handleDeleteCase(case_.caseid)}
                        >
                          Delete
                        </Button>
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
)}

      {/* Pending Lawyer Join Requests */}
      {selectedPage === 'cases' && (
        <Card className="shadow-sm border-0 mt-3" style={{ borderRadius: 16 }}>
          <Card.Body>
            <div className="d-flex justify-content-between align-items-center mb-3">
              <div>
                <h2 className="fw-bold mb-1" style={{ color: '#22304a' }}><i className="bi bi-people me-2"></i>Pending Lawyer Join Requests</h2>
                <div className="text-muted mb-2">Review and approve or reject lawyer requests to join cases.</div>
              </div>
            </div>
            {joinRequestsLoading ? (
              <div className="text-center py-4">
                <Spinner animation="border" variant="primary" />
                <div>Loading join requests...</div>
              </div>
            ) : joinRequests.length === 0 ? (
              <div className="text-muted text-center py-4">No pending join requests.</div>
            ) : (
              <div className="table-responsive">
                <table className="table align-middle mb-0">
                  <thead style={{ background: '#f4f6fa' }}>
                    <tr style={{ color: '#22304a', fontWeight: 600 }}>
                      <th>Case Name</th>
                      <th>Case Number</th>
                      <th>Lawyer Name</th>
                      <th>Side Requested</th>
                      <th>Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {joinRequests.map((r, idx) => (
                      <tr key={`${r.caseid}-${r.lawyerid}-${idx}`}>
                        <td>{r.case_name}</td>
                        <td>{r.casenumber}</td>
                        <td>{r.lawyer_name}</td>
                        <td>{r.side}</td>
                        <td>
                          <div className="d-flex gap-2">
                            <Button variant="success" size="sm" onClick={() => handleApproveJoinRequest(r.lawyerid, r.caseid)}>Approve</Button>
                            <Button variant="danger" size="sm" onClick={() => handleRejectJoinRequest(r.lawyerid, r.caseid)}>Reject</Button>
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </Card.Body>
        </Card>
      )}

                {selectedPage === 'hearingSchedule' && (
              <Card className="shadow-sm border-0" style={{ borderRadius: 16 }}>
                <Card.Body style={{ padding: 0 }}>
                  <RegistrarHearingSchedule />
                </Card.Body>
              </Card>
            )}

            
            {selectedPage === 'appeals' && (
              <Card className="shadow-sm border-0" style={{ borderRadius: 16 }}>
                <Card.Body>
                  <div className="d-flex justify-content-between align-items-center mb-3">
                    <div>
                      <h2 className="fw-bold mb-1" style={{ color: '#22304a' }}><i className="bi bi-balance-scale me-2"></i>Appeals Monitoring</h2>
                      <div className="text-muted mb-2">View and monitor appeals heard by the court. Update decision and status as needed.</div>
                    </div>
                  </div>
                  <InputGroup className="mb-3" style={{ maxWidth: 400 }}>
                    <InputGroup.Text><i className="bi bi-search"></i></InputGroup.Text>
                    <Form.Control placeholder="Search appeals by lawyer, case, client, or status..." value={searchAppeal} onChange={e => setSearchAppeal(e.target.value)} />
                  </InputGroup>
                  <div className="table-responsive">
                    <table className="table align-middle mb-0">
                      <thead style={{ background: '#f4f6fa' }}>
                        <tr style={{ color: '#22304a', fontWeight: 600 }}>
                          <th>Lawyer</th>
                          <th>Case Name</th>
                          <th>Client</th>
                          <th>Appeal Date</th>
                          <th>Status</th>
                          <th>Decision Date</th>
                          <th>Decision</th>
                          <th>Action</th>
                        </tr>
                      </thead>
                      <tbody>
                        {filteredAppeals.map((appeal, i) => (
                          <tr key={appeal.id}>
                            <td>{appeal.lawyerName}</td>
                            <td>{appeal.caseName}</td>
                            <td>{appeal.clientName}</td>
                            <td>{appeal.appealDate}</td>
                            <td>{appeal.status}</td>
                            <td>{appeal.decisionDate || '-'}</td>
                            <td>{appeal.decision || '-'}</td>
                            <td>
                              <Button variant="outline-primary" size="sm" onClick={() => handleOpenDecisionModal(appeal)}>
                                Update Decision
                              </Button>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </Card.Body>
              </Card>
            )}
            {selectedPage === 'evidence' && (
              <Card className="mb-4">
                <Card.Header>
                  <h5 className="mb-0">Evidence</h5>
                  <p className="text-muted mb-0">View evidence submitted by lawyers/clients</p>
                </Card.Header>
                <Card.Body>
                  <InputGroup className="mb-3">
                    <InputGroup.Text>
                      <Search size={18} />
                    </InputGroup.Text>
                    <Form.Control
                      placeholder="Search by case, type, description, file, or lawyer..."
                      value={searchEvidence}
                      onChange={(e) => setSearchEvidence(e.target.value)}
                    />
                  </InputGroup>
                  <div className="table-responsive">
                    <table className="table table-hover">
                      <thead>
                        <tr>
                          <th>Evidence Type</th>
                          <th>Description</th>
                          <th>Submission Date</th>
                          <th>Case Name</th>
                          <th>Lawyer Name</th>
                          <th>File</th>
                        </tr>
                      </thead>
                      <tbody>
                        {filteredEvidence.map(e => (
                          <tr key={e.id}>
                            <td>{e.evidenceType}</td>
                            <td>{e.description}</td>
                            <td>{e.submissionDate}</td>
                            <td>{e.caseName}</td>
                            <td>{e.lawyerName}</td>
                            <td>{e.file ? <a href={`#/${e.file}`} download>{e.file}</a> : '-'}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </Card.Body>
              </Card>
            )}
            {selectedPage === 'witnesses' && (
  <Card className="mb-4">
    <Card.Header>
      <h5 className="mb-0">Witnesses</h5>
      <p className="text-muted mb-0">View witnesses submitted by lawyers/clients</p>
    </Card.Header>
    <Card.Body>
      <InputGroup className="mb-3">
        <InputGroup.Text>
          <Search size={18} />
        </InputGroup.Text>
        <Form.Control
          placeholder="Search by name, case, contact, or lawyer..."
          value={searchWitness}
          onChange={(e) => setSearchWitness(e.target.value)}
        />
      </InputGroup>
      <div className="table-responsive">
        <table className="table table-hover">
          <thead>
            <tr>
              <th>Name</th>
              <th>Case Name</th>
              <th>Contact</th>
              <th>Status</th>
              <th>Lawyer Name</th>
            </tr>
          </thead>
          <tbody>
            {filteredWitnesses.map((witnessData) => {
              const { witness, cases } = witnessData; // Destructure witness and cases
              const caseStatement = cases[0]?.statement || 'No Case Info'; // Handle if cases array is empty

              return (
                <tr key={witness.id}>
                  <td>{`${witness.firstname} ${witness.lastname}`}</td>
                  <td>{caseStatement}</td>
                  <td>{witness.phone}</td>
                  <td>
                    <Badge bg={witness.status === 'Testified' ? 'success' : witness.status === 'Scheduled' ? 'info' : 'warning'}>
                      {witness.status || 'N/A'}
                    </Badge>
                  </td>
                  <td>{witness.lawyerName || 'Unknown'}</td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </Card.Body>
  </Card>
)}
            {selectedPage === 'payments' && (
      <Card className="shadow-sm border-0" style={{ borderRadius: 16 }}>
        <Card.Body>
          <div className="d-flex justify-content-between align-items-center mb-3">
            <div>
              <h2 className="fw-bold mb-1" style={{ color: '#22304a' }}>
                <i className="bi bi-credit-card me-2"></i>Payment Management
              </h2>
              <div className="text-muted mb-2">View and manage court payments from lawyers and clients.</div>
            </div>
            <Button
              variant="primary"
              className="d-flex align-items-center gap-2"
              onClick={() => {
                setEditingPayment(null);
                setPaymentForm({ caseid: '', purpose: '', balance: '', paymenttype: 'Court Fee' });
                setPaymentSubmitError('');
                setShowPaymentModal(true);
              }}
            >
              <Plus size={20} /> Create Payment Request
            </Button>
          </div>
          <InputGroup className="mb-3" style={{ maxWidth: 400 }}>
            <InputGroup.Text><i className="bi bi-search"></i></InputGroup.Text>
            <Form.Control
              placeholder="Search payments by case, lawyer, client, or status..."
              value={searchPayment}
              onChange={(e) => setSearchPayment(e.target.value)}
            />
          </InputGroup>

          {/* Displaying Loading Spinner if Data is Being Loaded */}
          {loadingPayments ? (
            <div>Loading payments...</div>
          ) : error ? (
            <div>{error}</div>
          ) : (
            <div className="table-responsive">
              <table className="table align-middle mb-0">
                <thead style={{ background: '#f4f6fa' }}>
                  <tr style={{ color: '#22304a', fontWeight: 600 }}>
                    <th>Case Name</th>
                    <th>Lawyer</th>
                    <th>Client</th>
                    <th>Payment Type</th>
                    <th>Purpose</th>
                    <th>Amount</th>
                    <th>Mode</th>
                    <th>Payment Date</th>
                    <th>Status</th>
                    <th>Actions</th>
                  </tr>
                </thead>
               <tbody>
  {courtPayments
    .filter(
      (p) =>
        (p.caseName?.toLowerCase() || '').includes(searchPayment.toLowerCase()) ||
        (p.lawyerName?.toLowerCase() || '').includes(searchPayment.toLowerCase()) ||
        (p.clientName?.toLowerCase() || '').includes(searchPayment.toLowerCase()) ||
        (p.status?.toLowerCase() || '').includes(searchPayment.toLowerCase())
    )
    .map((payment) => (
      <tr key={payment.id}>
        <td>{payment.caseName}</td>
        <td>{payment.lawyerName || 'N/A'}</td>  {/* Assuming you handle lawyerName properly */}
        <td>{payment.clientName || 'N/A'}</td>  {/* Assuming you handle clientName properly */}
        <td>{payment.paymentType}</td>
        <td>{payment.purpose}</td>
        <td>PKR {Number(payment.amount || 0).toLocaleString()}</td>
        <td>{payment.mode}</td>
        <td>{payment.paymentDate}</td>
        <td>
          <Badge bg={payment.status === 'Paid' ? 'success' : 'warning'}>
            {payment.status}
          </Badge>
        </td>
        <td>
          {/* <Button
            variant="outline-primary"
            size="sm"
            className="me-2"
            onClick={() => {
              setEditingPayment(payment);
              setPaymentForm(payment);
              setShowPaymentModal(true);
            }}
          >
            Edit
          </Button> */}
          {/* <Button
            variant="outline-danger"
            size="sm"
            onClick={() => {
              setConfirm({
                show: true,
                type: 'deletePayment',
                payload: payment,
              });
            }}
          >
            Delete
          </Button> */}
        </td>
      </tr>
    ))}
</tbody>

              </table>
            </div>
          )}
        </Card.Body>
      </Card>
            )}
            {selectedPage === 'prosecutors' && (
              <Card className="shadow-sm border-0" style={{ borderRadius: 16 }}>
                <Card.Body>
                  <div className="d-flex justify-content-between align-items-center mb-3">
                    <div>
                      <h2 className="fw-bold mb-1" style={{ color: '#22304a' }}><i className="bi bi-person-badge me-2"></i>Prosecutor Management</h2>
                      <div className="text-muted mb-2">Manage court prosecutors and their case assignments.</div>
                            </div>
                    <Button variant="primary" className="d-flex align-items-center gap-2" onClick={() => {
                      setEditingProsecutor(null);
                      setProsecutorForm({ name: '', experience: '', status: 'Active', assignedCases: [] });
                      setShowProsecutorModal(true);
                    }}>
                      <Plus size={20} /> Add Prosecutor
                    </Button>
                  </div>
                  <InputGroup className="mb-3" style={{ maxWidth: 400 }}>
                    <InputGroup.Text><i className="bi bi-search"></i></InputGroup.Text>
                    <Form.Control 
                      placeholder="Search prosecutors..." 
                      value={searchProsecutor} 
                      onChange={e => setSearchProsecutor(e.target.value)} 
                    />
                  </InputGroup>
                  <div className="table-responsive">
                    <table className="table align-middle mb-0">
                      <thead style={{ background: '#f4f6fa' }}>
                        <tr style={{ color: '#22304a', fontWeight: 600 }}>
                          <th>Name</th>
                          <th>Experience</th>
                          <th>Status</th>
                          <th>Assigned Cases</th>
                          <th>Actions</th>
                        </tr>
                      </thead>
                      <tbody>
                        {courtProsecutors
                          .filter(p => p.name.toLowerCase().includes(searchProsecutor.toLowerCase()))
                          .map((prosecutor) => (
                            <tr key={prosecutor.id}>
                              <td>{prosecutor.name}</td>
                              <td>{prosecutor.experience} years</td>
                              <td>
                                <Badge bg={prosecutor.status === 'Active' ? 'success' : 'warning'}>
                                  {prosecutor.status}
                                </Badge>
                              </td>
                              <td>
                                {prosecutor.assignedCases.length > 0 ? (
                                  <ul className="list-unstyled mb-0">
                                    {prosecutor.assignedCases.map((caseName, idx) => (
                                      <li key={idx}>{caseName}</li>
                                    ))}
                                  </ul>
                                ) : (
                                  <span className="text-muted">No cases assigned</span>
                                )}
                              </td>
                              <td>
                                <Button variant="outline-primary" size="sm" className="me-2" onClick={() => handleEditProsecutor(prosecutor)}>
                                  Edit
                                </Button>
                                <Button variant="outline-danger" size="sm" onClick={() => handleDeleteProsecutor(prosecutor.id)}>
                                  Remove
                                </Button>
                              </td>
                            </tr>
                          ))}
                      </tbody>
                    </table>
                  </div>
                </Card.Body>
              </Card>
            )}
            {selectedPage === 'judges' && (
  <Card className="shadow-sm border-0" style={{ borderRadius: 16 }}>
    <Card.Body>
      <div className="d-flex justify-content-between align-items-center mb-3">
        <div>
          <h2 className="fw-bold mb-1" style={{ color: '#22304a' }}>
            <i className="bi bi-person-badge me-2"></i>Judge Management
          </h2>
          <div className="text-muted mb-2">Manage court judges and their case assignments.</div>
        </div>
        <Button variant="primary" className="d-flex align-items-center gap-2" onClick={() => {
          setEditingJudge(null);
          setJudgeForm({ name: '', position: '', experience: '', appointmentDate: '', specialization: '', assignedCases: [] });
          setShowJudgeModal(true);
        }}>
          <Plus size={20} /> Add Judge
        </Button>
      </div>
      <InputGroup className="mb-3" style={{ maxWidth: 400 }}>
        <InputGroup.Text><i className="bi bi-search"></i></InputGroup.Text>
        <Form.Control
          placeholder="Search judges..."
          value={searchJudge}
          onChange={e => setSearchJudge(e.target.value)}
        />
      </InputGroup>
      <div className="table-responsive">
        <table className="table align-middle mb-0">
          <thead style={{ background: '#f4f6fa' }}>
            <tr style={{ color: '#22304a', fontWeight: 600 }}>
              <th>Name</th>
              <th>Position</th>
              <th>Experience (years)</th>
              <th>Appointment Date</th>
              <th>Specialization</th>
              <th>Assigned Cases</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {judges
              .filter(j => j.name?.toLowerCase().includes(searchJudge.toLowerCase()))
              .map((judge) => (
                <tr key={judge.judgeid}>
                  <td>{judge.name}</td>
                  <td>{judge.position}</td>
                  <td>{judge.expyears}</td>
                  <td>{judge.appointmentdate}</td>
                  <td>{judge.specialization}</td>
                  <td>
                    {judge.assigned_cases?.length > 0 ? (
                      <ul className="list-unstyled mb-0">
                        {judge.assigned_cases.map((caseName, idx) => (
                          <li key={idx}>{caseName}</li>
                        ))}
                      </ul>
                    ) : (
                      <span className="text-muted">No cases assigned</span>
                    )}
                  </td>
                  <td>
                    <Button variant="outline-primary" size="sm" className="me-2" onClick={() => handleEditJudge(judge)}>
                      Edit
                    </Button>
                    <Button variant="outline-danger" size="sm" onClick={() => handleDeleteJudge(judge)}>
                      Remove
                    </Button>
                  </td>
                </tr>
              ))}
          </tbody>
        </table>
      </div>
    </Card.Body>
  </Card>
)}

{selectedPage === 'remands' && (
  <Card className="shadow-sm border-0" style={{ borderRadius: 16 }}>
    <Card.Body>
      <div className="d-flex justify-content-between align-items-center mb-3">
        <div>
          <h2 className="fw-bold mb-1" style={{ color: '#22304a' }}>
            <i className="bi bi-gavel me-2"></i>Remand Management
          </h2>
          <div className="text-muted mb-2">Manage remands for cases in your court.</div>
        </div>
        <Button variant="primary" className="d-flex align-items-center gap-2" onClick={() => {
          setEditingRemand(null);
          setRemandForm({
            caseName: '',
            lawyerName: '',
            clientName: '',
            remandType: '',
            remandDate: '',
            remandReason: '',
            status: '',
            duration: ''
          });
          setShowRemandModal(true);
        }}>
          <Plus size={20} /> Add Remand
        </Button>
      </div>
      <InputGroup className="mb-3" style={{ maxWidth: 400 }}>
        <InputGroup.Text><i className="bi bi-search"></i></InputGroup.Text>
        <Form.Control placeholder="Search remands..." />
      </InputGroup>
      <div className="table-responsive">
        <table className="table align-middle mb-0">
          <thead style={{ background: '#f4f6fa' }}>
            <tr style={{ color: '#22304a', fontWeight: 600 }}>
              <th>Case Title</th>
              <th>Remand Type</th>
              <th>Remand Date</th>
              <th>Reason</th>
              <th>Status</th>
              <th>Duration (days)</th>
            </tr>
          </thead>
          <tbody>
            {remands.length === 0 ? (
              <tr>
                <td colSpan={6} className="text-center text-muted">No remands found</td>
              </tr>
            ) : (
              remands.map((r, idx) => (
                <tr key={idx}>
                  <td>{r.title}</td>
                  <td>{r.remandtype}</td>
                  <td>{r.remanddate}</td>
                  <td>{r.remandreason}</td>
                  <td>{r.status}</td>
                  <td>{r.duration}</td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </Card.Body>
  </Card>
)}


          
            {selectedPage === 'caseHistory' && (
              <>
                <Card className="shadow-sm border-0" style={{ borderRadius: 16 }}>
                  <Card.Body>
                    <div className="d-flex justify-content-between align-items-center mb-3">
                      <div>
                        <h2 className="fw-bold mb-1" style={{ color: '#22304a' }}><i className="bi bi-clock-history me-2"></i>Manage Case History</h2>
                        <div className="text-muted mb-2">Click <strong>History</strong> on any case to view or add to the full case timeline.</div>
                      </div>
                      <Button variant="primary" onClick={() => { setEditingCaseHistory(null); setCaseHistoryForm({ caseName: '', judgeName: '', clientName: '', lawyerName: '', remarks: '', actionDate: '', actionTaken: '', status: '' }); setShowCaseHistoryModal(true); }}>
                        Add Note
                      </Button>
                    </div>
                    <div className="table-responsive">
                      <table className="table align-middle mb-0">
                        <thead className="table-light">
                          <tr>
                            <th>Case Name</th>
                            <th>Case Number</th>
                            <th>Type</th>
                            <th>Filing Date</th>
                            <th>Client</th>
                            <th>Lawyer</th>
                            <th>Judge</th>
                            <th>Status</th>
                            <th>History</th>
                          </tr>
                        </thead>
                        <tbody>
                          {courtCases.length === 0 ? (
                            <tr>
                              <td colSpan={9} className="text-center text-muted py-4">
                                No cases found.
                              </td>
                            </tr>
                          ) : (
                            courtCases.map(case_ => (
                              <tr key={case_.caseid}>
                                <td>{case_.title || '—'}</td>
                                <td>{case_.casenumber || '—'}</td>
                                <td>{case_.casetype || '—'}</td>
                                <td>{case_.filingdate || '—'}</td>
                                <td>{case_.clientName || '—'}</td>
                                <td>{case_.lawyername || '—'}</td>
                                <td>{case_.judgeName || '—'}</td>
                                <td>
                                  <Badge bg={case_.status === 'Closed' ? 'success' : case_.status === 'In Progress' ? 'warning' : 'secondary'}>
                                    {case_.status || '—'}
                                  </Badge>
                                </td>
                                <td>
                                  <Button
                                    variant="outline-info"
                                    size="sm"
                                    onClick={() => handleCaseView(case_)}
                                  >
                                    History
                                  </Button>
                                </td>
                              </tr>
                            ))
                          )}
                        </tbody>
                      </table>
                    </div>
                  </Card.Body>
                </Card>
                <Modal show={showCaseHistoryModal} onHide={() => { setShowCaseHistoryModal(false); setEditingCaseHistory(null); }} centered>
                  <Modal.Header closeButton>
                    <Modal.Title>{editingCaseHistory ? 'Edit Case History Entry' : 'Add Case History Entry'}</Modal.Title>
                  </Modal.Header>
                  <Form onSubmit={handleCaseHistorySubmit}>
                    <Modal.Body>
                      <Form.Group className="mb-3">
                        <Form.Label>Case Name</Form.Label>
                        <Form.Control type="text" name="caseName" value={caseHistoryForm.caseName} onChange={handleCaseHistoryFormChange} required />
                      </Form.Group>
                      <Form.Group className="mb-3">
                        <Form.Label>Judge Name</Form.Label>
                        <Form.Control type="text" name="judgeName" value={caseHistoryForm.judgeName} onChange={handleCaseHistoryFormChange} required />
                      </Form.Group>
                      <Form.Group className="mb-3">
                        <Form.Label>Client Name</Form.Label>
                        <Form.Control type="text" name="clientName" value={caseHistoryForm.clientName} onChange={handleCaseHistoryFormChange} />
                      </Form.Group>
                      <Form.Group className="mb-3">
                        <Form.Label>Lawyer Name</Form.Label>
                        <Form.Control type="text" name="lawyerName" value={caseHistoryForm.lawyerName} onChange={handleCaseHistoryFormChange} />
                      </Form.Group>
                      <Form.Group className="mb-3">
                        <Form.Label>Remarks</Form.Label>
                        <Form.Control as="textarea" name="remarks" value={caseHistoryForm.remarks} onChange={handleCaseHistoryFormChange} />
                      </Form.Group>
                      <Form.Group className="mb-3">
                        <Form.Label>Action Date</Form.Label>
                        <Form.Control type="date" name="actionDate" value={caseHistoryForm.actionDate} onChange={handleCaseHistoryFormChange} required />
                      </Form.Group>
                      <Form.Group className="mb-3">
                        <Form.Label>Action Taken</Form.Label>
                        <Form.Control type="text" name="actionTaken" value={caseHistoryForm.actionTaken} onChange={handleCaseHistoryFormChange} required />
                      </Form.Group>
                      <Form.Group className="mb-3">
                        <Form.Label>Status</Form.Label>
                        <Form.Select name="status" value={caseHistoryForm.status} onChange={handleCaseHistoryFormChange} required>
                          <option value="">Select status</option>
                          <option value="Pending">Pending</option>
                          <option value="Completed">Completed</option>
                          <option value="Adjourned">Adjourned</option>
                          <option value="Cancelled">Cancelled</option>
                        </Form.Select>
                      </Form.Group>
                    </Modal.Body>
                    <Modal.Footer>
                      <Button variant="secondary" onClick={() => { setShowCaseHistoryModal(false); setEditingCaseHistory(null); }}>Cancel</Button>
                      <Button variant="primary" type="submit">{editingCaseHistory ? 'Save Changes' : 'Add Entry'}</Button>
                    </Modal.Footer>
                  </Form>
                </Modal>
              </>
            )}
          </div>
        </div>
      </div>

      {/* Toasts */}
      <Toast
        show={toast.show}
        onClose={() => setToast({ ...toast, show: false })}
        bg={toast.variant}
        delay={2500}
        autohide
        style={{ position: 'fixed', top: 20, right: 20, zIndex: 9999 }}
      >
        <Toast.Body className="text-white">{toast.message}</Toast.Body>
      </Toast>

      {/* Register/Edit Court Modal */}
      <Modal show={showCourtModal} onHide={() => { setShowCourtModal(false); setEditingCourt(null); }} centered>
        <Modal.Header closeButton>
          <Modal.Title>{editingCourt ? 'Edit Court' : 'Edit Court'}</Modal.Title>
        </Modal.Header>
        <Form onSubmit={handleCourtSubmit}>
          <Modal.Body>
            <Form.Group className="mb-3">
              <Form.Label>Court Name</Form.Label>
              <Form.Control
                type="text"
                name="name"
                value={courtForm.name}
                onChange={handleCourtFormChange}
                required
                autoFocus
              />
            </Form.Group>
            <Form.Group className="mb-3">
              <Form.Label>Location</Form.Label>
              <Form.Control
                type="text"
                name="location"
                value={courtForm.location}
                onChange={handleCourtFormChange}
                required
              />
            </Form.Group>
            <Form.Group className="mb-3">
              <Form.Label>Type</Form.Label>
              <Form.Control
                type="text"
                name="type"
                value={courtForm.type}
                onChange={handleCourtFormChange}
                required
              />
            </Form.Group>
          </Modal.Body>
          <Modal.Footer>
            <Button variant="secondary" onClick={() => { setShowCourtModal(false); setEditingCourt(null); }}>
              Cancel
            </Button>
            <Button variant="primary" type="submit" disabled={loading}>
              {loading ? <Spinner animation="border" size="sm" className="me-2" /> : null}
              {editingCourt ? 'Save Changes' : 'Save Changes'}
            </Button>
          </Modal.Footer>
        </Form>
      </Modal>

   <Modal show={confirm.show} onHide={() => setConfirm({ show: false, type: '', payload: null })} centered>
  <Modal.Header closeButton>
    <Modal.Title>Confirm Delete</Modal.Title>
  </Modal.Header>
  <Modal.Body>
    {confirm.type === 'deleteRoom' && (
      <span>Are you sure you want to delete courtroom <b>#{confirm.payload?.number}</b>?</span>
    )}
    {confirm.type === 'deleteCourt' && (
      <span>Are you sure you want to delete the court <b>{confirm.payload?.name}</b>?</span>
    )}
    {confirm.type === 'deletePayment' && (
      <span>Are you sure you want to delete the payment record for <b>{confirm.payload?.caseName}</b>?</span>
    )}
    {/* Add more types if needed */}
  </Modal.Body>
  <Modal.Footer>
    <Button variant="secondary" onClick={() => setConfirm({ show: false, type: '', payload: null })}>
      Cancel
    </Button>
    <Button
      variant="danger"
      onClick={() => {
        if (confirm.type === 'deleteRoom') {
          handleConfirmDeleteRoom();
        } else if (confirm.type === 'deleteCourt') {
          confirmDeleteCourt();
        } else if (confirm.type === 'deletePayment') {
          // Call handleConfirmDeletePayment() if you implement that
        }
      }}
    >
      Delete
    </Button>
  </Modal.Footer>
</Modal>




      {/* Add/Edit Room Modal (full form) */}
      <Modal show={showRoomModal} onHide={() => { setShowRoomModal(false); setEditingRoom(null); }} centered>
        <Modal.Header closeButton>
          <Modal.Title>{editingRoom ? 'Edit Court Room' : 'Add Court Room'}</Modal.Title>
        </Modal.Header>
        <Form onSubmit={handleRoomSubmit}>
          <Modal.Body>
            <Form.Group className="mb-3">
              <Form.Label>Room Number</Form.Label>
              <Form.Control type="text" name="number" value={roomForm.number} onChange={handleRoomFormChange} required autoFocus />
            </Form.Group>
            <Form.Group className="mb-3">
              <Form.Label>Capacity</Form.Label>
              <Form.Control type="number" name="capacity" value={roomForm.capacity} onChange={handleRoomFormChange} required />
            </Form.Group>
            <Form.Group className="mb-3">
              <Form.Label>Status</Form.Label>
              <Form.Select name="status" value={roomForm.status} onChange={handleRoomFormChange} required>
                <option value="">Select status</option>
                <option value="Available">Available</option>
                <option value="Occupied">Occupied</option>
                <option value="Maintenance">Maintenance</option>
                <option value="Reserved">Reserved</option>
              </Form.Select>
            </Form.Group>
          </Modal.Body>
          <Modal.Footer>
            <Button variant="secondary" onClick={() => { setShowRoomModal(false); setEditingRoom(null); }}>Cancel</Button>
            <Button variant="primary" type="submit" disabled={loading}>{loading ? <Spinner animation="border" size="sm" className="me-2" /> : null}{editingRoom ? 'Save Changes' : 'Add Room'}</Button>
          </Modal.Footer>
        </Form>
      </Modal>

      {/* Add/Edit Appeal Modal */}
      <Modal show={showAppealModal} onHide={() => { setShowAppealModal(false); setEditingAppeal(null); }} centered>
        <Modal.Header closeButton>
          <Modal.Title>{editingAppeal ? 'Edit Appeal' : 'Add New Appeal'}</Modal.Title>
        </Modal.Header>
        <Form onSubmit={handleAppealSubmit}>
          <Modal.Body>
            <Form.Group className="mb-3">
              <Form.Label>Appeal Number</Form.Label>
              <Form.Control type="text" name="appealNumber" value={appealForm.appealNumber} onChange={handleAppealFormChange} required autoFocus />
            </Form.Group>
            <Form.Group className="mb-3">
              <Form.Label>Original Case ID</Form.Label>
              <Form.Control type="text" name="originalCaseId" value={appealForm.originalCaseId} onChange={handleAppealFormChange} required />
            </Form.Group>
            <Form.Group className="mb-3">
              <Form.Label>Appellant</Form.Label>
              <Form.Control type="text" name="appellant" value={appealForm.appellant} onChange={handleAppealFormChange} required />
            </Form.Group>
            <Form.Group className="mb-3">
              <Form.Label>Respondent</Form.Label>
              <Form.Control type="text" name="respondent" value={appealForm.respondent} onChange={handleAppealFormChange} required />
            </Form.Group>
            <Form.Group className="mb-3">
              <Form.Label>Date Filed</Form.Label>
              <Form.Control type="date" name="dateFiled" value={appealForm.dateFiled} onChange={handleAppealFormChange} required />
            </Form.Group>
            <Form.Group className="mb-3">
              <Form.Label>Status</Form.Label>
              <Form.Select name="status" value={appealForm.status} onChange={handleAppealFormChange} required>
                <option value="">Select status</option>
                <option value="Under Review">Under Review</option>
                <option value="Hearing Scheduled">Hearing Scheduled</option>
                <option value="Decided">Decided</option>
              </Form.Select>
            </Form.Group>
          </Modal.Body>
          <Modal.Footer>
            <Button variant="secondary" onClick={() => { setShowAppealModal(false); setEditingAppeal(null); }}>
              Cancel
            </Button>
            <Button variant="primary" type="submit" disabled={loading}>
              {loading ? <Spinner animation="border" size="sm" className="me-2" /> : null}
              {editingAppeal ? 'Save Changes' : 'Add Appeal'}
            </Button>
          </Modal.Footer>
        </Form>
      </Modal>
{/* <Modal show={confirm.show} onHide={() => setConfirm({ show: false, type: '', payload: null })} centered>
  <Modal.Header closeButton>
    <Modal.Title>Confirm Delete</Modal.Title>
  </Modal.Header>
  <Modal.Body>
  {confirm.type === 'deleteRoom' && (
    <span>Are you sure you want to delete courtroom <b>#{confirm.payload?.number}</b>?</span>
  )}
  {confirm.type === 'deleteCourt' && (
    <span>Are you sure you want to delete the court <b>{confirm.payload?.name}</b>?</span>
  )}
  {confirm.type === 'deletePayment' && (
    <span>Are you sure you want to delete the payment record for <b>{confirm.payload?.caseName}</b>?</span>
  )}
</Modal.Body>

  <Modal.Footer>
    <Button variant="secondary" onClick={() => setConfirm({ show: false, type: '', payload: null })}>
      Cancel
    </Button>
    <Button
      variant="danger"
      onClick={() => {
        if (confirm.type === 'deleteCourt') handleConfirmDeleteCourt();
        if (confirm.type === 'deleteRoom') handleConfirmDeleteRoom();
        if (confirm.type === 'deletePayment') handleConfirmDeletePayment();
      }}
    >
      Delete
    </Button>
  </Modal.Footer>
</Modal> */}

      {/* Room View Modal */}
      <Modal show={showRoomViewModal} onHide={() => setShowRoomViewModal(false)} centered>
        <Modal.Header closeButton><Modal.Title>Room Details</Modal.Title></Modal.Header>
        <Modal.Body>
          {viewingRoom && <div><b>Name/Number:</b> {viewingRoom.name}</div>}
        </Modal.Body>
        <Modal.Footer>
          <Button variant="secondary" onClick={() => setShowRoomViewModal(false)}>Close</Button>
        </Modal.Footer>
      </Modal>

      {/* Case Add/Edit Modal */}
      <Modal show={showCaseModal} onHide={() => { setShowCaseModal(false); setEditingCase(null); }} centered>
        <Modal.Header closeButton>
          <Modal.Title>{editingCase ? 'Verify New Case' : 'Verify New Case'}</Modal.Title>
        </Modal.Header>
        <Form onSubmit={handleCaseSubmit}>
          <Modal.Body>
            <Form.Group className="mb-3">
              <Form.Label>Case Name</Form.Label>
              <Form.Control
                type="text"
                value={caseForm.title}
                readOnly
                disabled
              />
            </Form.Group>
            <Form.Group className="mb-3">
              <Form.Label>Type</Form.Label>
              <Form.Select
                value={caseForm.caseType}
                readOnly
                disabled
              >
                <option value="">Select type</option>
                <option value="Criminal">Criminal</option>
                <option value="Civil">Civil</option>
                <option value="Family">Family</option>
                <option value="Corporate">Corporate</option>
              </Form.Select>
            </Form.Group>
            <Form.Group className="mb-3">
              <Form.Label>Filing Date</Form.Label>
              <Form.Control
                type="date"
                value={caseForm.filingDate}
                readOnly
                disabled
              />
            </Form.Group>
            <Form.Group className="mb-3">
              <Form.Label>Client Name</Form.Label>
              <Form.Control
                type="text"
                value={caseForm.clientName}
                readOnly
                disabled
              />
            </Form.Group>
            <Form.Group className="mb-3">
              <Form.Label>Lawyer Name</Form.Label>
              <Form.Control
                type="text"
                value={caseForm.lawyerName}
                readOnly
                disabled
              />
            </Form.Group>
            <Form.Group className="mb-3">
              <Form.Label>Prosecutor</Form.Label>
              <Form.Select
                value={caseForm.prosecutor}
                readOnly
                disabled
              >
                <option value="">Select prosecutor</option>
                {courtProsecutors.map(prosecutor => (
                  <option key={prosecutor.id} value={prosecutor.name}>
                    {prosecutor.name}
                  </option>
                ))}
              </Form.Select>
            </Form.Group>
            <Form.Group className="mb-3">
              <Form.Label>Judge</Form.Label>
              <Form.Select
                value={caseForm.judgeName}
                onChange={e => setCaseForm({ ...caseForm, judgeName: e.target.value })}
                required
              >
                <option value="">Select judge</option>
                {courtJudges.map(judge => (
                  <option key={judge.id} value={judge.name}>{judge.name}</option>
                ))}
              </Form.Select>
            </Form.Group>
          </Modal.Body>
          <Modal.Footer>
            <Button variant="secondary" onClick={() => { setShowCaseModal(false); setEditingCase(null); }}>Cancel</Button>
            <Button variant="primary" type="submit" disabled={loading}>{loading ? <Spinner animation="border" size="sm" className="me-2" /> : null}{editingCase ? 'Verify' : 'Verify'}</Button>
          </Modal.Footer>
        </Form>
      </Modal>

      {/* Case View Modal — full timeline */}
      <Modal show={showCaseViewModal} onHide={() => setShowCaseViewModal(false)} centered size="lg">
        <Modal.Header closeButton>
          <div>
            <Modal.Title className="fw-bold">
              {viewingCase?.title || 'Case History'}
            </Modal.Title>
            {viewingCase?.casenumber && (
              <small className="text-muted">{viewingCase.casenumber}</small>
            )}
          </div>
        </Modal.Header>
        <Modal.Body style={{ maxHeight: '70vh', overflowY: 'auto' }}>
          {/* Case summary strip */}
          {viewingCase && (
            <div className="d-flex flex-wrap gap-3 mb-4 p-3 rounded" style={{ background: '#f8f9fa' }}>
              <div><span className="text-muted small">Client</span><br /><strong>{viewingCase.clientname || viewingCase.clientName || '—'}</strong></div>
              <div><span className="text-muted small">Lawyer</span><br /><strong>{viewingCase.lawyername || viewingCase.lawyerName || '—'}</strong></div>
              <div><span className="text-muted small">Judge</span><br /><strong>{viewingCase.judgeName || '—'}</strong></div>
              <div><span className="text-muted small">Status</span><br />
                <Badge bg={viewingCase.status === 'Closed' ? 'success' : viewingCase.status === 'Open' ? 'primary' : 'secondary'}>
                  {viewingCase.status || '—'}
                </Badge>
              </div>
            </div>
          )}

          {/* Timeline */}
          {loadingTimeline ? (
            <div className="text-center text-muted py-4">
              <div style={{ fontSize: 32 }}>⏳</div>
              <div>Loading timeline...</div>
            </div>
          ) : caseHistory.length === 0 ? (
            <div className="text-center text-muted py-4">
              <div style={{ fontSize: 32 }}>📋</div>
              <div>No history recorded for this case yet.</div>
            </div>
          ) : (
            <div style={{ position: 'relative', paddingLeft: 28 }}>
              {/* vertical line */}
              <div style={{
                position: 'absolute', left: 10, top: 0, bottom: 0,
                width: 2, background: '#dee2e6', zIndex: 0
              }} />

              {caseHistory.map((entry, idx) => {
                const isAuto   = entry.eventType === 'auto';
                const dotColor = isAuto ? '#6c757d' : '#0d6efd';
                return (
                  <div key={entry.historyid || idx} className="mb-4" style={{ position: 'relative', zIndex: 1 }}>
                    {/* dot */}
                    <div style={{
                      position: 'absolute', left: -22, top: 4,
                      width: 14, height: 14, borderRadius: '50%',
                      background: dotColor, border: '2px solid #fff',
                      boxShadow: '0 0 0 2px ' + dotColor,
                    }} />
                    {/* content */}
                    <div className="ps-2">
                      <div className="d-flex align-items-center gap-2 mb-1 flex-wrap">
                        <span className="text-muted small">
                          {entry.actionDate || '—'}
                        </span>
                        <Badge bg={isAuto ? 'secondary' : 'info'} style={{ fontSize: '0.65rem' }}>
                          {isAuto ? 'System' : 'Note'}
                        </Badge>
                      </div>
                      <div className="fw-semibold">{entry.actionTaken || entry.event || '—'}</div>
                      {entry.remarks && (
                        <div className="text-muted small mt-1">{entry.remarks}</div>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </Modal.Body>
        <Modal.Footer>
          <Button variant="secondary" onClick={() => setShowCaseViewModal(false)}>Close</Button>
        </Modal.Footer>
      </Modal>

      {/* Profile Modal */}
      <Modal show={showProfileModal} onHide={() => setShowProfileModal(false)} centered size="lg">
        <Modal.Header closeButton>
          <Modal.Title>Registrar Profile</Modal.Title>
        </Modal.Header>
        <Modal.Body>
          <Row className="g-4">
            {/* Profile Header - Left Panel */}
            <Col xs={12} md={4}>
              <Card className="shadow-sm h-100">
                <Card.Body className="text-center p-4">
                    <div className="position-relative d-inline-block mb-3">
                    <img
                      src={profileImage}
                      alt="Registrar Avatar"
                      className="rounded-circle border-4 border-primary shadow-sm"
                      width={150}
                      height={150}
                      style={{ objectFit: 'cover' }}
                      onError={e => { e.target.onerror = null; e.target.src = `https://picsum.photos/seed/${profileData.name || 'registrar'}/150/150`; }}
                    />
                    {isEditingProfile && (
                      <Button
                        variant="light"
                        size="sm"
                        className="position-absolute bottom-0 end-0 rounded-circle border shadow-sm"
                        style={{ width: '32px', height: '32px', lineHeight: '1', padding: '0.3rem' }}
                        onClick={triggerProfileImageUpload}
                        title="Upload new picture"
                      >
                        <Upload size={16} />
                      </Button>
                    )}
                    <input
                      type="file"
                      ref={fileInputRef}
                      onChange={handleProfileImageUpload}
                      accept="image/*"
                      className="d-none"
                    />
                  </div>
                  <h4 className="mb-1 fw-semibold text-primary">{profileData.name}</h4>
                  <div className="d-grid gap-2 d-sm-flex justify-content-sm-center mb-3">
                    <Button variant="outline-primary" size="sm" href={`mailto:${profileData.email}`}>
                      <Mail size={16} className="me-1" /> Email
                    </Button>
                    <Button variant="outline-primary" size="sm" href={`tel:${profileData.phone}`}>
                      <Phone size={16} className="me-1" /> Call
                    </Button>
                  </div>
                  <hr />
                  <div className="text-start">
                    <p className="mb-2 d-flex align-items-start">
                      <MapPin size={18} className="me-2 text-primary shrink-0 mt-1" />
                      <span>{profileData.court || 'N/A'}</span>
                    </p>
                  </div>
                </Card.Body>
              </Card>
            </Col>
            {/* Profile Details - Right Panel */}
            <Col xs={12} md={8}>
              <Card className="shadow-sm mb-4">
                <Card.Header className="bg-light">
                  <div className="d-flex justify-content-between align-items-center">
                    <h5 className="mb-0 text-primary">Registrar Information</h5>
                    <div>
                      {isEditingProfile ? (
                        <>
                          <Button variant="success" size="sm" onClick={handleProfileSave} className="me-2">
                            <Save size={16} className="me-1" /> Save
                          </Button>
                          <Button variant="outline-secondary" size="sm" onClick={() => setIsEditingProfile(false)}>
                            Cancel
                          </Button>
                        </>
                      ) : (
                        <Button variant="outline-primary" size="sm" onClick={() => setIsEditingProfile(true)}>
                          <Edit3 size={16} className="me-1" /> Edit Profile
                        </Button>
                      )}
                    </div>
                  </div>
                </Card.Header>
                <Card.Body className="p-4">
                  <Form>
                    <Row className="g-3">
                      <Col md={12}>
                        <Form.Group>
                          <Form.Label>Name</Form.Label>
                          <Form.Control
                            type="text"
                            name="name"
                            value={profileData.name}
                            disabled={!isEditingProfile}
                            onChange={handleProfileChange}
                          />
                        </Form.Group>
                      </Col>
                      <Col md={6}>
                        <Form.Group>
                          <Form.Label>Email</Form.Label>
                          <Form.Control
                            type="email"
                            name="email"
                            value={profileData.email}
                            disabled={!isEditingProfile}
                            onChange={handleProfileChange}
                          />
                        </Form.Group>
                      </Col>
                      <Col md={6}>
                        <Form.Group>
                          <Form.Label>Phone</Form.Label>
                          <Form.Control
                            type="text"
                            name="phone"
                            value={profileData.phone}
                            disabled={!isEditingProfile}
                            onChange={handleProfileChange}
                          />
                        </Form.Group>
                      </Col>
                      <Col md={12}>
                        <Form.Group>
                          <Form.Label>Court</Form.Label>
                          <Form.Control
                            type="text"
                            name="court"
                            value={profileData.court}
                            disabled={!isEditingProfile}
                            onChange={handleProfileChange}
                          />
                        </Form.Group>
                      </Col>
                    </Row>
                  </Form>
                </Card.Body>
              </Card>
            </Col>
          </Row>
        </Modal.Body>
      </Modal>

      {/* Final Decision Modal */}
      <Modal show={showFinalDecisionModal} onHide={() => setShowFinalDecisionModal(false)} centered>
        <Modal.Header closeButton>
          <Modal.Title>Final Decision</Modal.Title>
        </Modal.Header>
        <Modal.Body>
          {selectedCase && (
            <>
              <div><strong>Decision Date:</strong> {selectedCase.decisionDate || '-'}</div>
              <div><strong>Summary:</strong> {selectedCase.decisionSummary || '-'}</div>
              <div><strong>Verdict:</strong> {selectedCase.verdict || '-'}</div>
            </>
          )}
        </Modal.Body>
        <Modal.Footer>
          <Button variant="secondary" onClick={() => setShowFinalDecisionModal(false)}>Close</Button>
        </Modal.Footer>
      </Modal>

      {/* Evidence Add/Edit Modal */}
      <Modal show={showEvidenceModal} onHide={() => { setShowEvidenceModal(false); setEditingEvidence(null); }} centered>
        <Modal.Header closeButton>
          <Modal.Title>{editingEvidence ? 'Edit Evidence' : 'Add Evidence'}</Modal.Title>
        </Modal.Header>
        <Form onSubmit={handleEvidenceSubmit}>
          <Modal.Body>
            <Form.Group className="mb-3">
              <Form.Label>Case</Form.Label>
              <Form.Select name="caseTitle" value={evidenceForm.caseTitle} onChange={handleEvidenceFormChange} required>
                <option value="">Select case</option>
                {cases.map(c => (
                  <option key={c.id} value={c.title}>{c.title}</option>
                ))}
              </Form.Select>
            </Form.Group>
            <Form.Group className="mb-3">
              <Form.Label>Type</Form.Label>
              <Form.Select name="type" value={evidenceForm.type} onChange={handleEvidenceFormChange} required>
                <option value="">Select type</option>
                <option value="Document">Document</option>
                <option value="Physical">Physical</option>
                <option value="Digital">Digital</option>
                <option value="Testimony">Testimony</option>
              </Form.Select>
            </Form.Group>
            <Form.Group className="mb-3">
              <Form.Label>Description</Form.Label>
              <Form.Control type="text" name="description" value={evidenceForm.description} onChange={handleEvidenceFormChange} required />
            </Form.Group>
            <Form.Group className="mb-3">
              <Form.Label>Date Added</Form.Label>
              <Form.Control type="date" name="dateAdded" value={evidenceForm.dateAdded} onChange={handleEvidenceFormChange} required />
            </Form.Group>
            <Form.Group className="mb-3">
              <Form.Label>Status</Form.Label>
              <Form.Select name="status" value={evidenceForm.status} onChange={handleEvidenceFormChange} required>
                <option value="Pending">Pending</option>
                <option value="Verified">Verified</option>
                <option value="Rejected">Rejected</option>
              </Form.Select>
            </Form.Group>
          </Modal.Body>
          <Modal.Footer>
            <Button variant="secondary" onClick={() => { setShowEvidenceModal(false); setEditingEvidence(null); }}>Cancel</Button>
            <Button variant="primary" type="submit" disabled={loading}>{loading ? <Spinner animation="border" size="sm" className="me-2" /> : null}{editingEvidence ? 'Save Changes' : 'Add Evidence'}</Button>
          </Modal.Footer>
        </Form>
      </Modal>

      {/* Evidence View Modal */}
      <Modal show={showEvidenceViewModal} onHide={() => setShowEvidenceViewModal(false)} centered>
        <Modal.Header closeButton>
          <Modal.Title>Evidence Details</Modal.Title>
        </Modal.Header>
        <Modal.Body>
          {viewingEvidence && (
            <div>
              <div className="mb-3">
                <h6>Case</h6>
                <p>{viewingEvidence.caseTitle}</p>
              </div>
              <div className="mb-3">
                <h6>Type</h6>
                <p>{viewingEvidence.type}</p>
              </div>
              <div className="mb-3">
                <h6>Description</h6>
                <p>{viewingEvidence.description}</p>
              </div>
              <div className="mb-3">
                <h6>Date Added</h6>
                <p>{viewingEvidence.dateAdded}</p>
              </div>
              <div>
                <h6>Status</h6>
                <p>{viewingEvidence.status}</p>
              </div>
            </div>
          )}
        </Modal.Body>
        <Modal.Footer>
          <Button variant="secondary" onClick={() => setShowEvidenceViewModal(false)}>Close</Button>
        </Modal.Footer>
      </Modal>

      {/* Witness Add/Edit Modal */}
      <Modal show={showWitnessModal} onHide={() => { setShowWitnessModal(false); setEditingWitness(null); }} centered>
        <Modal.Header closeButton>
          <Modal.Title>{editingWitness ? 'Edit Witness' : 'Add Witness'}</Modal.Title>
        </Modal.Header>
        <Form onSubmit={handleWitnessSubmit}>
          <Modal.Body>
            <Form.Group className="mb-3">
              <Form.Label>Name</Form.Label>
              <Form.Control type="text" name="name" value={witnessForm.name} onChange={handleWitnessFormChange} required />
            </Form.Group>
            <Form.Group className="mb-3">
              <Form.Label>Case</Form.Label>
              <Form.Select name="caseTitle" value={witnessForm.caseTitle} onChange={handleWitnessFormChange} required>
                <option value="">Select case</option>
                {cases.map(c => (
                  <option key={c.id} value={c.title}>{c.title}</option>
                ))}
              </Form.Select>
            </Form.Group>
            <Form.Group className="mb-3">
              <Form.Label>Contact</Form.Label>
              <Form.Control type="text" name="contact" value={witnessForm.contact} onChange={handleWitnessFormChange} required />
            </Form.Group>
            <Form.Group className="mb-3">
              <Form.Label>Status</Form.Label>
              <Form.Select name="status" value={witnessForm.status} onChange={handleWitnessFormChange} required>
                <option value="Pending">Pending</option>
                <option value="Scheduled">Scheduled</option>
                <option value="Testified">Testified</option>
              </Form.Select>
            </Form.Group>
          </Modal.Body>
          <Modal.Footer>
            <Button variant="secondary" onClick={() => { setShowWitnessModal(false); setEditingWitness(null); }}>Cancel</Button>
            <Button variant="primary" type="submit" disabled={loading}>{loading ? <Spinner animation="border" size="sm" className="me-2" /> : null}{editingWitness ? 'Save Changes' : 'Add Witness'}</Button>
          </Modal.Footer>
        </Form>
      </Modal>

      {/* Witness View Modal */}
      <Modal show={showWitnessViewModal} onHide={() => setShowWitnessViewModal(false)} centered>
        <Modal.Header closeButton>
          <Modal.Title>Witness Details</Modal.Title>
        </Modal.Header>
        <Modal.Body>
          {viewingWitness && (
            <div>
              <div className="mb-3">
                <h6>Name</h6>
                <p>{viewingWitness.name}</p>
              </div>
              <div className="mb-3">
                <h6>Case</h6>
                <p>{viewingWitness.caseTitle}</p>
              </div>
              <div className="mb-3">
                <h6>Contact</h6>
                <p>{viewingWitness.contact}</p>
              </div>
              <div>
                <h6>Status</h6>
                <p>{viewingWitness.status}</p>
              </div>
            </div>
          )}
        </Modal.Body>
        <Modal.Footer>
          <Button variant="secondary" onClick={() => setShowWitnessViewModal(false)}>Close</Button>
        </Modal.Footer>
      </Modal>

      {/* Appeal Decision Modal */}
      <Modal show={showDecisionModal} onHide={handleCloseDecisionModal} centered>
        <Modal.Header closeButton>
          <Modal.Title>Update Appeal Decision</Modal.Title>
        </Modal.Header>
        <Form onSubmit={handleDecisionSubmit}>
          <Modal.Body>
            <Form.Group className="mb-3">
              <Form.Label>Status</Form.Label>
              <Form.Select name="status" value={decisionForm.status} onChange={handleDecisionFormChange} required>
                <option value="">Select status</option>
                <option value="Under Review">Under Review</option>
                <option value="Hearing Scheduled">Hearing Scheduled</option>
                <option value="Decided">Decided</option>
              </Form.Select>
            </Form.Group>
            <Form.Group className="mb-3">
              <Form.Label>Decision Date</Form.Label>
              <Form.Control type="date" name="decisionDate" value={decisionForm.decisionDate} onChange={handleDecisionFormChange} required />
            </Form.Group>
            <Form.Group className="mb-3">
              <Form.Label>Decision</Form.Label>
              <Form.Control as="textarea" name="decision" value={decisionForm.decision} onChange={handleDecisionFormChange} required />
            </Form.Group>
          </Modal.Body>
          <Modal.Footer>
            <Button variant="secondary" onClick={handleCloseDecisionModal}>Cancel</Button>
            <Button variant="primary" type="submit">Save</Button>
          </Modal.Footer>
        </Form>
      </Modal>

      {/* Payment Create Modal */}
      <Modal show={showPaymentModal} onHide={() => setShowPaymentModal(false)} centered>
        <Modal.Header closeButton>
          <Modal.Title>Create Payment Request</Modal.Title>
        </Modal.Header>
        <Form onSubmit={handleSubmitPayment}>
          <Modal.Body>
            {paymentSubmitError && (
              <div className="alert alert-danger py-2">{paymentSubmitError}</div>
            )}
            <div className="text-muted small mb-3">
              The assigned lawyer will be notified to confirm payment via the lawyer dashboard.
            </div>
            <Form.Group className="mb-3">
              <Form.Label className="fw-semibold">Case</Form.Label>
              <Form.Select
                value={paymentForm.caseid}
                onChange={(e) => setPaymentForm(prev => ({ ...prev, caseid: e.target.value }))}
                required
              >
                <option value="">— Select a case —</option>
                {courtCases.map(c => (
                  <option key={c.caseid || c.id} value={c.caseid || c.id}>
                    {c.title}
                  </option>
                ))}
              </Form.Select>
            </Form.Group>
            <Form.Group className="mb-3">
              <Form.Label className="fw-semibold">Purpose</Form.Label>
              <Form.Control
                type="text"
                placeholder="e.g. Court Fee, Filing Fee, Fine..."
                value={paymentForm.purpose}
                onChange={(e) => setPaymentForm(prev => ({ ...prev, purpose: e.target.value }))}
                required
              />
            </Form.Group>
            <Form.Group className="mb-3">
              <Form.Label className="fw-semibold">Amount (PKR)</Form.Label>
              <Form.Control
                type="number"
                placeholder="Enter amount"
                value={paymentForm.balance}
                onChange={(e) => setPaymentForm(prev => ({ ...prev, balance: e.target.value }))}
                required
                min="1"
                step="0.01"
              />
            </Form.Group>
            <Form.Group className="mb-3">
              <Form.Label className="fw-semibold">Payment Type</Form.Label>
              <Form.Select
                value={paymentForm.paymenttype}
                onChange={(e) => setPaymentForm(prev => ({ ...prev, paymenttype: e.target.value }))}
              >
                <option value="Court Fee">Court Fee</option>
                <option value="Filing Fee">Filing Fee</option>
                <option value="Fine">Fine</option>
                <option value="Bail">Bail</option>
                <option value="Other">Other</option>
              </Form.Select>
            </Form.Group>
          </Modal.Body>
          <Modal.Footer>
            <Button variant="secondary" onClick={() => setShowPaymentModal(false)}>Cancel</Button>
            <Button variant="primary" type="submit" disabled={paymentSubmitting}>
              {paymentSubmitting ? <Spinner size="sm" animation="border" /> : 'Send to Lawyer'}
            </Button>
          </Modal.Footer>
        </Form>
      </Modal>

      {/* Payment Delete Confirmation Modal */}
      <Modal show={confirm.show} onHide={() => setConfirm({ show: false, type: '', payload: null })} centered>
        <Modal.Header closeButton>
          <Modal.Title>Confirm Delete</Modal.Title>
        </Modal.Header>
        <Modal.Body>
          Are you sure you want to delete this payment record?
        </Modal.Body>
        <Modal.Footer>
          <Button variant="secondary" onClick={() => setConfirm({ show: false, type: '', payload: null })}>Cancel</Button>
          <Button variant="danger" onClick={() => {
            setCourtPayments(prev => prev.filter(p => p.id !== confirm.payload.id));
            setConfirm({ show: false, type: '', payload: null });
          }}>Delete</Button>
        </Modal.Footer>
      </Modal>

      {/* Prosecutor Add/Edit Modal */}
      <Modal show={showProsecutorModal} onHide={() => setShowProsecutorModal(false)} centered>
        <Modal.Header closeButton>
          <Modal.Title>{editingProsecutor ? 'Edit Prosecutor' : 'Add New Prosecutor'}</Modal.Title>
        </Modal.Header>
        <Form onSubmit={handleProsecutorSubmit}>
          <Modal.Body>
            <Form.Group className="mb-3">
              <Form.Label>Name</Form.Label>
              <Form.Control
                type="text"
                name="name"
                value={prosecutorForm.name}
                onChange={handleProsecutorFormChange}
                required
              />
            </Form.Group>
            <Form.Group className="mb-3">
              <Form.Label>Experience (years)</Form.Label>
              <Form.Control
                type="number"
                name="experience"
                value={prosecutorForm.experience}
                onChange={handleProsecutorFormChange}
                required
                min="0"
              />
            </Form.Group>
            <Form.Group className="mb-3">
              <Form.Label>Status</Form.Label>
              <Form.Select
                name="status"
                value={prosecutorForm.status}
                onChange={handleProsecutorFormChange}
                required
              >
                <option value="Active">Active</option>
                <option value="Inactive">Inactive</option>
              </Form.Select>
            </Form.Group>
            <Form.Group className="mb-3">
              <Form.Label>Assign Cases</Form.Label>
              <Form.Select
                multiple
                name="assignedCases"
                value={prosecutorForm.assignedCases}
                onChange={e => {
                  const selectedOptions = Array.from(e.target.selectedOptions, option => option.value);
                  setProsecutorForm({ ...prosecutorForm, assignedCases: selectedOptions });
                }}
              >
                {cases.map(case_ => (
                  <option key={case_.id} value={case_.title}>
                    {case_.title}
                  </option>
                ))}
              </Form.Select>
              <Form.Text className="text-muted">
                Hold Ctrl/Cmd to select multiple cases
              </Form.Text>
            </Form.Group>
          </Modal.Body>
          <Modal.Footer>
            <Button variant="secondary" onClick={() => setShowProsecutorModal(false)}>
              Cancel
            </Button>
            <Button variant="primary" type="submit">
              {editingProsecutor ? 'Save Changes' : 'Add Prosecutor'}
            </Button>
          </Modal.Footer>
        </Form>
      </Modal>

      {/* Judge Add/Edit Modal */}
      <Modal show={showJudgeModal} onHide={() => setShowJudgeModal(false)} centered>
        <Modal.Header closeButton>
          <Modal.Title>{editingJudge ? 'Edit Judge' : 'Add New Judge'}</Modal.Title>
        </Modal.Header>
        <Form onSubmit={handleJudgeSubmit}>
          <Modal.Body>
            <Form.Group className="mb-3">
              <Form.Label>Name</Form.Label>
              <Form.Control
                type="text"
                name="name"
                value={judgeForm.name}
                onChange={handleJudgeFormChange}
                required
              />
            </Form.Group>
            <Form.Group className="mb-3">
              <Form.Label>Position</Form.Label>
              <Form.Control
                type="text"
                name="position"
                value={judgeForm.position}
                onChange={handleJudgeFormChange}
                required
              />
            </Form.Group>
            <Form.Group className="mb-3">
              <Form.Label>Experience (years)</Form.Label>
              <Form.Control
                type="number"
                name="experience"
                value={judgeForm.experience}
                onChange={handleJudgeFormChange}
                required
                min="0"
              />
            </Form.Group>
            <Form.Group className="mb-3">
              <Form.Label>Appointment Date</Form.Label>
              <Form.Control
                type="date"
                name="appointmentDate"
                value={judgeForm.appointmentDate}
                onChange={handleJudgeFormChange}
                required
              />
            </Form.Group>
            <Form.Group className="mb-3">
              <Form.Label>Specialization</Form.Label>
              <Form.Control
                type="text"
                name="specialization"
                value={judgeForm.specialization}
                onChange={handleJudgeFormChange}
                required
              />
            </Form.Group>
            <Form.Group className="mb-3">
              <Form.Label>Assign Cases</Form.Label>
              <Form.Select
                multiple
                name="assignedCases"
                value={judgeForm.assignedCases}
                onChange={e => {
                  const selectedOptions = Array.from(e.target.selectedOptions, option => option.value);
                  setJudgeForm({ ...judgeForm, assignedCases: selectedOptions });
                }}
              >
                {courtCases.map(case_ => (
                  <option key={case_.id} value={case_.title}>
                    {case_.title}
                  </option>
                ))}
              </Form.Select>
              <Form.Text className="text-muted">
                Hold Ctrl/Cmd to select multiple cases
              </Form.Text>
            </Form.Group>
          </Modal.Body>
          <Modal.Footer>
            <Button variant="secondary" onClick={() => setShowJudgeModal(false)}>
              Cancel
            </Button>
            <Button variant="primary" type="submit">
              {editingJudge ? 'Save Changes' : 'Add Judge'}
            </Button>
          </Modal.Footer>
        </Form>
      </Modal>

      {/* Remand Add/Edit Modal */}
      <Modal show={showRemandModal} onHide={() => setShowRemandModal(false)} centered>
        <Modal.Header closeButton>
          <Modal.Title>{editingRemand ? 'Edit Remand' : 'Add New Remand'}</Modal.Title>
        </Modal.Header>
        <Form onSubmit={handleRemandSubmit}>
          <Modal.Body>
            <Form.Group className="mb-3">
              <Form.Label>Case Name</Form.Label>
              <Form.Control
                type="text"
                name="caseName"
                value={remandForm.caseName}
                onChange={handleRemandFormChange}
                required
              />
            </Form.Group>
            <Form.Group className="mb-3">
              <Form.Label>Lawyer Name</Form.Label>
              <Form.Control
                type="text"
                name="lawyerName"
                value={remandForm.lawyerName}
                onChange={handleRemandFormChange}
                required
              />
            </Form.Group>
            <Form.Group className="mb-3">
              <Form.Label>Client Name</Form.Label>
              <Form.Control
                type="text"
                name="clientName"
                value={remandForm.clientName}
                onChange={handleRemandFormChange}
                required
              />
            </Form.Group>
            <Form.Group className="mb-3">
              <Form.Label>Remand Type</Form.Label>
              <Form.Control
                type="text"
                name="remandType"
                value={remandForm.remandType}
                onChange={handleRemandFormChange}
                required
              />
            </Form.Group>
            <Form.Group className="mb-3">
              <Form.Label>Remand Date</Form.Label>
              <Form.Control
                type="date"
                name="remandDate"
                value={remandForm.remandDate}
                onChange={handleRemandFormChange}
                required
              />
            </Form.Group>
            <Form.Group className="mb-3">
              <Form.Label>Remand Reason</Form.Label>
              <Form.Control
                type="text"
                name="remandReason"
                value={remandForm.remandReason}
                onChange={handleRemandFormChange}
                required
              />
            </Form.Group>
            <Form.Group className="mb-3">
              <Form.Label>Status</Form.Label>
              <Form.Control
                type="text"
                name="status"
                value={remandForm.status}
                onChange={handleRemandFormChange}
                required
              />
            </Form.Group>
            <Form.Group className="mb-3">
              <Form.Label>Duration</Form.Label>
              <Form.Control
                type="text"
                name="duration"
                value={remandForm.duration}
                onChange={handleRemandFormChange}
                required
              />
            </Form.Group>
          </Modal.Body>
          <Modal.Footer>
            <Button variant="secondary" onClick={() => setShowRemandModal(false)}>
              Cancel
            </Button>
            <Button variant="primary" type="submit">
              {editingRemand ? 'Save Changes' : 'Add Remand'}
            </Button>
          </Modal.Footer>
        </Form>
      </Modal>
      {/* Verify Case Modal */}
      <Modal show={showVerifyModal} onHide={() => setShowVerifyModal(false)} centered>
  <Modal.Header closeButton>
    <Modal.Title>Verify Case</Modal.Title>
  </Modal.Header>
  <Form onSubmit={handleVerifySubmit}>
    <Modal.Body>
      {verifyError && <div className="alert alert-danger">{verifyError}</div>}
      {verifySuccess && <div className="alert alert-success">{verifySuccess}</div>}
      <Form.Group className="mb-3">
        <Form.Label>Case Name</Form.Label>
        <Form.Control
          type="text"
          name="casename"
          value={verifyForm.casename}
          readOnly
          disabled
        />
      </Form.Group>
      <Form.Group className="mb-3">
        <Form.Label>Type</Form.Label>
        <Form.Control
          type="text"
          name="type"
          value={verifyForm.type}
          readOnly
          disabled
        />
      </Form.Group>
      <Form.Group className="mb-3">
        <Form.Label>Filing Date</Form.Label>
        <Form.Control
          type="date"
          name="filingdate"
          value={verifyForm.filingdate}
          readOnly
          disabled
        />
      </Form.Group>
      <Form.Group className="mb-3">
        <Form.Label>Client Name</Form.Label>
        <Form.Control
          type="text"
          name="clientname"
          value={verifyForm.clientname}
          onChange={handleVerifyFormChange}
          required
        />
      </Form.Group>
      <p className="text-muted small mb-3">
        A court case number will be assigned automatically when you verify this case.
      </p>
      <Form.Group className="mb-3">
        <Form.Label>Lawyer Name</Form.Label>
        <Form.Control
          type="text"
          name="lawyername"
          value={verifyForm.lawyername}
          onChange={handleVerifyFormChange}
          required
        />
      </Form.Group>
      <Form.Group className="mb-3">
        <Form.Label>Judge</Form.Label>
        <Form.Select
          name="judgename"
          value={verifyForm.judgename}
          onChange={handleVerifyFormChange}
          required
        >
          <option value="">Select judge</option>
          {judgeOptions.map(j => (
            <option key={j.judgeid} value={j.name}>{j.name}</option>
          ))}
        </Form.Select>
      </Form.Group>
      <Form.Group className="mb-3">
        <Form.Label>Prosecutor</Form.Label>
        <Form.Select
          name="prosecutorname"
          value={verifyForm.prosecutorname}
          onChange={handleVerifyFormChange}
        >
          <option value="">Select prosecutor (optional)</option>
          {prosecutorOptions.map(p => (
            <option key={p.id} value={p.name}>{p.name}</option>
          ))}
        </Form.Select>
      </Form.Group>
      <Form.Group className="mb-3">
        <Form.Label>Opposing Lawyer</Form.Label>
        <Form.Select
          name="respondentLawyer"
          value={respondentLawyerId}
          onChange={e => setRespondentLawyerId(e.target.value)}
        >
          <option value="">Select opposing lawyer (optional)</option>
          {lawyerOptions.map(l => (
            <option key={l.lawyerid || l.id} value={l.lawyerid || l.id}>{`${l.firstname || l.name || ''} ${l.lastname || ''}`.trim()}</option>
          ))}
        </Form.Select>
      </Form.Group>
    </Modal.Body>
    <Modal.Footer>
      <Button variant="secondary" onClick={() => setShowVerifyModal(false)}>
        Cancel
      </Button>
      <Button variant="primary" type="submit" disabled={verifyLoading}>
        {verifyLoading ? 'Verifying...' : 'Verify'}
      </Button>
    </Modal.Footer>
  </Form>
</Modal>
    </div>
  );
};

export default RegistrarDashboard; 