import React, { useState, useEffect } from 'react';
import { Container, Table, Form, Card, Image, Spinner, Alert } from 'react-bootstrap';
import { LogOut } from 'lucide-react';

const AdminDashboard = () => {
  const [searchTerm, setSearchTerm] = useState('');
  const [profileImage, setProfileImage] = useState('https://via.placeholder.com/40');
  const [adminData, setAdminData] = useState({ username: 'Admin' });

  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Fetch logs
  useEffect(() => {
    const fetchLogs = async () => {
      try {
        const res = await fetch('/api/logs', { credentials: 'include' });
        const result = await res.json();

        if (res.ok) {
          setLogs(Array.isArray(result) ? result : []);
        } else {
          setError(result.error || result.message || 'Failed to load logs');
        }
      } catch (err) {
        setError('An error occurred while fetching logs');
      } finally {
        setLoading(false);
      }
    };

    fetchLogs();
  }, []);

  // Fetch admin profile
  useEffect(() => {
    const fetchAdminProfile = async () => {
      try {
        const res = await fetch('/api/adminprofile', { credentials: 'include' });
        const result = await res.json();

        if (res.ok && result.success) {
          const { firstName, lastName } = result.data;
          setAdminData({ username: `${firstName} ${lastName}`.trim() });
        }
      } catch (err) {
        console.error('Error fetching admin profile:', err);
      }
    };

    fetchAdminProfile();
  }, []);

  const filteredLogs = logs.filter(log =>
    Object.values(log).some(value =>
      value.toString().toLowerCase().includes(searchTerm.toLowerCase())
    )
  );

  const handleLogout = () => {
    localStorage.clear();
    window.location.href = '/login';
  };

  return (
    <div style={{ minHeight: '100vh', width: '100vw', background: '#f8f9fa', display: 'flex', flexDirection: 'column' }}>
      {/* Gradient Header */}
      <div className="dashboard-header-gradient p-3" style={{ background: 'linear-gradient(90deg, #22304a 0%, #1ec6b6 100%)', flex: '0 0 auto' }}>
        <div className="d-flex justify-content-between align-items-center">
          <div className="d-flex align-items-center gap-3">
            <h4 className="mb-0" style={{ color: '#fff', fontWeight: 700 }}>Admin Dashboard</h4>
            <span style={{ color: 'rgba(255,255,255,0.7)' }}>|</span>
            <div className="d-flex align-items-center gap-2">
              <Image
                src={profileImage}
                roundedCircle
                width={40}
                height={40}
                className="border"
                style={{ borderColor: '#fff' }}
              />
              <div>
                <h6 className="mb-0" style={{ color: '#fff', fontWeight: 600 }}>{adminData?.username}</h6>
                <small style={{ color: 'rgba(255,255,255,0.85)' }}>Admin</small>
              </div>
            </div>
          </div>
          <button
            className="btn btn-outline-danger d-flex align-items-center gap-2 logout-btn"
            onClick={handleLogout}
            style={{ background: 'rgba(255,255,255,0.12)', color: '#fff', borderColor: '#fff', fontWeight: 600 }}
          >
            <LogOut size={20} color="#fff" />
            Logout
          </button>
        </div>
      </div>

      {/* Main Content */}
      <Container fluid className="py-4">
        <div style={{
          resize: 'both',
          overflow: 'auto',
          minHeight: '300px',
          minWidth: '300px',
          maxWidth: '100%',
          maxHeight: '80vh',
          border: '1px solid #dee2e6',
          borderRadius: '0.375rem',
          padding: '1rem',
          backgroundColor: '#fff'
        }}>
          <Card className="mb-0 h-100 border-0">
            <Card.Body>
              <h4 className="mb-3" style={{ color: '#22304a', fontWeight: 700 }}>System Logs</h4>
              <Form.Group className="mb-3">
                <Form.Control
                  type="text"
                  placeholder="Search logs..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                />
              </Form.Group>

              {loading && (
                <div className="d-flex justify-content-center">
                  <Spinner animation="border" />
                </div>
              )}

              {error && <Alert variant="danger">{error}</Alert>}

              {!loading && !error && (
                <div className="table-responsive">
                  <Table striped bordered hover>
                    <thead>
                      <tr>
                        <th>Action Type</th>
                        <th>Description</th>
                        <th>Status</th>
                        <th>Timestamp</th>
                        <th>Entity Type</th>
                      </tr>
                    </thead>
                    <tbody>
                      {filteredLogs.length > 0 ? (
                        filteredLogs.map((log) => (
                          <tr key={log.logid}>
                            <td>{log.actiontype}</td>
                            <td>{log.description}</td>
                            <td>
                              <span className={`badge ${log.status === 'Success' ? 'bg-success' : 'bg-danger'}`}>
                                {log.status}
                              </span>
                            </td>
                            <td>{new Date(log.actiontimestamp).toLocaleString()}</td>
                            <td>{log.entitytype}</td>
                          </tr>
                        ))
                      ) : (
                        <tr>
                          <td colSpan="5" className="text-center">No logs found</td>
                        </tr>
                      )}
                    </tbody>
                  </Table>
                </div>
              )}
            </Card.Body>
          </Card>
        </div>
      </Container>
    </div>
  );
};

export default AdminDashboard;
