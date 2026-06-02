import React, { useState, useEffect } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { Form, Button, Alert, Spinner } from 'react-bootstrap';
import '../styles/Signup.css';
import legalLoginImage from '../assets/legal-login.png';
import CourtRegistrationForm from '../components/CourtRegistrationForm';

const roleFieldMap = {
  'Client': [
    { name: 'address', label: 'Address', type: 'text', placeholder: '123 Main St, City', required: true }
  ],
  'Case Participant': [
    { name: 'address', label: 'Address', type: 'text', placeholder: '123 Main St, City', required: true }
  ],
  'CourtRegistrar': [
    { name: 'position', label: 'Position', type: 'text', placeholder: 'Registrar Position', required: true }
  ],
  'Lawyer': [
    { name: 'barLicense', label: 'Bar License No', type: 'number', placeholder: '123456', required: true },
    { name: 'experience', label: 'Experience (years)', type: 'number', placeholder: '5', required: true },
    { name: 'specialization', label: 'Specialization', type: 'text', placeholder: 'e.g. Civil Law', required: true }
  ],
  'Judge': [
    { name: 'position', label: 'Position', type: 'text', placeholder: 'Judge Position', required: true },
    { name: 'specialization', label: 'Specialization', type: 'text', placeholder: 'e.g. Criminal Law', required: true },
    { name: 'experience', label: 'Experience (years)', type: 'number', placeholder: '10', required: true }
  ]
};

const getRoleFields = (role) => {
  if (role === 'Client') return roleFieldMap['Case Participant'];
  return roleFieldMap[role] || [];
};

const CompleteProfile = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const role = location.state?.role || 'Client';
  const [form, setForm] = useState({});
  const [error, setError] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [step, setStep] = useState(0);

  const fields = getRoleFields(role);

  const steps = [
    {
      label: 'Basic Info',
      content: (
        <div className="mb-3">
          <p><b>Role:</b> {role}</p>
          <p className="text-muted">Please complete your profile to continue.</p>
        </div>
      )
    },
    {
      label: 'Additional Info',
      fields: fields
    }
  ];

  const handleChange = (e) => {
    setForm({ ...form, [e.target.name]: e.target.value });
  };

  const validateStep = () => {
    setError(null);
    if (step === 1) {
      for (const field of fields) {
        const value = form[field.name];
        if (field.required && (!value || value.trim() === '')) {
          setError(`${field.label} is required.`);
          return false;
        }
      }
    }
    return true;
  };

  const handleNext = (e) => {
    e.preventDefault();
    if (validateStep()) {
      setStep(step + 1);
    }
  };

  const handleBack = (e) => {
    e.preventDefault();
    setError(null);
    setStep(step - 1);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!validateStep()) return;
    setIsLoading(true);

    try {
      const userId = localStorage.getItem('user_id');
      if (!userId) {
        setError('Session expired. Please sign up or log in again.');
        setIsLoading(false);
        return;
      }

      const profileData = {
        ...form,
        user_id: Number(userId),
      };

      const response = await fetch('/api/complete-profile', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include',
        body: JSON.stringify(profileData)
      });

      const result = await response.json();

      if (!response.ok || !result.success) {
        throw new Error(result.message || 'Profile completion failed');
      }

      // Navigate based on role
      if (role === 'CourtRegistrar') {
        navigate('/register-court');
      } else if (role === 'Lawyer') {
        navigate('/dashboard');
      } else if (role === 'Client') {
        navigate('/ClientDashboard');
      } else if (role === 'Judge') {
        navigate('/JudgeDashboard');
      } else if (role === 'Admin') {
        navigate('/AdminDashboard');
      } else {
        navigate('/dashboard');
      }
    } catch (err) {
      setError(err.message || 'Profile completion failed. Please try again.');
      console.error('Error:', err);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="signup-bg" style={{ minHeight: '100vh', width: '100vw', display: 'flex', alignItems: 'center', justifyContent: 'center', overflow: 'auto' }}>
      <div className="signup-form-card" style={{ maxWidth: 370, width: '100%', padding: '1.2em 0.8em 1em 0.8em', margin: '2em 0' }}>
        <h2 className="gradient-text" style={{
          background: 'linear-gradient(90deg, #22304a 0%, #1ec6b6 100%)',
          WebkitBackgroundClip: 'text',
          WebkitTextFillColor: 'transparent',
          backgroundClip: 'text',
          textFillColor: 'transparent',
          marginBottom: '0.5rem',
          fontSize: '1.5rem',
        }}>Complete Your Profile</h2>
        <p className="text-muted">Just one more step to get started!</p>
        <div className="mb-3 w-100 d-flex justify-content-center align-items-center gap-2">
          {steps.map((s, idx) => (
            <div key={s.label} style={{width: 18, height: 18, borderRadius: '50%', background: idx === step ? '#1ec6b6' : '#e0e7ef', border: '2px solid #1ec6b6', display: 'inline-block', transition: 'all 0.3s ease'}}></div>
          ))}
        </div>
        <h5 className="mb-3" style={{ color: '#22304a', fontWeight: 700 }}>{steps[step].label}</h5>
        {error && (
          <Alert variant="danger" onClose={() => setError(null)} dismissible>
            {error}
          </Alert>
        )}
        <Form onSubmit={step === steps.length - 1 ? handleSubmit : handleNext} style={{width: '100%'}}>
          {step === 0 && steps[0].content}
          {step === 1 && fields.map(field => (
            <Form.Group className="mb-3" key={field.name}>
              <Form.Label>{field.label} {field.required && <span style={{color: 'red'}}>*</span>}</Form.Label>
              <Form.Control
                type={field.type}
                placeholder={field.placeholder}
                name={field.name}
                value={form[field.name] || ''}
                onChange={handleChange}
                required={field.required}
                aria-required={field.required}
              />
            </Form.Group>
          ))}
          <div className="d-flex gap-3 mt-3" style={{ justifyContent: 'stretch' }}>
            {step > 0 && (
              <Button
                variant="outline-secondary"
                onClick={handleBack}
                className="flex-grow-1"
                style={{
                  borderRadius: '0.75rem',
                  padding: '0.75rem',
                  fontWeight: '600',
                  borderColor: '#1ec6b6',
                  color: '#1ec6b6',
                  minWidth: 0
                }}
                disabled={isLoading}
                type="button"
              >Back</Button>
            )}
            {step < steps.length - 1 ? (
              <Button
                type="submit"
                className="flex-grow-1"
                disabled={isLoading}
                style={{
                  background: 'linear-gradient(90deg, #22304a 0%, #1ec6b6 100%)',
                  border: 'none',
                  borderRadius: '0.75rem',
                  padding: '0.75rem',
                  fontWeight: '600',
                  boxShadow: '0 4px 12px rgba(30,198,182,0.15)',
                  minWidth: 0
                }}
              >Next</Button>
            ) : (
              <Button
                type="submit"
                className="flex-grow-1"
                disabled={isLoading}
                style={{
                  background: 'linear-gradient(90deg, #22304a 0%, #1ec6b6 100%)',
                  border: 'none',
                  borderRadius: '0.75rem',
                  padding: '0.75rem',
                  fontWeight: '600',
                  boxShadow: '0 4px 12px rgba(30,198,182,0.15)',
                  minWidth: 0
                }}
              >
                {isLoading ? (
                  <><Spinner animation="border" size="sm" className="me-2" /> Completing...</>
                ) : (
                  'Complete Profile'
                )}
              </Button>
            )}
          </div>
        </Form>
      </div>
    </div>
  );
};

export default CompleteProfile;