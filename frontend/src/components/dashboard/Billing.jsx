import React, { useState, useEffect, useMemo } from 'react';
import { Card, Table, InputGroup, Form, Row, Col, Badge, Button, Modal, Spinner } from 'react-bootstrap';
import { Search, CheckCircle } from 'lucide-react';

const MODES = ['Cash', 'Credit/Debit card', 'Online Transfer'];

const Billing = () => {
  const [payments, setPayments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState('All');

  // Confirm payment modal
  const [confirmPayment, setConfirmPayment] = useState(null); // the payment object
  const [mode, setMode] = useState('Cash');
  const [paymentDate, setPaymentDate] = useState(new Date().toISOString().split('T')[0]);
  const [confirming, setConfirming] = useState(false);
  const [confirmError, setConfirmError] = useState('');

  useEffect(() => {
    fetchPayments();
  }, []);

  const fetchPayments = async () => {
    setLoading(true);
    try {
      const res = await fetch('/api/payments', { credentials: 'include' });
      const data = await res.json();
      if (res.ok && data.payments) {
        setPayments(data.payments);
      }
    } catch (e) {
      console.error('Failed to load payments', e);
    } finally {
      setLoading(false);
    }
  };

  const handleConfirm = async (e) => {
    e.preventDefault();
    setConfirming(true);
    setConfirmError('');
    try {
      const res = await fetch(`/api/payments/${confirmPayment.paymentid}/confirm`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({ mode, paymentdate: paymentDate }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.message || 'Failed to confirm');
      setConfirmPayment(null);
      fetchPayments();
    } catch (e) {
      setConfirmError(e.message);
    } finally {
      setConfirming(false);
    }
  };

  const filtered = useMemo(() => payments.filter(p => {
    const matchSearch =
      (p.casename || '').toLowerCase().includes(search.toLowerCase()) ||
      (p.purpose || '').toLowerCase().includes(search.toLowerCase());
    const matchStatus = statusFilter === 'All' || p.status === statusFilter;
    return matchSearch && matchStatus;
  }), [payments, search, statusFilter]);

  const pendingCount = payments.filter(p => p.status === 'Pending').length;

  return (
    <Row className="justify-content-center py-4 px-2 px-md-4">
      <Col xs={12} xl={11}>
        {pendingCount > 0 && (
          <div style={{
            background: '#fef3c7', border: '1px solid #f59e0b', borderRadius: 10,
            padding: '10px 16px', marginBottom: 16, fontSize: 14, color: '#92400e',
            display: 'flex', alignItems: 'center', gap: 8,
          }}>
            ⚠️ You have <strong>{pendingCount}</strong> pending payment{pendingCount > 1 ? 's' : ''} awaiting confirmation.
          </div>
        )}

        <Card className="shadow-sm">
          <Card.Header className="bg-white border-bottom d-flex align-items-center gap-3">
            <h5 className="mb-0 fw-bold" style={{ color: '#22304a' }}>💰 Billing & Payments</h5>
          </Card.Header>
          <Card.Body>
            <Row className="g-2 mb-3">
              <Col md={8}>
                <InputGroup>
                  <InputGroup.Text><Search size={15} /></InputGroup.Text>
                  <Form.Control
                    placeholder="Search by case or purpose..."
                    value={search}
                    onChange={e => setSearch(e.target.value)}
                    style={{ borderRadius: '0 8px 8px 0' }}
                  />
                </InputGroup>
              </Col>
              <Col md={4}>
                <Form.Select value={statusFilter} onChange={e => setStatusFilter(e.target.value)} style={{ borderRadius: 8 }}>
                  <option value="All">All Statuses</option>
                  <option value="Pending">Pending</option>
                  <option value="Paid">Paid</option>
                </Form.Select>
              </Col>
            </Row>

            {loading ? (
              <div className="text-center py-5"><Spinner animation="border" style={{ color: '#1ec6b6' }} /></div>
            ) : (
              <div className="table-responsive" style={{ maxHeight: 460, overflowY: 'auto' }}>
                <Table hover className="align-middle mb-0">
                  <thead className="table-light sticky-top">
                    <tr>
                      <th>Case</th>
                      <th>Purpose</th>
                      <th>Type</th>
                      <th>Amount</th>
                      <th>Mode</th>
                      <th>Date</th>
                      <th>Court</th>
                      <th>Status</th>
                      <th></th>
                    </tr>
                  </thead>
                  <tbody>
                    {filtered.length === 0 ? (
                      <tr>
                        <td colSpan={9} className="text-center text-muted py-5">
                          No payments found.
                        </td>
                      </tr>
                    ) : (
                      filtered.map((p) => (
                        <tr key={p.paymentid}>
                          <td className="fw-semibold">{p.casename || '—'}</td>
                          <td>{p.purpose || '—'}</td>
                          <td>{p.paymenttype || '—'}</td>
                          <td>PKR {Number(p.balance || 0).toLocaleString()}</td>
                          <td>{p.mode || <span className="text-muted">—</span>}</td>
                          <td>{p.paymentdate || <span className="text-muted">—</span>}</td>
                          <td>{p.courtname || '—'}</td>
                          <td>
                            <Badge
                              bg={p.status === 'Paid' ? 'success' : 'warning'}
                              style={{ fontSize: 12 }}
                            >
                              {p.status}
                            </Badge>
                          </td>
                          <td>
                            {p.status === 'Pending' && (
                              <Button
                                size="sm"
                                onClick={() => {
                                  setConfirmPayment(p);
                                  setMode('Cash');
                                  setPaymentDate(new Date().toISOString().split('T')[0]);
                                  setConfirmError('');
                                }}
                                style={{
                                  background: '#1ec6b6', border: 'none',
                                  borderRadius: 6, fontSize: 12, fontWeight: 600,
                                }}
                              >
                                Confirm Payment
                              </Button>
                            )}
                            {p.status === 'Paid' && (
                              <CheckCircle size={16} style={{ color: '#16a34a' }} />
                            )}
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

        {/* Confirm Payment Modal */}
        <Modal show={!!confirmPayment} onHide={() => setConfirmPayment(null)} centered>
          <Modal.Header closeButton>
            <Modal.Title style={{ fontSize: 18, fontWeight: 700, color: '#22304a' }}>
              Confirm Payment
            </Modal.Title>
          </Modal.Header>
          <form onSubmit={handleConfirm}>
            <Modal.Body>
              {confirmError && (
                <div className="alert alert-danger py-2">{confirmError}</div>
              )}
              {confirmPayment && (
                <div style={{ background: '#f8f9fa', borderRadius: 10, padding: '12px 16px', marginBottom: 16 }}>
                  <div className="d-flex justify-content-between mb-1">
                    <span className="text-muted small">Case</span>
                    <span className="fw-semibold">{confirmPayment.casename}</span>
                  </div>
                  <div className="d-flex justify-content-between mb-1">
                    <span className="text-muted small">Purpose</span>
                    <span>{confirmPayment.purpose}</span>
                  </div>
                  <div className="d-flex justify-content-between">
                    <span className="text-muted small">Amount</span>
                    <span className="fw-bold" style={{ color: '#1ec6b6' }}>
                      PKR {Number(confirmPayment.balance || 0).toLocaleString()}
                    </span>
                  </div>
                </div>
              )}

              <Form.Group className="mb-3">
                <Form.Label className="fw-semibold" style={{ fontSize: 14 }}>Payment Method</Form.Label>
                <div className="d-flex flex-column gap-2">
                  {MODES.map(m => (
                    <label key={m} style={{
                      display: 'flex', alignItems: 'center', gap: 10,
                      padding: '10px 14px', borderRadius: 8, cursor: 'pointer',
                      border: `2px solid ${mode === m ? '#1ec6b6' : '#e5e7eb'}`,
                      background: mode === m ? '#e0f7f5' : '#fff',
                    }}>
                      <input
                        type="radio" name="mode" value={m}
                        checked={mode === m} onChange={() => setMode(m)}
                        style={{ accentColor: '#1ec6b6' }}
                      />
                      <span style={{ fontWeight: 600, fontSize: 14, color: '#22304a' }}>{m}</span>
                    </label>
                  ))}
                </div>
              </Form.Group>

              <Form.Group>
                <Form.Label className="fw-semibold" style={{ fontSize: 14 }}>Payment Date</Form.Label>
                <Form.Control
                  type="date"
                  value={paymentDate}
                  onChange={e => setPaymentDate(e.target.value)}
                  required
                  style={{ borderRadius: 8 }}
                />
              </Form.Group>
            </Modal.Body>
            <Modal.Footer>
              <Button variant="secondary" onClick={() => setConfirmPayment(null)}>Cancel</Button>
              <Button
                type="submit"
                disabled={confirming}
                style={{ background: '#1ec6b6', border: 'none', fontWeight: 600 }}
              >
                {confirming ? <Spinner size="sm" animation="border" /> : 'Mark as Paid'}
              </Button>
            </Modal.Footer>
          </form>
        </Modal>
      </Col>
    </Row>
  );
};

export default Billing;
