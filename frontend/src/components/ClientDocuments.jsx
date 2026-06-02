import React, { useState, useEffect, useRef } from 'react';
import { Card, Row, Col, ListGroup, Button, Badge, Modal, Form, Spinner, Alert } from 'react-bootstrap';
import { Eye, UploadCloud } from 'lucide-react';

const categories = ['Legal Documents', 'Evidence', 'Statements'];

function ClientDocuments() {
  const [documents, setDocuments] = useState([]);
  const [selectedCategory, setSelectedCategory] = useState('Legal Documents');
  { /*
Removed the add document functionality for client, uncomment if needed
  const [showAddModal, setShowAddModal] = useState(false);
  const [addTitle, setAddTitle] = useState('');
  const [addFile, setAddFile] = useState(null);
  const [addLoading, setAddLoading] = useState(false);
  const fileInputRef = useRef();
  */ }
  const [showViewModal, setShowViewModal] = useState(false);
  const [viewDoc, setViewDoc] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchDocuments = async () => {
      setLoading(true);
      setError(null);
      try {
        const res = await fetch('/api/clientdocuments', {
          method: 'GET',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${localStorage.getItem('userToken')}`,
          },
          credentials: 'include',
        });

        const result = await res.json();
        if (!res.ok || result.success === false) {
          throw new Error(result.message || 'Failed to fetch documents');
        }

        const docs = result.documents || result.data || [];

        // Normalize backend fields to frontend keys
        const normalizedDocs = docs.map(doc => ({
          id: doc.documentid || doc.id,
          title: doc.documenttitle || doc.title,
          documenttype: doc.documenttype || doc.category || 'Legal Documents',
          uploadDate: doc.uploaddate || doc.uploadDate || '',
          size: doc.size || '',
          type: doc.documenttype || doc.type || '',
          path: doc.filepath || doc.path || '',
          fileType: doc.filetype || doc.fileType || '',

          // Extra fields for view modal (optional)
          evidenceType: doc.evidencetype,
          description: doc.description,
          date: doc.date,
          caseName: doc.casename,
          firstName: doc.firstname,
          lastName: doc.lastname,
          cnic: doc.cnic,
          phone: doc.phone,
          email: doc.email,
          pastHistory: doc.pasthistory,
          statement: doc.statement,
        }));

        setDocuments(normalizedDocs);
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };

    fetchDocuments();
  }, []);

  // Filter using documenttype field
  const filteredDocuments = documents.filter(doc => doc.documenttype === selectedCategory);

  {/* uncomment if wanted to add the document upload functionality
  const handleAddDocument = async (e) => {
    e.preventDefault();
    if (!addTitle || !addFile) return;
    setAddLoading(true);
    // Simulated upload - replace with real upload logic
    setTimeout(() => {
      const fileType = addFile.type.startsWith('image')
        ? 'image'
        : addFile.type === 'application/pdf'
        ? 'pdf'
        : 'file';

      const newDoc = {
        id: Date.now(),
        title: addTitle,
        documenttype: 'Legal Documents',
        uploadDate: new Date().toISOString().split('T')[0],
        size: `${(addFile.size / 1024 / 1024).toFixed(1)} MB`,
        type: addFile.name.split('.').pop().toUpperCase(),
        path: URL.createObjectURL(addFile),
        fileType,
      };

      setDocuments(prevDocs => [newDoc, ...prevDocs]);
      setAddTitle('');
      setAddFile(null);
      setAddLoading(false);
      setShowAddModal(false);
      if (fileInputRef.current) fileInputRef.current.value = '';
    }, 1000);
  };
*/ }

  const handleView = (doc) => {
    setViewDoc(doc);
    setShowViewModal(true);
  };

  return (
    <Row className="h-100 g-4 justify-content-center align-items-start">
      <Col md={3} className="d-flex flex-column">
        <Card className="shadow-sm rounded-4 w-100 flex-grow-1 mb-0">
          <Card.Body className="p-4">
            <h4 className="mb-4">Categories</h4>
            <ListGroup>
              {categories.map(category => (
                <ListGroup.Item
                  key={category}
                  action
                  active={selectedCategory === category}
                  onClick={() => setSelectedCategory(category)}
                  className="border-0 mb-2 rounded"
                >
                  {category}
                </ListGroup.Item>
              ))}
            </ListGroup> 
            { /* Remove add Legal document button */ }
{ /* Uncomment if you want to add the button back */ }
            { /* { selectedCategory === 'Legal Documents' && (
              <Button
                variant="primary"
                className="mt-4 w-100 d-flex align-items-center gap-2"
                onClick={() => setShowAddModal(true)}
              >
                <UploadCloud size={18} /> Add Legal Document
              </Button>
            )} */ }
          </Card.Body>
        </Card>
      </Col>

      <Col md={9} className="d-flex flex-column">
        <Card className="shadow-sm rounded-4 w-100 flex-grow-1 mb-0">
          <Card.Body className="p-4">
            <h4 className="mb-4">Documents</h4>

            {loading && (
              <div className="text-center my-5">
                <Spinner animation="border" />
              </div>
            )}

            {error && (
              <Alert variant="danger" className="my-3">
                {error}
              </Alert>
            )}

            {!loading && !error && (
              <div className="table-responsive" style={{ maxHeight: 'calc(100vh - 250px)', overflowY: 'auto' }}>
                <table className="table table-hover align-middle mb-0">
                  <thead className="table-light sticky-top">
                    <tr>
                      <th>Title</th>
                      <th>Type</th>
                      <th>Upload Date</th>
                      <th>Size</th>
                      <th>Document Type</th>
                      <th>Action</th>
                    </tr>
                  </thead>
                  <tbody>
                    {filteredDocuments.length === 0 ? (
                      <tr>
                        <td colSpan={6} className="text-center text-muted py-4">
                          No documents found in this category.
                        </td>
                      </tr>
                    ) : (
                      filteredDocuments.map(doc => (
                        <tr key={doc.id}>
                          <td>{doc.title}</td>
                          <td><Badge bg="info">{doc.type}</Badge></td>
                          <td>{doc.uploadDate}</td>
                          <td>{doc.size}</td>
                          <td><Badge bg="secondary">{doc.documenttype}</Badge></td>
                          <td>
                            <Button
                              variant="outline-primary"
                              size="sm"
                              onClick={() => handleView(doc)}
                            >
                              <Eye size={16} className="me-1" /> View
                            </Button>
                          </td>
                        </tr>
                      ))
                    )}
                  </tbody>
                </table>
              </div>
            )}
          </Card.Body>
        </Card>
      </Col>
      {/* Legal Document Modal Removed for client, uncomment if needed */}
      {/*
      <Modal show={showAddModal} onHide={() => setShowAddModal(false)} centered>
        <Modal.Header closeButton>
          <Modal.Title>Add Legal Document</Modal.Title>
        </Modal.Header>
        <Form onSubmit={handleAddDocument}>
          <Modal.Body>
            <Form.Group className="mb-3">
              <Form.Label>Title</Form.Label>
              <Form.Control
                type="text"
                value={addTitle}
                onChange={e => setAddTitle(e.target.value)}
                required
              />
            </Form.Group>
            <Form.Group className="mb-3">
              <Form.Label>File Upload</Form.Label>
              <Form.Control
                type="file"
                accept=".pdf,.doc,.docx,.txt,.jpg,.jpeg,.png"
                onChange={e => setAddFile(e.target.files[0])}
                ref={fileInputRef}
                required
              />
            </Form.Group>
          </Modal.Body>
          <Modal.Footer>
            <Button variant="secondary" onClick={() => setShowAddModal(false)} disabled={addLoading}>Cancel</Button>
            <Button variant="primary" type="submit" disabled={addLoading}>
              {addLoading ? <Spinner size="sm" animation="border" /> : 'Add Document'}
            </Button>
          </Modal.Footer>
        </Form>
      </Modal>
      */}

      {/* View Document Modal */}
      <Modal show={showViewModal} onHide={() => setShowViewModal(false)} centered size="lg">
        <Modal.Header closeButton>
          <Modal.Title>View Document</Modal.Title>
        </Modal.Header>
        <Modal.Body>
          {viewDoc && (
            <div>
              {viewDoc.documenttype === 'Evidence' ? (
                <>
                  <div className="mb-3"><strong>Evidence Type:</strong> {viewDoc.evidenceType}</div>
                  <div className="mb-3"><strong>Description:</strong> {viewDoc.description}</div>
                  <div className="mb-3"><strong>Date:</strong> {viewDoc.date}</div>
                  <div className="mb-3"><strong>Case Name:</strong> {viewDoc.caseName}</div>
                </>
              ) : viewDoc.documenttype === 'Statements' ? (
                <>
                  <div className="mb-3"><strong>First Name:</strong> {viewDoc.firstName}</div>
                  <div className="mb-3"><strong>Last Name:</strong> {viewDoc.lastName}</div>
                  <div className="mb-3"><strong>CNIC:</strong> {viewDoc.cnic}</div>
                  <div className="mb-3"><strong>Phone:</strong> {viewDoc.phone}</div>
                  <div className="mb-3"><strong>Email Address:</strong> {viewDoc.email}</div>
                  <div className="mb-3"><strong>Past History:</strong> {viewDoc.pastHistory}</div>
                  <div className="mb-3"><strong>Statement:</strong> {viewDoc.statement}</div>
                  <div className="mb-3"><strong>Case Name:</strong> {viewDoc.caseName}</div>
                  <div className="mb-3"><strong>Date:</strong> {viewDoc.date}</div>
                </>
              ) : (
                <>
                  <div className="mb-3"><strong>Title:</strong> {viewDoc.title}</div>
                  <div className="mb-3"><strong>Upload Date:</strong> {viewDoc.uploadDate}</div>
                  <div className="mb-3"><strong>Type:</strong> {viewDoc.type}</div>
                  <div className="mb-3"><strong>Size:</strong> {viewDoc.size}</div>
                </>
              )}

              {viewDoc.fileType === 'image' ? (
                <div className="text-center">
                  <img src={viewDoc.path} alt={viewDoc.title} style={{ maxWidth: '100%', maxHeight: 400, borderRadius: 8 }} />
                </div>
              ) : viewDoc.fileType === 'pdf' ? (
                <div className="text-center">
                  <iframe src={viewDoc.path} title="PDF Preview" width="100%" height="400px" style={{ border: 'none', borderRadius: 8 }}></iframe>
                  <div className="mt-2">
                    <a href={viewDoc.path} target="_blank" rel="noopener noreferrer" className="btn btn-outline-primary btn-sm">Open in new tab</a>
                  </div>
                </div>
              ) : (
                <div className="text-center">
                  <a href={viewDoc.path} target="_blank" rel="noopener noreferrer" className="btn btn-outline-primary">Download File</a>
                </div>
              )}
            </div>
          )}
        </Modal.Body>
        <Modal.Footer>
          <Button variant="secondary" onClick={() => setShowViewModal(false)}>Close</Button>
        </Modal.Footer>
      </Modal>
    </Row>
  );
}

export default ClientDocuments;
