import React, { useState, useEffect } from 'react';
import { Card, Table, Button, Modal, Form, Spinner } from 'react-bootstrap';

function normalizeWitnessesResponse(data) {
  const list = Array.isArray(data) ? data : data?.witnesses || [];
  const rows = [];

  list.forEach((item) => {
    const w = item.witness || item;
    if (!w) return;

    const cases = item.cases || [];
    if (cases.length === 0) {
      rows.push({
        id: w.id ?? w.witnessid,
        firstName: w.firstname || w.firstName || '',
        lastName: w.lastname || w.lastName || '',
        cnic: w.cnic || '',
        phone: w.phone || '',
        email: w.email || '',
        address: w.address || '',
        pasthistory: w.pasthistory || '',
        caseName: item.case_id ? `Case #${item.case_id}` : 'N/A',
        statement: item.statement || '',
        statementDate: item.statementdate || item.statementDate || '',
      });
      return;
    }

    cases.forEach((c) => {
      rows.push({
        id: `${w.id ?? w.witnessid}-${c.caseid}`,
        firstName: w.firstname || w.firstName || '',
        lastName: w.lastname || w.lastName || '',
        cnic: w.cnic || '',
        phone: w.phone || '',
        email: w.email || '',
        address: w.address || '',
        pasthistory: w.pasthistory || '',
        caseName: c.title || (c.caseid ? `Case #${c.caseid}` : 'N/A'),
        statement: c.statement || item.statement || '',
        statementDate: c.statementdate || item.statementdate || '',
      });
    });
  });

  return rows;
}

const Witnesses = () => {
  const [show, setShow] = useState(false);
  const [form, setForm] = useState({
    firstName: '', lastName: '', cnic: '', phone: '',
    email: '', address: '', pasthistory: '',
    caseName: '', statement: '', statementDate: ''
  });
  const [witnesses, setWitnesses] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    setLoading(true);
    fetch('/api/witnesses', {
      method: 'GET',
      credentials: 'include',
      headers: { 'Content-Type': 'application/json' },
    })
      .then(async (response) => {
        if (!response.ok) {
          const err = await response.json().catch(() => ({}));
          throw new Error(err.message || 'Failed to fetch witnesses');
        }
        return response.json();
      })
      .then((data) => {
        setWitnesses(normalizeWitnessesResponse(data));
        setError('');
      })
      .catch((err) => {
        console.error('Error fetching witnesses:', err);
        setError(err.message);
        setWitnesses([]);
      })
      .finally(() => setLoading(false));
  }, []);

  const handleChange = e => setForm({ ...form, [e.target.name]: e.target.value });

  const handleSubmit = e => {
    e.preventDefault();
    setWitnesses([{ ...form, id: Date.now() }, ...witnesses]);
    setShow(false);
  };

  return (
    <div className="container py-4">
      <Card className="shadow mb-4">
        <Card.Header as="h5" className="d-flex justify-content-between align-items-center">
          Witnesses
          <Button variant="primary" onClick={() => setShow(true)}>Add Witness</Button>
        </Card.Header>
        <Card.Body>
          {error && <div className="text-danger mb-2">{error}</div>}
          {loading ? (
            <div className="text-center py-4">
              <Spinner animation="border" variant="primary" />
            </div>
          ) : (
            <Table bordered hover>
              <thead className="table-light">
                <tr>
                  <th>First Name</th>
                  <th>Last Name</th>
                  <th>CNIC</th>
                  <th>Phone</th>
                  <th>Email</th>
                  <th>Address</th>
                  <th>Past History</th>
                  <th>Case Name</th>
                  <th>Statement</th>
                  <th>Statement Date</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {witnesses.length === 0 ? (
                  <tr>
                    <td colSpan={11} className="text-center text-muted py-4">
                      No witnesses found.
                    </td>
                  </tr>
                ) : (
                  witnesses.map(w => (
                    <tr key={w.id}>
                      <td>{w.firstName}</td>
                      <td>{w.lastName}</td>
                      <td>{w.cnic}</td>
                      <td>{w.phone}</td>
                      <td>{w.email}</td>
                      <td>{w.address}</td>
                      <td>{w.pasthistory}</td>
                      <td>{w.caseName}</td>
                      <td>{w.statement}</td>
                      <td>{w.statementDate}</td>
                      <td>
                        <Button size="sm" variant="primary" className="me-1">Edit</Button>
                        <Button size="sm" variant="info" className="me-1">View</Button>
                        <Button size="sm" variant="secondary">Download</Button>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </Table>
          )}
        </Card.Body>
      </Card>
      <Modal show={show} onHide={() => setShow(false)} centered>
        <Modal.Header closeButton><Modal.Title>Add Witness</Modal.Title></Modal.Header>
        <Form onSubmit={handleSubmit}>
          <Modal.Body>
            <p className="text-muted small mb-0">Add witness via a case detail screen (coming soon).</p>
          </Modal.Body>
          <Modal.Footer>
            <Button variant="secondary" onClick={() => setShow(false)}>Cancel</Button>
            <Button variant="primary" type="submit">Submit</Button>
          </Modal.Footer>
        </Form>
      </Modal>
    </div>
  );
};

export default Witnesses;
