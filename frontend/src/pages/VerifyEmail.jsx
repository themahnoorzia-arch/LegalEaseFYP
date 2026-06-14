import React, { useEffect, useState } from 'react';
import { useSearchParams, Link } from 'react-router-dom';

const VerifyEmail = () => {
  const [searchParams] = useSearchParams();
  const token = searchParams.get('token');
  const status = searchParams.get('status');
  const [state, setState] = useState(token ? 'loading' : status || 'invalid');

  useEffect(() => {
    if (!token) return;
    fetch(`/api/verify-email?token=${encodeURIComponent(token)}`, { credentials: 'include' })
      .then(res => {
        // The backend redirects, so we check the final URL via the status param
        // If we're still here, check the response
        if (res.redirected) {
          const url = new URL(res.url);
          setState(url.searchParams.get('status') || 'success');
        } else {
          setState('success');
        }
      })
      .catch(() => setState('error'));
  }, [token]);

  // If status param is set (redirected from backend), use it directly
  useEffect(() => {
    if (status) setState(status);
  }, [status]);

  const content = {
    loading: {
      icon: '⏳',
      title: 'Verifying your email…',
      body: 'Please wait a moment.',
      color: '#1ec6b6',
      showLogin: false,
    },
    success: {
      icon: '✅',
      title: 'Email verified!',
      body: 'Your account is now active. You can log in.',
      color: '#22c55e',
      showLogin: true,
    },
    expired: {
      icon: '⏰',
      title: 'Link expired',
      body: 'This verification link has expired (links are valid for 24 hours). Request a new one from the login page.',
      color: '#f59e0b',
      showLogin: true,
    },
    invalid: {
      icon: '❌',
      title: 'Invalid link',
      body: 'This verification link is invalid or has already been used.',
      color: '#ef4444',
      showLogin: true,
    },
    error: {
      icon: '⚠️',
      title: 'Something went wrong',
      body: 'An unexpected error occurred. Please try again or contact support.',
      color: '#ef4444',
      showLogin: true,
    },
  };

  const c = content[state] || content.invalid;

  return (
    <div style={{
      minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center',
      background: 'linear-gradient(135deg, #22304a 0%, #1ec6b6 100%)',
    }}>
      <div style={{
        background: '#fff', borderRadius: 16, padding: '48px 40px', maxWidth: 440,
        width: '90%', textAlign: 'center', boxShadow: '0 8px 40px rgba(0,0,0,0.18)',
      }}>
        <div style={{ fontSize: 56, marginBottom: 16 }}>{c.icon}</div>
        <h2 style={{ color: '#22304a', fontWeight: 700, marginBottom: 12 }}>{c.title}</h2>
        <p style={{ color: '#6b7280', fontSize: 15, marginBottom: 28 }}>{c.body}</p>
        {c.showLogin && (
          <Link
            to="/login"
            style={{
              display: 'inline-block', padding: '12px 32px',
              background: '#1ec6b6', color: '#fff', borderRadius: 8,
              fontWeight: 600, textDecoration: 'none', fontSize: 15,
            }}
          >
            Go to Login
          </Link>
        )}
        <div style={{ marginTop: 16 }}>
          <Link to="/" style={{ color: '#9ca3af', fontSize: 13 }}>Back to Home</Link>
        </div>
      </div>
    </div>
  );
};

export default VerifyEmail;
