import React, { useState, useEffect, useCallback } from 'react';
import {
  Container, Table, Form, Card, Image, Spinner, Alert,
  Badge, Button, Modal, Row, Col, InputGroup,
} from 'react-bootstrap';
import { LogOut, Users, FileText, Activity, ClipboardList, LayoutDashboard } from 'lucide-react';

// ── helpers ────────────────────────────────────────────────────────────────

const statusBadge = (status) => {
  const map = {
    Open: 'primary', Pending: 'warning', Closed: 'success',
    Success: 'success', Error: 'danger', scheduled: 'secondary',
  };
  return <Badge bg={map[status] || 'secondary'}>{status}</Badge>;
};

const roleBadge = (role) => {
  const map = {
    Admin: 'danger', Judge: 'primary', Lawyer: 'info',
    CourtRegistrar: 'success', CaseParticipant: 'secondary',
  };
  return <Badge bg={map[role] || 'secondary'}>{role}</Badge>;
};

const fmtDate = (d) => {
  if (!d) return '—';
  try { return new Date(d).toLocaleDateString(); } catch { return d; }
};

const fmtDateTime = (d) => {
  if (!d) return '—';
  try { return new Date(d).toLocaleString(); } catch { return d; }
};

const activityIcon = (type) => {
  const icons = {
    case_filed: '📁', hearing: '⚖️', appeal: '📋',
    decision: '🔒', user_registered: '👤',
  };
  return icons[type] || '📌';
};

// ── main component ─────────────────────────────────────────────────────────

const AdminDashboard = () => {
  const [activePage, setActivePage] = useState('overview');
  const [adminData, setAdminData] = useState({ username: 'Admin' });

  // data states
  const [stats, setStats] = useState(null);
  const [users, setUsers] = useState([]);
  const [cases, setCases] = useState([]);
  const [activity, setActivity] = useState([]);
  const [logs, setLogs] = useState([]);

  // ui states
  const [loading, setLoading] = useState({});
  const [errors, setErrors] = useState({});
  const [searchUser, setSearchUser] = useState('');
  const [searchCase, setSearchCase] = useState('');
  const [searchLog, setSearchLog] = useState('');

  // role change modal
  const [roleModal, setRoleModal] = useState({ show: false, user: null, newRole: '' });
  const [deleteModal, setDeleteModal] = useState({ show: false, user: null });
  const [actionMsg, setActionMsg] = useState(null);

  // ── fetch helpers ──────────────────────────────────────────────────────

  const load = useCallback(async (key, url, setter) => {
    setLoading(p => ({ ...p, [key]: true }));
    setErrors(p => ({ ...p, [key]: null }));
    try {
      const res = await fetch(url, { credentials: 'include' });
      const data = await res.json();
      if (!res.ok) throw new Error(data.error || data.message || 'Failed');
      setter(data);
    } catch (e) {
      setErrors(p => ({ ...p, [key]: e.message }));
    } finally {
      setLoading(p => ({ ...p, [key]: false }));
    }
  }, []);

  // ── load on page change ────────────────────────────────────────────────

  useEffect(() => {
    fetch('/api/adminprofile', { credentials: 'include' })
      .then(r => r.json())
      .then(d => {
        if (d.success) setAdminData({ username: `${d.data.firstName} ${d.data.lastName}`.trim() });
      })
      .catch(() => {});
  }, []);

  useEffect(() => {
    if (activePage === 'overview' && !stats) {
      load('stats', '/api/admin/stats', d => setStats(d));
    }
    if (activePage === 'users' && users.length === 0) {
      load('users', '/api/admin/users', d => setUsers(d.users || []));
    }
    if (activePage === 'cases' && cases.length === 0) {
      load('cases', '/api/admin/cases', d => setCases(d.cases || []));
    }
    if (activePage === 'activity' && activity.length === 0) {
      load('activity', '/api/admin/activity', d => setActivity(d.activity || []));
    }
    if (activePage === 'logs' && logs.length === 0) {
      load('logs', '/api/logs', d => setLogs(Array.isArray(d) ? d : []));
    }
  }, [activePage]); // eslint-disable-line

  // ── user actions ───────────────────────────────────────────────────────

  const confirmDeleteUser = async () => {
    const u = deleteModal.user;
    if (!u) return;
    try {
      const res = await fetch(`/api/admin/users/${u.userid}`, {
        method: 'DELETE', credentials: 'include',
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.error);
      setUsers(prev => prev.filter(x => x.userid !== u.userid));
      setActionMsg({ type: 'success', text: `User "${u.name}" deleted.` });
    } catch (e) {
      setActionMsg({ type: 'danger', text: e.message });
    }
    setDeleteModal({ show: false, user: null });
  };

  const confirmRoleChange = async () => {
    const { user, newRole } = roleModal;
    if (!user || !newRole) return;
    try {
      const res = await fetch(`/api/admin/users/${user.userid}/role`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({ role: newRole }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.error);
      setUsers(prev => prev.map(u => u.userid === user.userid ? { ...u, role: newRole } : u));
      setActionMsg({ type: 'success', text: `Role updated to ${newRole} for "${user.name}".` });
    } catch (e) {
      setActionMsg({ type: 'danger', text: e.message });
    }
    setRoleModal({ show: false, user: null, newRole: '' });
  };

  const handleLogout = () => {
    localStorage.clear();
    window.location.href = '/login';
  };

  // ── filtered lists ─────────────────────────────────────────────────────

  const filteredUsers = users.filter(u =>
    [u.name, u.email, u.role, u.phone, u.cnic].join(' ').toLowerCase().includes(searchUser.toLowerCase())
  );

  const filteredCases = cases.filter(c =>
    [c.title, c.casenumber, c.court, c.judge, c.client, c.status].join(' ').toLowerCase().includes(searchCase.toLowerCase())
  );

  const filteredLogs = logs.filter(l =>
    Object.values(l).join(' ').toLowerCase().includes(searchLog.toLowerCase())
  );

  // ── sidebar items ──────────────────────────────────────────────────────

  const navItems = [
    { key: 'overview', label: 'Overview', icon: <LayoutDashboard size={16} /> },
    { key: 'users', label: 'Users', icon: <Users size={16} /> },
    { key: 'cases', label: 'All Cases', icon: <FileText size={16} /> },
    { key: 'activity', label: 'Activity Feed', icon: <Activity size={16} /> },
    { key: 'logs', label: 'System Logs', icon: <ClipboardList size={16} /> },
  ];

  // ── render helpers ─────────────────────────────────────────────────────

  const LoadingRow = ({ cols }) => (
    <tr><td colSpan={cols} className="text-center py-4"><Spinner size="sm" /> Loading...</td></tr>
  );

  const ErrorRow = ({ cols, msg }) => (
    <tr><td colSpan={cols} className="text-center text-danger py-3">{msg}</td></tr>
  );

  // ── pages ──────────────────────────────────────────────────────────────

  const Overview = () => (
    <div>
      <h4 className="fw-bold mb-4" style={{ color: '#22304a' }}>Overview</h4>
      {loading.stats && <div className="text-center py-5"><Spinner /></div>}
      {errors.stats && <Alert variant="danger">{errors.stats}</Alert>}
      {stats && (
        <>
          {/* Case stats */}
          <Row className="g-3 mb-4">
            {[
              { label: 'Total Cases', value: stats.cases.total, bg: '#22304a', icon: '📁' },
              { label: 'Open Cases', value: stats.cases.open, bg: '#1ec6b6', icon: '⚖️' },
              { label: 'Pending Cases', value: stats.cases.pending, bg: '#f6c344', icon: '⏳' },
              { label: 'Closed Cases', value: stats.cases.closed, bg: '#6c757d', icon: '🔒' },
            ].map(card => (
              <Col key={card.label} xs={6} md={3}>
                <Card className="border-0 shadow-sm h-100" style={{ borderRadius: 12 }}>
                  <Card.Body className="d-flex align-items-center gap-3">
                    <div style={{ fontSize: 28 }}>{card.icon}</div>
                    <div>
                      <div className="fw-bold fs-4" style={{ color: card.bg }}>{card.value}</div>
                      <div className="text-muted small">{card.label}</div>
                    </div>
                  </Card.Body>
                </Card>
              </Col>
            ))}
          </Row>

          {/* User + hearing + appeal stats */}
          <Row className="g-3 mb-4">
            {[
              { label: 'Total Users', value: stats.users.total, bg: '#22304a', icon: '👥' },
              { label: 'Total Hearings', value: stats.hearings.total, bg: '#1ec6b6', icon: '📅' },
              { label: 'Total Appeals', value: stats.appeals.total, bg: '#6f42c1', icon: '📋' },
              { label: 'Pending Appeals', value: stats.appeals.pending, bg: '#dc3545', icon: '🔔' },
            ].map(card => (
              <Col key={card.label} xs={6} md={3}>
                <Card className="border-0 shadow-sm h-100" style={{ borderRadius: 12 }}>
                  <Card.Body className="d-flex align-items-center gap-3">
                    <div style={{ fontSize: 28 }}>{card.icon}</div>
                    <div>
                      <div className="fw-bold fs-4" style={{ color: card.bg }}>{card.value}</div>
                      <div className="text-muted small">{card.label}</div>
                    </div>
                  </Card.Body>
                </Card>
              </Col>
            ))}
          </Row>

          {/* Users by role */}
          <Card className="border-0 shadow-sm" style={{ borderRadius: 12 }}>
            <Card.Body>
              <h6 className="fw-bold mb-3">Users by Role</h6>
              <div className="d-flex flex-wrap gap-3">
                {Object.entries(stats.users.by_role).map(([role, count]) => (
                  <div key={role} className="text-center p-3 rounded" style={{ background: '#f8f9fa', minWidth: 100 }}>
                    <div className="fw-bold fs-5">{count}</div>
                    <div>{roleBadge(role)}</div>
                  </div>
                ))}
              </div>
            </Card.Body>
          </Card>
        </>
      )}
    </div>
  );

  const UsersPage = () => (
    <div>
      <h4 className="fw-bold mb-3" style={{ color: '#22304a' }}>User Management</h4>
      <div className="text-muted mb-3 small">View all registered users. Change roles or remove accounts.</div>
      {actionMsg && (
        <Alert variant={actionMsg.type} dismissible onClose={() => setActionMsg(null)}>
          {actionMsg.text}
        </Alert>
      )}
      <InputGroup className="mb-3" style={{ maxWidth: 400 }}>
        <InputGroup.Text>🔍</InputGroup.Text>
        <Form.Control placeholder="Search by name, email, role…" value={searchUser} onChange={e => setSearchUser(e.target.value)} />
      </InputGroup>
      <div className="table-responsive">
        <Table hover className="align-middle mb-0">
          <thead className="table-light">
            <tr>
              <th>#</th>
              <th>Name</th>
              <th>Email</th>
              <th>Phone</th>
              <th>Role</th>
              <th>Specialization</th>
              <th>Joined</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {loading.users && <LoadingRow cols={8} />}
            {errors.users && <ErrorRow cols={8} msg={errors.users} />}
            {!loading.users && !errors.users && filteredUsers.length === 0 && (
              <tr><td colSpan={8} className="text-center text-muted py-4">No users found.</td></tr>
            )}
            {filteredUsers.map((u, i) => (
              <tr key={u.userid}>
                <td className="text-muted small">{i + 1}</td>
                <td className="fw-semibold">{u.name || '—'}</td>
                <td>{u.email}</td>
                <td>{u.phone}</td>
                <td>{roleBadge(u.role)}</td>
                <td className="text-muted small">{u.specialization}</td>
                <td className="text-muted small">{fmtDate(u.joinedAt)}</td>
                <td>
                  <div className="d-flex gap-1">
                    <Button
                      size="sm"
                      variant="outline-primary"
                      onClick={() => setRoleModal({ show: true, user: u, newRole: u.role })}
                    >
                      Change Role
                    </Button>
                    <Button
                      size="sm"
                      variant="outline-danger"
                      onClick={() => setDeleteModal({ show: true, user: u })}
                    >
                      Delete
                    </Button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </Table>
      </div>
    </div>
  );

  const CasesPage = () => (
    <div>
      <h4 className="fw-bold mb-3" style={{ color: '#22304a' }}>All Cases</h4>
      <div className="text-muted mb-3 small">Read-only view of every case across all courts.</div>
      <InputGroup className="mb-3" style={{ maxWidth: 400 }}>
        <InputGroup.Text>🔍</InputGroup.Text>
        <Form.Control placeholder="Search by title, court, judge…" value={searchCase} onChange={e => setSearchCase(e.target.value)} />
      </InputGroup>
      <div className="table-responsive">
        <Table hover className="align-middle mb-0">
          <thead className="table-light">
            <tr>
              <th>Case Name</th>
              <th>Number</th>
              <th>Type</th>
              <th>Court</th>
              <th>Judge</th>
              <th>Lawyer</th>
              <th>Client</th>
              <th>Filing Date</th>
              <th>Status</th>
            </tr>
          </thead>
          <tbody>
            {loading.cases && <LoadingRow cols={9} />}
            {errors.cases && <ErrorRow cols={9} msg={errors.cases} />}
            {!loading.cases && !errors.cases && filteredCases.length === 0 && (
              <tr><td colSpan={9} className="text-center text-muted py-4">No cases found.</td></tr>
            )}
            {filteredCases.map(c => (
              <tr key={c.caseid}>
                <td className="fw-semibold">{c.title}</td>
                <td className="text-muted small">{c.casenumber}</td>
                <td>{c.casetype}</td>
                <td>{c.court}</td>
                <td>{c.judge}</td>
                <td>{c.lawyer}</td>
                <td>{c.client}</td>
                <td className="text-muted small">{fmtDate(c.filingdate)}</td>
                <td>{statusBadge(c.status)}</td>
              </tr>
            ))}
          </tbody>
        </Table>
      </div>
    </div>
  );

  const ActivityPage = () => (
    <div>
      <h4 className="fw-bold mb-3" style={{ color: '#22304a' }}>Activity Feed</h4>
      <div className="text-muted mb-3 small">Live feed of real events — cases, hearings, appeals, decisions, new users.</div>
      {loading.activity && <div className="text-center py-5"><Spinner /></div>}
      {errors.activity && <Alert variant="danger">{errors.activity}</Alert>}
      {!loading.activity && !errors.activity && activity.length === 0 && (
        <div className="text-center text-muted py-5">No activity yet.</div>
      )}
      <div style={{ maxHeight: '65vh', overflowY: 'auto' }}>
        {activity.map((ev, i) => (
          <div key={i} className="d-flex gap-3 py-3 border-bottom align-items-start">
            <div style={{ fontSize: 22, minWidth: 32, textAlign: 'center' }}>{activityIcon(ev.type)}</div>
            <div className="flex-grow-1">
              <div className="d-flex align-items-center gap-2 flex-wrap">
                <Badge bg="light" text="dark" className="border">{ev.label}</Badge>
                {statusBadge(ev.status)}
                <span className="text-muted small">{fmtDate(ev.date)}</span>
              </div>
              <div className="mt-1">{ev.description}</div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );

  const LogsPage = () => (
    <div>
      <h4 className="fw-bold mb-3" style={{ color: '#22304a' }}>System Logs</h4>
      <div className="text-muted mb-3 small">Auto-written log entries for key actions (user registration, case creation, verification).</div>
      <InputGroup className="mb-3" style={{ maxWidth: 400 }}>
        <InputGroup.Text>🔍</InputGroup.Text>
        <Form.Control placeholder="Search logs…" value={searchLog} onChange={e => setSearchLog(e.target.value)} />
      </InputGroup>
      {loading.logs && <div className="text-center py-5"><Spinner /></div>}
      {errors.logs && <Alert variant="danger">{errors.logs}</Alert>}
      <div className="table-responsive">
        <Table hover className="align-middle mb-0">
          <thead className="table-light">
            <tr>
              <th>Action</th>
              <th>Description</th>
              <th>Entity</th>
              <th>Status</th>
              <th>Timestamp</th>
            </tr>
          </thead>
          <tbody>
            {!loading.logs && filteredLogs.length === 0 && (
              <tr><td colSpan={5} className="text-center text-muted py-4">No logs yet. New registrations and case actions will appear here.</td></tr>
            )}
            {filteredLogs.map(l => (
              <tr key={l.logid}>
                <td><Badge bg="secondary">{l.actiontype}</Badge></td>
                <td>{l.description}</td>
                <td className="text-muted small">{l.entitytype}</td>
                <td>{statusBadge(l.status)}</td>
                <td className="text-muted small">{fmtDateTime(l.actiontimestamp)}</td>
              </tr>
            ))}
          </tbody>
        </Table>
      </div>
    </div>
  );

  const pageMap = {
    overview: <Overview />,
    users: <UsersPage />,
    cases: <CasesPage />,
    activity: <ActivityPage />,
    logs: <LogsPage />,
  };

  // ── render ──────────────────────────────────────────────────────────────

  return (
    <div style={{ minHeight: '100vh', width: '100vw', display: 'flex', flexDirection: 'column', background: '#f0f2f5', overflow: 'hidden' }}>
      {/* Header */}
      <div style={{ background: 'linear-gradient(90deg, #22304a 0%, #1ec6b6 100%)', padding: '12px 24px', flexShrink: 0 }}>
        <div className="d-flex justify-content-between align-items-center">
          <div className="d-flex align-items-center gap-3">
            <span style={{ color: '#fff', fontWeight: 700, fontSize: 18 }}>Court Central</span>
            <span style={{ color: 'rgba(255,255,255,0.5)' }}>|</span>
            <span style={{ color: 'rgba(255,255,255,0.9)', fontWeight: 600 }}>Admin Dashboard</span>
            <span style={{ color: 'rgba(255,255,255,0.5)' }}>|</span>
            <span style={{ color: 'rgba(255,255,255,0.85)', fontSize: 14 }}>{adminData.username}</span>
          </div>
          <button
            className="btn btn-sm"
            onClick={handleLogout}
            style={{ background: 'rgba(255,255,255,0.15)', color: '#fff', border: '1px solid rgba(255,255,255,0.3)', display: 'flex', alignItems: 'center', gap: 6 }}
          >
            <LogOut size={16} />
            Logout
          </button>
        </div>
      </div>

      {/* Body */}
      <div style={{ display: 'flex', flex: 1, overflow: 'hidden', minHeight: 0 }}>
        {/* Sidebar */}
        <div style={{ width: 200, background: '#22304a', flexShrink: 0, paddingTop: 16 }}>
          {navItems.map(item => (
            <button
              key={item.key}
              onClick={() => setActivePage(item.key)}
              style={{
                display: 'flex', alignItems: 'center', gap: 10,
                width: '100%', padding: '12px 20px', border: 'none', textAlign: 'left',
                background: activePage === item.key ? 'rgba(30,198,182,0.2)' : 'transparent',
                borderLeft: activePage === item.key ? '3px solid #1ec6b6' : '3px solid transparent',
                color: activePage === item.key ? '#1ec6b6' : 'rgba(255,255,255,0.7)',
                fontWeight: activePage === item.key ? 600 : 400,
                cursor: 'pointer', fontSize: 14,
              }}
            >
              {item.icon}
              {item.label}
            </button>
          ))}
        </div>

        {/* Main */}
        <div style={{ flex: 1, overflow: 'auto', padding: 24 }}>
          <Card className="border-0 shadow-sm h-100" style={{ borderRadius: 12 }}>
            <Card.Body style={{ padding: 24 }}>
              {pageMap[activePage]}
            </Card.Body>
          </Card>
        </div>
      </div>

      {/* Role change modal */}
      <Modal show={roleModal.show} onHide={() => setRoleModal({ show: false, user: null, newRole: '' })} centered>
        <Modal.Header closeButton>
          <Modal.Title>Change Role — {roleModal.user?.name}</Modal.Title>
        </Modal.Header>
        <Modal.Body>
          <Form.Label>New Role</Form.Label>
          <Form.Select value={roleModal.newRole} onChange={e => setRoleModal(p => ({ ...p, newRole: e.target.value }))}>
            {['Admin', 'CourtRegistrar', 'Judge', 'Lawyer', 'CaseParticipant'].map(r => (
              <option key={r} value={r}>{r}</option>
            ))}
          </Form.Select>
          <div className="text-muted small mt-2">Current role: {roleModal.user?.role}</div>
        </Modal.Body>
        <Modal.Footer>
          <Button variant="secondary" onClick={() => setRoleModal({ show: false, user: null, newRole: '' })}>Cancel</Button>
          <Button variant="primary" onClick={confirmRoleChange}>Save</Button>
        </Modal.Footer>
      </Modal>

      {/* Delete confirm modal */}
      <Modal show={deleteModal.show} onHide={() => setDeleteModal({ show: false, user: null })} centered>
        <Modal.Header closeButton>
          <Modal.Title>Delete User</Modal.Title>
        </Modal.Header>
        <Modal.Body>
          Are you sure you want to permanently delete <strong>{deleteModal.user?.name}</strong> ({deleteModal.user?.role})?
          This cannot be undone and will remove all their associated records.
        </Modal.Body>
        <Modal.Footer>
          <Button variant="secondary" onClick={() => setDeleteModal({ show: false, user: null })}>Cancel</Button>
          <Button variant="danger" onClick={confirmDeleteUser}>Delete</Button>
        </Modal.Footer>
      </Modal>
    </div>
  );
};

export default AdminDashboard;
