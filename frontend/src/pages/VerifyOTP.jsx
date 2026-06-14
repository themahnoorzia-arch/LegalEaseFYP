import React, { useState, useRef, useEffect } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';

const VerifyOTP = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const email = location.state?.email || '';
  const role = location.state?.role || '';

  const [otp, setOtp] = useState(['', '', '', '', '', '']);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [resendStatus, setResendStatus] = useState(null);
  const [countdown, setCountdown] = useState(0);
  const inputs = useRef([]);

  useEffect(() => {
    inputs.current[0]?.focus();
  }, []);

  useEffect(() => {
    if (countdown <= 0) return;
    const t = setTimeout(() => setCountdown(c => c - 1), 1000);
    return () => clearTimeout(t);
  }, [countdown]);

  const handleChange = (index, value) => {
    if (!/^\d*$/.test(value)) return;
    const next = [...otp];
    next[index] = value.slice(-1);
    setOtp(next);
    setError('');
    if (value && index < 5) inputs.current[index + 1]?.focus();
  };

  const handleKeyDown = (index, e) => {
    if (e.key === 'Backspace' && !otp[index] && index > 0) {
      inputs.current[index - 1]?.focus();
    }
  };

  const handlePaste = (e) => {
    const pasted = e.clipboardData.getData('text').replace(/\D/g, '').slice(0, 6);
    if (pasted.length === 6) {
      setOtp(pasted.split(''));
      inputs.current[5]?.focus();
    }
    e.preventDefault();
  };

  const handleVerify = async () => {
    const code = otp.join('');
    if (code.length < 6) {
      setError('Please enter the full 6-digit code.');
      return;
    }
    setLoading(true);
    setError('');
    try {
      const res = await fetch('/api/verify-otp', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, otp: code }),
      });
      const data = await res.json();
      if (data.success) {
        navigate('/CompleteProfile', { state: { role } });
      } else {
        setError(data.message || 'Incorrect code. Try again.');
        if (data.expired) setOtp(['', '', '', '', '', '']);
      }
    } catch {
      setError('Could not reach the server. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleResend = async () => {
    setResendStatus('sending');
    setError('');
    try {
      const res = await fetch('/api/resend-otp', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, purpose: 'verify' }),
      });
      const data = await res.json();
      if (data.success) {
        setResendStatus('sent');
        setCountdown(60);
        setOtp(['', '', '', '', '', '']);
        inputs.current[0]?.focus();
      } else {
        setResendStatus('error');
        setError(data.message);
      }
    } catch {
      setResendStatus('error');
    }
  };

  return (
    <div style={{
      minHeight: '100vh',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      background: 'linear-gradient(135deg, #22304a 0%, #1ec6b6 100%)',
      padding: '20px',
    }}>
      <div style={{
        background: '#ffffff',
        borderRadius: 20,
        padding: '48px 40px',
        maxWidth: 440,
        width: '100%',
        textAlign: 'center',
        boxShadow: '0 20px 60px rgba(0,0,0,0.25)',
      }}>
        {/* Icon */}
        <div style={{
          width: 72, height: 72, borderRadius: '50%',
          background: 'linear-gradient(135deg, #e0f7f5 0%, #b2ede8 100%)',
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          margin: '0 auto 20px',
          fontSize: 32,
        }}>
          ✉️
        </div>

        <h2 style={{ color: '#22304a', fontWeight: 700, fontSize: 24, marginBottom: 8 }}>
          Check your email
        </h2>
        <p style={{ color: '#6b7280', fontSize: 14, marginBottom: 4, lineHeight: 1.6 }}>
          We sent a 6-digit verification code to
        </p>
        <p style={{
          color: '#1ec6b6', fontWeight: 700, fontSize: 15,
          marginBottom: 32, wordBreak: 'break-all',
        }}>
          {email || 'your email'}
        </p>

        {/* OTP boxes */}
        <div style={{ display: 'flex', gap: 10, justifyContent: 'center', marginBottom: 24 }}>
          {otp.map((digit, i) => (
            <input
              key={i}
              ref={el => inputs.current[i] = el}
              type="text"
              inputMode="numeric"
              maxLength={1}
              value={digit}
              onChange={e => handleChange(i, e.target.value)}
              onKeyDown={e => handleKeyDown(i, e)}
              onPaste={handlePaste}
              style={{
                width: 52, height: 60,
                textAlign: 'center',
                fontSize: 26,
                fontWeight: 700,
                borderRadius: 12,
                border: error ? '2.5px solid #ef4444' : '2.5px solid #e5e7eb',
                outline: 'none',
                color: '#22304a',
                background: '#f9fafb',
                transition: 'border-color 0.2s, background 0.2s',
                cursor: 'text',
              }}
              onFocus={e => {
                e.target.style.borderColor = '#1ec6b6';
                e.target.style.background = '#f0fdfb';
              }}
              onBlur={e => {
                e.target.style.borderColor = error ? '#ef4444' : '#e5e7eb';
                e.target.style.background = '#f9fafb';
              }}
            />
          ))}
        </div>

        {error && (
          <div style={{
            background: '#fef2f2',
            border: '1px solid #fecaca',
            borderRadius: 10,
            padding: '10px 14px',
            color: '#dc2626',
            fontSize: 13,
            marginBottom: 16,
            textAlign: 'left',
          }}>
            {error}
          </div>
        )}

        <button
          onClick={handleVerify}
          disabled={loading}
          style={{
            width: '100%',
            padding: '14px',
            background: loading ? '#9ca3af' : 'linear-gradient(90deg, #22304a 0%, #1ec6b6 100%)',
            color: '#fff',
            border: 'none',
            borderRadius: 12,
            fontWeight: 700,
            fontSize: 16,
            cursor: loading ? 'not-allowed' : 'pointer',
            marginBottom: 20,
            transition: 'opacity 0.2s',
            letterSpacing: 0.3,
          }}
        >
          {loading ? 'Verifying…' : 'Verify Email'}
        </button>

        <div style={{ fontSize: 13, color: '#6b7280', marginBottom: 20 }}>
          Didn't receive the code?{' '}
          {countdown > 0 ? (
            <span style={{ color: '#9ca3af' }}>Resend in {countdown}s</span>
          ) : resendStatus === 'sent' ? (
            <span style={{ color: '#16a34a', fontWeight: 600 }}>✓ New code sent!</span>
          ) : (
            <button
              onClick={handleResend}
              disabled={resendStatus === 'sending'}
              style={{
                background: 'none', border: 'none',
                color: '#1ec6b6', fontWeight: 600,
                cursor: 'pointer', padding: 0, fontSize: 13,
              }}
            >
              {resendStatus === 'sending' ? 'Sending…' : 'Resend code'}
            </button>
          )}
        </div>

        <div style={{ fontSize: 13, color: '#9ca3af' }}>
          Wrong email?{' '}
          <button
            onClick={() => navigate('/signup')}
            style={{
              background: 'none', border: 'none',
              color: '#6b7280', cursor: 'pointer',
              padding: 0, fontSize: 13,
              textDecoration: 'underline',
            }}
          >
            Go back to signup
          </button>
        </div>
      </div>
    </div>
  );
};

export default VerifyOTP;
