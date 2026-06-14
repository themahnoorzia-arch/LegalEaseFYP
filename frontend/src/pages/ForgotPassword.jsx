import React, { useState, useRef, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Eye, EyeOff } from 'lucide-react';

const ForgotPassword = () => {
  const navigate = useNavigate();
  const [step, setStep] = useState(1); // 1=email, 2=otp, 3=new password
  const [email, setEmail] = useState('');
  const [otp, setOtp] = useState(['', '', '', '', '', '']);
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [showPw, setShowPw] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [resendStatus, setResendStatus] = useState(null);
  const [countdown, setCountdown] = useState(0);
  const [success, setSuccess] = useState(false);
  const inputs = useRef([]);

  useEffect(() => {
    if (step === 2) setTimeout(() => inputs.current[0]?.focus(), 100);
  }, [step]);

  useEffect(() => {
    if (countdown <= 0) return;
    const t = setTimeout(() => setCountdown(c => c - 1), 1000);
    return () => clearTimeout(t);
  }, [countdown]);

  // Step 1 — send OTP
  const handleSendOtp = async (e) => {
    e.preventDefault();
    if (!email) { setError('Enter your email address.'); return; }
    setLoading(true); setError('');
    try {
      const res = await fetch('/api/forgot-password', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email }),
      });
      const data = await res.json();
      if (data.success) {
        setStep(2);
        setCountdown(60);
      } else {
        setError(data.message);
      }
    } catch { setError('Could not reach the server.'); }
    finally { setLoading(false); }
  };

  // OTP input helpers
  const handleOtpChange = (i, value) => {
    if (!/^\d*$/.test(value)) return;
    const next = [...otp]; next[i] = value.slice(-1); setOtp(next); setError('');
    if (value && i < 5) inputs.current[i + 1]?.focus();
  };
  const handleOtpKey = (i, e) => {
    if (e.key === 'Backspace' && !otp[i] && i > 0) inputs.current[i - 1]?.focus();
  };
  const handlePaste = (e) => {
    const p = e.clipboardData.getData('text').replace(/\D/g, '').slice(0, 6);
    if (p.length === 6) { setOtp(p.split('')); inputs.current[5]?.focus(); }
    e.preventDefault();
  };

  // Step 2 → verify OTP, move to step 3
  const handleVerifyOtp = async () => {
    const code = otp.join('');
    if (code.length < 6) { setError('Enter the full 6-digit code.'); return; }
    setLoading(true); setError('');
    try {
      const res = await fetch('/api/reset-password', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, otp: code, newPassword: '__CHECK_OTP__' }),
      });
      const data = await res.json();
      // If OTP is wrong/expired we get an error; if password is too short we move on
      if (data.message?.includes('8 characters') || data.success) {
        setStep(3);
      } else {
        setError(data.message);
        if (data.expired) setOtp(['', '', '', '', '', '']);
      }
    } catch { setError('Could not reach the server.'); }
    finally { setLoading(false); }
  };

  // Step 3 — reset password
  const handleResetPassword = async (e) => {
    e.preventDefault();
    if (newPassword.length < 8) { setError('Password must be at least 8 characters.'); return; }
    if (newPassword !== confirmPassword) { setError('Passwords do not match.'); return; }
    setLoading(true); setError('');
    try {
      const res = await fetch('/api/reset-password', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, otp: otp.join(''), newPassword }),
      });
      const data = await res.json();
      if (data.success) { setSuccess(true); }
      else { setError(data.message); }
    } catch { setError('Could not reach the server.'); }
    finally { setLoading(false); }
  };

  const handleResend = async () => {
    setResendStatus('sending');
    try {
      const res = await fetch('/api/resend-otp', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, purpose: 'reset' }),
      });
      const data = await res.json();
      if (data.success) { setResendStatus('sent'); setCountdown(60); setOtp(['', '', '', '', '', '']); }
      else { setResendStatus('error'); setError(data.message); }
    } catch { setResendStatus('error'); }
  };

  const containerStyle = {
    minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center',
    background: 'linear-gradient(135deg, #22304a 0%, #1ec6b6 100%)',
  };
  const cardStyle = {
    background: '#fff', borderRadius: 16, padding: '48px 40px',
    maxWidth: 420, width: '90%', boxShadow: '0 8px 40px rgba(0,0,0,0.18)',
  };
  const inputStyle = {
    width: '100%', padding: '12px 14px', border: '1.5px solid #e5e7eb',
    borderRadius: 8, fontSize: 15, outline: 'none', color: '#22304a',
  };
  const btnStyle = {
    width: '100%', padding: 13, background: '#1ec6b6', color: '#fff',
    border: 'none', borderRadius: 8, fontWeight: 700, fontSize: 15,
    cursor: loading ? 'not-allowed' : 'pointer', opacity: loading ? 0.7 : 1,
    marginTop: 8,
  };
  const errorBox = error && (
    <div style={{ background: '#fef2f2', border: '1px solid #fecaca', borderRadius: 8, padding: '10px 14px', color: '#dc2626', fontSize: 14, marginBottom: 12 }}>
      {error}
    </div>
  );

  if (success) return (
    <div style={containerStyle}>
      <div style={{ ...cardStyle, textAlign: 'center' }}>
        <div style={{ fontSize: 52, marginBottom: 16 }}>✅</div>
        <h2 style={{ color: '#22304a', fontWeight: 700, marginBottom: 12 }}>Password reset!</h2>
        <p style={{ color: '#6b7280', marginBottom: 28 }}>Your password has been updated. You can now log in with your new password.</p>
        <button onClick={() => navigate('/login')} style={{ ...btnStyle, width: 'auto', padding: '12px 32px' }}>
          Go to Login
        </button>
      </div>
    </div>
  );

  return (
    <div style={containerStyle}>
      <div style={cardStyle}>
        {/* Progress dots */}
        <div style={{ display: 'flex', justifyContent: 'center', gap: 8, marginBottom: 28 }}>
          {[1, 2, 3].map(s => (
            <div key={s} style={{
              width: s === step ? 24 : 8, height: 8, borderRadius: 4,
              background: s <= step ? '#1ec6b6' : '#e5e7eb',
              transition: 'all 0.3s',
            }} />
          ))}
        </div>

        {step === 1 && (
          <>
            <h2 style={{ color: '#22304a', fontWeight: 700, marginBottom: 8 }}>Forgot password?</h2>
            <p style={{ color: '#6b7280', fontSize: 14, marginBottom: 24 }}>
              Enter your registered email and we'll send you a reset code.
            </p>
            {errorBox}
            <form onSubmit={handleSendOtp}>
              <label style={{ fontWeight: 600, fontSize: 14, color: '#374151', display: 'block', marginBottom: 6 }}>Email address</label>
              <input
                type="email" value={email} onChange={e => setEmail(e.target.value)}
                placeholder="you@example.com" style={inputStyle} required
              />
              <button type="submit" disabled={loading} style={btnStyle}>
                {loading ? 'Sending…' : 'Send reset code'}
              </button>
            </form>
          </>
        )}

        {step === 2 && (
          <>
            <h2 style={{ color: '#22304a', fontWeight: 700, marginBottom: 8 }}>Enter your code</h2>
            <p style={{ color: '#6b7280', fontSize: 14, marginBottom: 6 }}>
              We sent a 6-digit code to
            </p>
            <p style={{ color: '#22304a', fontWeight: 600, fontSize: 15, marginBottom: 24 }}>{email}</p>
            {errorBox}
            <div style={{ display: 'flex', gap: 10, justifyContent: 'center', marginBottom: 20 }}>
              {otp.map((digit, i) => (
                <input
                  key={i} ref={el => inputs.current[i] = el}
                  type="text" inputMode="numeric" maxLength={1} value={digit}
                  onChange={e => handleOtpChange(i, e.target.value)}
                  onKeyDown={e => handleOtpKey(i, e)} onPaste={handlePaste}
                  style={{
                    width: 48, height: 56, textAlign: 'center', fontSize: 24,
                    fontWeight: 700, borderRadius: 8, border: error ? '2px solid #ef4444' : '2px solid #e5e7eb',
                    outline: 'none', color: '#22304a',
                  }}
                  onFocus={e => e.target.style.borderColor = '#1ec6b6'}
                  onBlur={e => e.target.style.borderColor = error ? '#ef4444' : '#e5e7eb'}
                />
              ))}
            </div>
            <button onClick={handleVerifyOtp} disabled={loading} style={btnStyle}>
              {loading ? 'Checking…' : 'Continue'}
            </button>
            <div style={{ textAlign: 'center', marginTop: 16, fontSize: 14, color: '#6b7280' }}>
              {countdown > 0 ? (
                <span style={{ color: '#9ca3af' }}>Resend in {countdown}s</span>
              ) : resendStatus === 'sent' ? (
                <span style={{ color: '#16a34a', fontWeight: 600 }}>✓ New code sent!</span>
              ) : (
                <button onClick={handleResend} disabled={resendStatus === 'sending'}
                  style={{ background: 'none', border: 'none', color: '#1ec6b6', fontWeight: 600, cursor: 'pointer', fontSize: 14 }}>
                  {resendStatus === 'sending' ? 'Sending…' : 'Resend code'}
                </button>
              )}
            </div>
          </>
        )}

        {step === 3 && (
          <>
            <h2 style={{ color: '#22304a', fontWeight: 700, marginBottom: 8 }}>Set new password</h2>
            <p style={{ color: '#6b7280', fontSize: 14, marginBottom: 24 }}>Choose a strong password for your account.</p>
            {errorBox}
            <form onSubmit={handleResetPassword}>
              <label style={{ fontWeight: 600, fontSize: 14, color: '#374151', display: 'block', marginBottom: 6 }}>New password</label>
              <div style={{ position: 'relative', marginBottom: 14 }}>
                <input
                  type={showPw ? 'text' : 'password'} value={newPassword}
                  onChange={e => setNewPassword(e.target.value)}
                  placeholder="Minimum 8 characters" style={{ ...inputStyle, paddingRight: 44 }} required
                />
                <button type="button" onClick={() => setShowPw(p => !p)}
                  style={{ position: 'absolute', right: 12, top: '50%', transform: 'translateY(-50%)', background: 'none', border: 'none', cursor: 'pointer', color: '#9ca3af' }}>
                  {showPw ? <EyeOff size={18} /> : <Eye size={18} />}
                </button>
              </div>
              <label style={{ fontWeight: 600, fontSize: 14, color: '#374151', display: 'block', marginBottom: 6 }}>Confirm password</label>
              <input
                type="password" value={confirmPassword}
                onChange={e => setConfirmPassword(e.target.value)}
                placeholder="Re-enter password" style={{ ...inputStyle, marginBottom: 4 }} required
              />
              <button type="submit" disabled={loading} style={btnStyle}>
                {loading ? 'Saving…' : 'Reset password'}
              </button>
            </form>
          </>
        )}

        <div style={{ textAlign: 'center', marginTop: 24 }}>
          <Link to="/login" style={{ color: '#9ca3af', fontSize: 13 }}>← Back to login</Link>
        </div>
      </div>
    </div>
  );
};

export default ForgotPassword;
