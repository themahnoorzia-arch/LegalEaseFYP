import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import {
  Form,
  Button,
  Alert,
  Spinner
} from 'react-bootstrap';
import '../styles/login.css';
import legalLoginImage from '../assets/legal-login.png';
import { Eye, EyeOff } from 'lucide-react';

// Mock credentials for lawyer and registrar
const MOCK_LAWYER = {
  email: 'lawyer@example.com',
  password: 'password123',
};
const MOCK_COURTREGISTRAR = {
  email: 'registrar@example.com',
  password: 'registrar123',
};

// Add mock admin credentials
const MOCK_ADMIN = {
  email: 'admin@legalease.com',
  password: 'admin123',
};

// Add mock judge credentials
const MOCK_JUDGE = {
  email: 'judge@example.com',
  password: 'judge123',
};

// Add mock client credentials
const MOCK_CLIENT = {
  email: 'client@example.com',
  password: 'client123',
};

const Login = () => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [userType, setUserType] = useState('lawyer');
  const [error, setError] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const [unverifiedEmail, setUnverifiedEmail] = useState(null);
  const [resendStatus, setResendStatus] = useState(null);
  const navigate = useNavigate();

  const isEmailValid = (email) => /\S+@\S+\.\S+/.test(email);

 const handleSubmit = async (event) => {
  event.preventDefault();
  setError(null);

  if (!email || !isEmailValid(email)) {
    setError('Please enter a valid email address.');
    return;
  }
  if (!password) {
    setError('Password is required.');
    return;
  }

  setIsLoading(true);

  const isMockClient =
    userType === 'Client' &&
    email === MOCK_CLIENT.email &&
    password === MOCK_CLIENT.password;

  const isMockLawyer =
    userType === 'lawyer' &&
    email === MOCK_LAWYER.email &&
    password === MOCK_LAWYER.password;

  const isMockCourtRegistrar =
    userType === 'CourtRegistrar' &&
    email === MOCK_COURTREGISTRAR.email &&
    password === MOCK_COURTREGISTRAR.password;

  const isMockAdmin =
    userType === 'Admin' &&
    email === MOCK_ADMIN.email &&
    password === MOCK_ADMIN.password;

  const isMockJudge =
    userType === 'Judge' &&
    email === MOCK_JUDGE.email &&
    password === MOCK_JUDGE.password;

  try {
    const response = await fetch('/api/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password, userType }),
      credentials: 'include',
    });

    const result = await response.json();

    if (response.ok && result.success) {
      const { role } = result;
      localStorage.setItem('userRole', role);
      localStorage.setItem('email', result.email);
      if (result.user_id) {
        localStorage.setItem('user_id', String(result.user_id));
      }

      if (role === 'Lawyer') {
        navigate('/dashboard');
      } else if (role === 'CourtRegistrar') {
        navigate('/RegistrarDashboard');
      } else if (role === 'Admin') {
        navigate('/AdminDashboard');
      } else if (role === 'Judge') {
        navigate('/JudgeDashboard');
      } else if (role === 'Client') {
        navigate('/ClientDashboard');
      } else {
        setError('Unknown role.');
      }
    } else if (response.status === 403 && result.email_not_verified) {
      setUnverifiedEmail(result.email || email);
      setError(null);
    } else if (isMockLawyer || isMockCourtRegistrar || isMockAdmin || isMockJudge || isMockClient) {
      // Fallback to mock credentials if API fails
      let role;
      if (isMockLawyer) role = 'Lawyer';
      else if (isMockCourtRegistrar) role = 'CourtRegistrar';
      else if (isMockAdmin) role = 'Admin';
      else if (isMockJudge) role = 'Judge';
      else if (isMockClient) role = 'Client';
      localStorage.setItem('userRole', role);
      localStorage.setItem('email', email);
      
      if (role === 'Lawyer') navigate('/dashboard');
      else if (role === 'CourtRegistrar') navigate('/RegistrarDashboard');
      else if (role === 'Admin') navigate('/AdminDashboard');
      else if (role === 'Judge') navigate('/JudgeDashboard');
      else if (role === 'Client') navigate('/ClientDashboard');
    } else {
      setError(result.message || 'Invalid email or password.');
    }
  } catch (err) {
    // Network/API down → check mock credentials
    if (isMockLawyer || isMockCourtRegistrar || isMockAdmin || isMockJudge || isMockClient) {
      let role;
      if (isMockLawyer) role = 'Lawyer';
      else if (isMockCourtRegistrar) role = 'CourtRegistrar';
      else if (isMockAdmin) role = 'Admin';
      else if (isMockJudge) role = 'Judge';
      else if (isMockClient) role = 'Client';
      localStorage.setItem('userRole', role);
      localStorage.setItem('email', email);
      
      if (role === 'Lawyer') navigate('/dashboard');
      else if (role === 'CourtRegistrar') navigate('/RegistrarDashboard');
      else if (role === 'Admin') navigate('/AdminDashboard');
      else if (role === 'Judge') navigate('/JudgeDashboard');
      else if (role === 'Client') navigate('/ClientDashboard');
    } else {
      setError('Login failed. Please try again later.');
    }
  } finally {
    setIsLoading(false);
  }
};

  const handleResend = async () => {
    setResendStatus('sending');
    try {
      const res = await fetch('/api/resend-verification', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email: unverifiedEmail }),
      });
      const data = await res.json();
      setResendStatus(data.success ? 'sent' : 'error');
    } catch {
      setResendStatus('error');
    }
  };

  return (
    <div style={{
      minHeight: '100vh',
      width: '100vw',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      overflow: 'hidden',
      position: 'relative',
    }}>
      {/* Blurred background image with overlay */}
      <div style={{
        position: 'fixed',
        top: 0,
        left: 0,
        width: '100vw',
        height: '100vh',
        zIndex: 0,
        background: `url(${legalLoginImage}) center center/cover no-repeat`,
        filter: 'blur(4px) brightness(0.8)',
      }} />
      <div style={{
        position: 'fixed',
        top: 0,
        left: 0,
        width: '100vw',
        height: '100vh',
        zIndex: 1,
        background: 'linear-gradient(120deg, rgba(34,48,74,0.45) 0%, rgba(30,198,182,0.18) 100%)',
      }} />
      {/* Login Card */}
      <div className="signup-form-card" style={{
        maxWidth: 340,
        width: '100%',
        minHeight: 'auto',
        maxHeight: '95vh',
        padding: '0.8em 0.7em 0.8em 0.7em',
        margin: '1em 0',
        boxShadow: '0 8px 32px 0 rgba(31,38,135,0.18)',
        borderRadius: '1.2rem',
        background: 'white',
        border: '1px solid rgba(255,255,255,0.18)',
        zIndex: 2,
        position: 'relative',
        display: 'flex',
        flexDirection: 'column',
        justifyContent: 'center',
        overflow: 'auto',
      }}>
        <h2 className="gradient-text" style={{
          background: 'linear-gradient(90deg, #22304a 0%, #1ec6b6 100%)',
          WebkitBackgroundClip: 'text',
          WebkitTextFillColor: 'transparent',
          backgroundClip: 'text',
          textFillColor: 'transparent',
          marginBottom: '0.5rem',
          fontSize: '1.5rem',
        }}>Welcome Back</h2>
        <p className="text-muted mb-2" style={{ fontSize: '0.95rem' }}>Log in to your LegalEase account.</p>
        {error && (
          <Alert variant="danger" onClose={() => setError(null)} dismissible style={{ borderRadius: '0.75rem', fontSize: '0.95rem', marginBottom: '0.5rem' }}>
            {error}
          </Alert>
        )}
        {unverifiedEmail && (
          <Alert variant="warning" onClose={() => { setUnverifiedEmail(null); setResendStatus(null); }} dismissible style={{ borderRadius: '0.75rem', fontSize: '0.94rem', marginBottom: '0.5rem' }}>
            <div className="fw-semibold mb-1">Email not verified</div>
            <div style={{ fontSize: 13 }}>Please check your inbox at <strong>{unverifiedEmail}</strong> and click the verification link.</div>
            <div className="mt-2">
              {resendStatus === 'sent' ? (
                <span style={{ color: '#15803d', fontWeight: 600 }}>✓ New link sent! Check your inbox.</span>
              ) : resendStatus === 'error' ? (
                <span style={{ color: '#dc2626' }}>Failed to send. Try again later.</span>
              ) : (
                <button
                  className="btn btn-sm btn-outline-warning"
                  onClick={handleResend}
                  disabled={resendStatus === 'sending'}
                  style={{ fontSize: 13 }}
                >
                  {resendStatus === 'sending' ? 'Sending…' : 'Resend verification email'}
                </button>
              )}
            </div>
          </Alert>
        )}
        <Form onSubmit={handleSubmit} style={{width: '100%'}}>
          <Form.Group className="mb-2">
            <Form.Label className="fw-bold" style={{ fontSize: '0.97rem', marginBottom: 2 }}>Email address</Form.Label>
              <Form.Control
                type="email"
                placeholder="you@example.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
              style={{ 
                borderRadius: '0.75rem',
                padding: '0.45rem 0.7rem',
                border: '1px solid rgba(30,198,182,0.2)',
                fontSize: '0.97rem',
                marginBottom: 2
              }}
              />
            </Form.Group>
          <Form.Group className="mb-2">
            <Form.Label className="fw-bold" style={{ fontSize: '0.97rem', marginBottom: 2 }}>Password</Form.Label>
              <div style={{ position: 'relative' }}>
                <Form.Control
                  type={showPassword ? 'text' : 'password'}
                  placeholder="Enter your password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                style={{ 
                  borderRadius: '0.75rem',
                  padding: '0.45rem 0.7rem',
                  border: '1px solid rgba(30,198,182,0.2)',
                  fontSize: '0.97rem',
                  marginBottom: 2
                }}
                />
              <Button
                variant="link"
                className="position-absolute end-0 top-50 translate-middle-y"
                onClick={() => setShowPassword(!showPassword)}
                style={{ color: '#1ec6b6', padding: 0, minWidth: 0 }}
                >
                {showPassword ? <EyeOff size={18} /> : <Eye size={18} />}
              </Button>
              </div>
            </Form.Group>
          <Button
            type="submit"
            className="w-100 mb-2"
            disabled={isLoading}
            style={{
              background: 'linear-gradient(90deg, #22304a 0%, #1ec6b6 100%)',
              border: 'none',
              borderRadius: '0.75rem',
              padding: '0.55rem',
              fontWeight: '600',
              fontSize: '1.05rem',
              boxShadow: '0 4px 12px rgba(30,198,182,0.15)'
            }}
          >
              {isLoading ? (
              <Spinner as="span" animation="border" size="sm" role="status" aria-hidden="true" />
              ) : (
                'Log In'
              )}
            </Button>
          <div className="text-center" style={{ fontSize: '0.95rem', marginTop: 2 }}>
            <p className="mb-1">
              <Link to="/forgot-password" style={{ color: '#6b7280', textDecoration: 'none', fontSize: '0.9rem' }}>
                Forgot password?
              </Link>
            </p>
            <p className="mb-0">
              Don't have an account?{' '}
              <Link to="/signup" style={{ color: '#1ec6b6', textDecoration: 'none', fontWeight: '600' }}>
                Sign up
              </Link>
            </p>
          </div>
          </Form>
        <style>{`
          .btn-primary, .btn-outline-primary, .btn-outline-secondary, .custom-radio input[type='radio']:checked + label {
            background: #1ec6b6 !important;
            border-color: #1ec6b6 !important;
            color: #fff !important;
          }
          .btn-primary:hover, .btn-outline-primary:hover, .btn-outline-secondary:hover {
            background: #159e8c !important;
            border-color: #159e8c !important;
            color: #fff !important;
          }
          .form-check-input:checked {
            background-color: #1ec6b6 !important;
            border-color: #1ec6b6 !important;
          }
        `}</style>
      </div>
    </div>
  );
};

export default Login;
