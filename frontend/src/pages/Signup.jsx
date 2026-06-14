import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import {
  Form,
  Button,
  Alert,
  Spinner
} from 'react-bootstrap';
import '../styles/Signup.css'; // We will add custom CSS here
import legalSignupImage from '../assets/legal-signup.png'; // Background image
import legalLoginImage from '../assets/legal-login.png'; // Use as logo at the top
import { Eye, EyeOff } from 'lucide-react';

const roles = [
  'Client',
  'CourtRegistrar',
  'Lawyer',
  'Judge',
  'Admin'
];

const steps = [
  {
    label: 'Personal Info',
    fields: [
      { name: 'firstname', label: 'First Name', type: 'text', placeholder: 'Jane', required: true },
      { name: 'lastname', label: 'Last Name', type: 'text', placeholder: 'Doe', required: true },
      { name: 'dob', label: 'Date of Birth', type: 'date', required: true }
    ]
  },
  {
    label: 'Contact Info',
    fields: [
      { name: 'email', label: 'Email address', type: 'email', placeholder: 'you@example.com', required: true },
      { name: 'phoneno', label: 'Phone Number', type: 'tel', placeholder: '123-456-7890', required: true },
      { name: 'cnic', label: 'CNIC', type: 'text', placeholder: '12345-1234567-1', required: true }
    ]
  },
  {
    label: 'Account Info',
    fields: [
      { name: 'password', label: 'Password', type: 'password', placeholder: 'Minimum 8 characters', required: true },
      { name: 'role', label: 'Role', type: 'select', options: roles, required: true }
    ]
  }
];

const Signup = () => {
  const [form, setForm] = useState({
    firstname: '',
    lastname: '',
    password: '',
    email: '',
    role: '',
    phoneno: '',
    cnic: '',
    dob: ''
  });
  const [error, setError] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [step, setStep] = useState(0);
  const [emailSent, setEmailSent] = useState(false);
  const [registeredEmail, setRegisteredEmail] = useState('');
  const navigate = useNavigate();
  const [showPassword, setShowPassword] = useState(false);

  const isEmailValid = (email) => /\S+@\S+\.\S+/.test(email);
  const isPasswordStrong = (password) => password.length >= 8;

  const handleChange = (e) => {
    setForm({ ...form, [e.target.name]: e.target.value });
  };

  const validateStep = () => {
    setError(null);
    for (const field of steps[step].fields) {
      const value = form[field.name];
      if (field.required && (!value || value.trim() === '')) {
        setError(`${field.label} is required.`);
        return false;
      }
      if (field.name === 'email' && value && !isEmailValid(value)) {
        setError('Please enter a valid email address.');
        return false;
      }
      if (field.name === 'password' && value && !isPasswordStrong(value)) {
        setError('Password must be at least 8 characters long.');
        return false;
      }
      if (field.name === 'firstname' && value && value.trim().length < 2) {
        setError('First name must be at least 2 characters.');
        return false;
      }
      if (field.name === 'lastname' && value && value.trim().length < 2) {
        setError('Last name must be at least 2 characters.');
        return false;
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

  const handleSubmit = async (event) => {
    event.preventDefault();
    if (!validateStep()) return;
    setIsLoading(true);
    try {
      // API call to signup
      const response = await fetch('/api/signup', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include',
        body: JSON.stringify(form),
      });
      const data = await response.json();

      if (response.ok && data.success) {
        localStorage.setItem('userRole', form.role);
        localStorage.setItem('email', form.email);
        if (data.user_id) {
          localStorage.setItem('user_id', String(data.user_id));
        }
        if (form.role === 'CourtRegistrar') {
          localStorage.setItem('CourtRegistrarProfile', JSON.stringify({
            name: form.firstname + ' ' + form.lastname,
            email: form.email,
            phone: form.phoneno,
            cnic: form.cnic,
            dob: form.dob
          }));
        }
        // Go to OTP verification — profile only accessible after verifying
        navigate('/verify-otp', { state: { email: data.email || form.email, role: form.role } });
      } else {
        setError(data.message || 'Signup failed. Please try again later.');
      }
    } catch (apiError) {
      setError('Could not reach the server. Make sure the backend is running on port 5000.');
      console.error('Signup error:', apiError);
    } finally {
      setIsLoading(false);
    }
  };

  if (emailSent) {
    return (
      <div style={{
        minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center',
        background: 'linear-gradient(135deg, #22304a 0%, #1ec6b6 100%)',
      }}>
        <div style={{
          background: '#fff', borderRadius: 16, padding: '48px 40px', maxWidth: 440,
          width: '90%', textAlign: 'center', boxShadow: '0 8px 40px rgba(0,0,0,0.18)',
        }}>
          <div style={{ fontSize: 56, marginBottom: 16 }}>📧</div>
          <h2 style={{ color: '#22304a', fontWeight: 700, marginBottom: 12 }}>Check your email</h2>
          <p style={{ color: '#6b7280', fontSize: 15, marginBottom: 8 }}>
            We sent a verification link to:
          </p>
          <p style={{ color: '#22304a', fontWeight: 600, fontSize: 16, marginBottom: 20 }}>
            {registeredEmail}
          </p>
          <p style={{ color: '#6b7280', fontSize: 14 }}>
            Click the link in the email to activate your account. Redirecting you to complete your profile…
          </p>
        </div>
      </div>
    );
  }

  return (
    <div style={{
      minHeight: '100vh',
      width: '100vw',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      overflow: 'auto',
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
        background: `url(${legalSignupImage}) center center/cover no-repeat`,
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
      {/* Signup Card */}
      <div className="signup-form-card" style={{
        maxWidth: 370,
        width: '100%',
        padding: '1.2em 0.8em 1em 0.8em',
        margin: '2em 0',
        boxShadow: '0 8px 32px 0 rgba(31,38,135,0.18)',
        borderRadius: '1.5rem',
        background: 'white',
        border: '1px solid rgba(255,255,255,0.18)',
        zIndex: 2,
        position: 'relative',
      }}>
        <h2 className="gradient-text" style={{
          background: 'linear-gradient(90deg, #22304a 0%, #1ec6b6 100%)',
          WebkitBackgroundClip: 'text',
          WebkitTextFillColor: 'transparent',
          backgroundClip: 'text',
          textFillColor: 'transparent',
          marginBottom: '0.5rem'
        }}>Sign Up for LegalEase</h2>
        <p className="text-muted mb-4">Create your account to manage cases, clients, and more.</p>
        <div className="mb-4 w-100 d-flex justify-content-center align-items-center gap-2">
          {steps.map((s, idx) => (
            <div 
              key={s.label} 
              style={{
                width: 18, 
                height: 18, 
                borderRadius: '50%', 
                background: idx === step ? '#1ec6b6' : '#e0e7ef', 
                border: '2px solid #1ec6b6',
                display: 'inline-block',
                transition: 'all 0.3s ease'
              }}
            />
          ))}
        </div>
        <h5 className="mb-4 fw-bold" style={{ color: '#22304a' }}>{steps[step].label}</h5>
        {error && (
          <Alert variant="danger" onClose={() => setError(null)} dismissible style={{ borderRadius: '0.75rem' }}>
            {error}
          </Alert>
        )}
        <Form onSubmit={step === steps.length - 1 ? handleSubmit : handleNext} style={{ width: '100%' }}>
          {steps[step].fields.map(field => (
            <Form.Group className="mb-4" key={field.name}>
              <Form.Label className="fw-bold">{field.label} {field.required && <span style={{ color: '#1ec6b6' }}>*</span>}</Form.Label>
              {field.type === 'select' ? (
                <Form.Select
                  name={field.name}
                  value={form[field.name]}
                  onChange={handleChange}
                  required={field.required}
                  aria-required={field.required}
                  style={{ 
                    borderRadius: '0.75rem',
                    padding: '0.75rem 1rem',
                    border: '1px solid rgba(30,198,182,0.2)'
                  }}
                >
                  <option value="">Select {field.label}</option>
                  {field.options && field.options.map(opt => (
                    <option key={opt} value={opt}>{opt}</option>
                  ))}
                </Form.Select>
              ) : field.type === 'password' ? (
                <div style={{ position: 'relative' }}>
                  <Form.Control
                    type={showPassword ? 'text' : 'password'}
                    placeholder={field.placeholder}
                    name={field.name}
                    value={form[field.name]}
                    onChange={handleChange}
                    required={field.required}
                    aria-required={field.required}
                    style={{ 
                      borderRadius: '0.75rem',
                      padding: '0.75rem 1rem',
                      border: '1px solid rgba(30,198,182,0.2)'
                    }}
                  />
                  <Button
                    variant="link"
                    className="position-absolute end-0 top-50 translate-middle-y"
                    onClick={() => setShowPassword(!showPassword)}
                    style={{ color: '#1ec6b6' }}
                  >
                    {showPassword ? <EyeOff size={20} /> : <Eye size={20} />}
                  </Button>
                </div>
              ) : (
                <Form.Control
                  type={field.type}
                  placeholder={field.placeholder}
                  name={field.name}
                  value={form[field.name]}
                  onChange={handleChange}
                  required={field.required}
                  aria-required={field.required}
                  style={{ 
                    borderRadius: '0.75rem',
                    padding: '0.75rem 1rem',
                    border: '1px solid rgba(30,198,182,0.2)'
                  }}
                />
              )}
            </Form.Group>
          ))}
          <div className="d-flex gap-3">
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
                  color: '#1ec6b6'
                }}
              >
                Back
              </Button>
            )}
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
                boxShadow: '0 4px 12px rgba(30,198,182,0.15)'
              }}
            >
              {isLoading ? (
                <Spinner as="span" animation="border" size="sm" role="status" aria-hidden="true" />
              ) : step === steps.length - 1 ? (
                'Sign Up'
              ) : (
                'Next'
              )}
            </Button>
          </div>
        </Form>
        <div className="text-center mt-4">
          <p className="mb-0">
            Already have an account?{' '}
            <Link to="/login" style={{ color: '#1ec6b6', textDecoration: 'none', fontWeight: '600' }}>
              Log in
            </Link>
          </p>
        </div>
      </div>
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
        .signup-form-card h2.gradient-text {
          font-size: 2rem;
        }
        .signup-form-card p,
        .signup-form-card label,
        .signup-form-card .form-label,
        .signup-form-card .form-control,
        .signup-form-card .form-check-label,
        .signup-form-card .btn,
        .signup-form-card .alert,
        .signup-form-card .small {
          font-size: 0.97rem;
        }
        .signup-form-card .form-control {
          font-size: 0.97rem;
          padding: 0.5rem 0.75rem;
        }
        .signup-form-card .form-group,
        .signup-form-card .mb-4,
        .signup-form-card .mb-3,
        .signup-form-card .form-label,
        .signup-form-card .form-control,
        .signup-form-card .btn,
        .signup-form-card .alert,
        .signup-form-card .small {
          margin-bottom: 0.65rem !important;
        }
        .signup-form-card .form-group:last-child,
        .signup-form-card .mb-4:last-child,
        .signup-form-card .mb-3:last-child {
          margin-bottom: 0 !important;
        }
        .signup-form-card {
          padding-top: 1.2em !important;
        }
      `}</style>
    </div>
  );
};

export default Signup;
