import React, { useState, useEffect, useRef } from 'react';
import { Modal, Button, Form, Badge, Spinner } from 'react-bootstrap';
import { UploadCloud, Download, Trash2, FileText, Lock, Users, Globe } from 'lucide-react';

const DOC_TYPES = ['Evidence', 'Medical Report', 'Court Order', 'Legal Notice', 'Petition', 'Affidavit', 'Other'];

const VIS_CONFIG = {
  court:   { label: 'Everyone on Case', icon: <Globe size={13} />,  color: '#1ec6b6', bg: '#e0f7f5' },
  team:    { label: 'Lawyers & Clients', icon: <Users size={13} />, color: '#f59e0b', bg: '#fef3c7' },
  private: { label: 'Private (Only Me)', icon: <Lock size={13} />,  color: '#6b7280', bg: '#f3f4f6' },
};

export default function CaseDocuments({ cases = [], userRole = '' }) {
  const [selectedCaseId, setSelectedCaseId] = useState('');
  const [documents, setDocuments] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  // Upload modal state
  const [showUpload, setShowUpload] = useState(false);
  const [uploadFile, setUploadFile] = useState(null);
  const [uploadType, setUploadType] = useState('Evidence');
  const [uploadVis, setUploadVis] = useState('court');
  const [uploading, setUploading] = useState(false);
  const [uploadError, setUploadError] = useState('');
  const fileRef = useRef();

  // Delete confirm
  const [deleteId, setDeleteId] = useState(null);
  const [deleting, setDeleting] = useState(false);

  const isJudge = userRole === 'Judge';

  useEffect(() => {
    if (cases.length > 0 && !selectedCaseId) {
      setSelectedCaseId(String(cases[0].id || cases[0].caseid || ''));
    }
  }, [cases]);

  useEffect(() => {
    if (!selectedCaseId) return;
    fetchDocs();
  }, [selectedCaseId]);

  const fetchDocs = async () => {
    setLoading(true);
    setError('');
    try {
      const res = await fetch(`/api/cases/${selectedCaseId}/documents`, {
        credentials: 'include',
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.error || 'Failed to load');
      setDocuments(data.documents || []);
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  const handleUpload = async (e) => {
    e.preventDefault();
    if (!uploadFile) { setUploadError('Please select a file.'); return; }
    setUploading(true);
    setUploadError('');
    try {
      const fd = new FormData();
      fd.append('file', uploadFile);
      fd.append('documenttype', uploadType);
      fd.append('visibility', uploadVis);

      const res = await fetch(`/api/cases/${selectedCaseId}/documents`, {
        method: 'POST',
        credentials: 'include',
        body: fd,
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.error || 'Upload failed');
      setShowUpload(false);
      setUploadFile(null);
      setUploadType('Evidence');
      setUploadVis('court');
      fetchDocs();
    } catch (e) {
      setUploadError(e.message);
    } finally {
      setUploading(false);
    }
  };

  const handleDelete = async () => {
    setDeleting(true);
    try {
      const res = await fetch(`/api/cases/${selectedCaseId}/documents/${deleteId}`, {
        method: 'DELETE',
        credentials: 'include',
      });
      if (!res.ok) {
        const d = await res.json();
        throw new Error(d.error || 'Delete failed');
      }
      setDeleteId(null);
      fetchDocs();
    } catch (e) {
      alert(e.message);
    } finally {
      setDeleting(false);
    }
  };

  const handleDownload = (docId, title) => {
    window.open(`/api/documents/${docId}/download`, '_blank');
  };

  const selectedCase = cases.find(c => String(c.id || c.caseid) === selectedCaseId);

  return (
    <div style={{ padding: '0 0 24px 0' }}>
      {/* Header row */}
      <div className="d-flex align-items-center justify-content-between mb-3 flex-wrap gap-2">
        <div className="d-flex align-items-center gap-3 flex-wrap">
          <h5 className="mb-0 fw-bold" style={{ color: '#22304a' }}>Documents</h5>
          {cases.length > 1 && (
            <Form.Select
              size="sm"
              value={selectedCaseId}
              onChange={e => setSelectedCaseId(e.target.value)}
              style={{ width: 220, borderRadius: 8, borderColor: '#e5e7eb' }}
            >
              {cases.map(c => (
                <option key={c.id || c.caseid} value={String(c.id || c.caseid)}>
                  {c.title || `Case #${c.id || c.caseid}`}
                </option>
              ))}
            </Form.Select>
          )}
          {cases.length === 1 && selectedCase && (
            <span style={{ color: '#6b7280', fontSize: 14 }}>{selectedCase.title}</span>
          )}
        </div>
        {selectedCaseId && (
          <Button
            size="sm"
            onClick={() => setShowUpload(true)}
            style={{ background: '#1ec6b6', border: 'none', borderRadius: 8, fontWeight: 600 }}
          >
            <UploadCloud size={14} className="me-1" /> Upload Document
          </Button>
        )}
      </div>

      {/* Visibility legend */}
      <div className="d-flex gap-3 mb-3 flex-wrap">
        {Object.entries(VIS_CONFIG).map(([key, v]) => (
          <span key={key} style={{ fontSize: 12, display: 'flex', alignItems: 'center', gap: 4, color: v.color }}>
            {v.icon} {v.label}
          </span>
        ))}
      </div>

      {/* Document list */}
      {!selectedCaseId ? (
        <p className="text-muted">Select a case to view documents.</p>
      ) : loading ? (
        <div className="text-center py-4"><Spinner animation="border" size="sm" style={{ color: '#1ec6b6' }} /></div>
      ) : error ? (
        <div className="alert alert-danger py-2">{error}</div>
      ) : documents.length === 0 ? (
        <div className="text-center text-muted py-5">
          <FileText size={36} style={{ marginBottom: 8, opacity: 0.3 }} />
          <div>No documents uploaded for this case yet.</div>
        </div>
      ) : (
        <div className="d-flex flex-column gap-2">
          {documents.map(doc => {
            const vis = VIS_CONFIG[doc.visibility] || VIS_CONFIG.court;
            return (
              <div key={doc.id} style={{
                background: '#fff', border: '1px solid #e5e7eb', borderRadius: 10,
                padding: '12px 16px', display: 'flex', alignItems: 'center',
                justifyContent: 'space-between', gap: 12, flexWrap: 'wrap',
              }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 10, flex: 1, minWidth: 0 }}>
                  <FileText size={20} style={{ color: '#1ec6b6', flexShrink: 0 }} />
                  <div style={{ minWidth: 0 }}>
                    <div className="fw-semibold text-truncate" style={{ color: '#22304a', fontSize: 14 }}>
                      {doc.title}
                    </div>
                    <div style={{ fontSize: 12, color: '#9ca3af' }}>
                      {doc.type} · {doc.uploaddate ? doc.uploaddate.split('T')[0] : '—'}
                      {doc.uploader_name ? ` · ${doc.uploader_name}` : ''}
                    </div>
                  </div>
                </div>
                <div className="d-flex align-items-center gap-2">
                  <span style={{
                    fontSize: 11, fontWeight: 600, padding: '3px 8px', borderRadius: 20,
                    background: vis.bg, color: vis.color,
                    display: 'flex', alignItems: 'center', gap: 4,
                  }}>
                    {vis.icon} {vis.label}
                  </span>
                  <Button
                    size="sm"
                    variant="outline-secondary"
                    onClick={() => handleDownload(doc.id, doc.title)}
                    style={{ borderRadius: 6, padding: '3px 8px' }}
                    title="Download"
                  >
                    <Download size={13} />
                  </Button>
                  {doc.is_own && (
                    <Button
                      size="sm"
                      variant="outline-danger"
                      onClick={() => setDeleteId(doc.id)}
                      style={{ borderRadius: 6, padding: '3px 8px' }}
                      title="Delete"
                    >
                      <Trash2 size={13} />
                    </Button>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Upload Modal */}
      <Modal show={showUpload} onHide={() => { setShowUpload(false); setUploadError(''); }} centered>
        <Modal.Header closeButton>
          <Modal.Title style={{ fontSize: 18, fontWeight: 700, color: '#22304a' }}>Upload Document</Modal.Title>
        </Modal.Header>
        <form onSubmit={handleUpload}>
          <Modal.Body>
            {uploadError && <div className="alert alert-danger py-2">{uploadError}</div>}

            <Form.Group className="mb-3">
              <Form.Label className="fw-semibold" style={{ fontSize: 14 }}>File</Form.Label>
              <div
                onClick={() => fileRef.current?.click()}
                style={{
                  border: '2px dashed #1ec6b6', borderRadius: 10, padding: '20px',
                  textAlign: 'center', cursor: 'pointer', background: '#f0fdfb',
                }}
              >
                <UploadCloud size={24} style={{ color: '#1ec6b6', marginBottom: 6 }} />
                <div style={{ fontSize: 13, color: '#6b7280' }}>
                  {uploadFile ? uploadFile.name : 'Click to choose a file'}
                </div>
                <div style={{ fontSize: 11, color: '#9ca3af', marginTop: 4 }}>
                  PDF, DOC, DOCX, JPG, PNG, TXT, XLSX
                </div>
              </div>
              <input
                type="file"
                ref={fileRef}
                style={{ display: 'none' }}
                accept=".pdf,.doc,.docx,.jpg,.jpeg,.png,.txt,.xlsx,.xls"
                onChange={e => setUploadFile(e.target.files[0] || null)}
              />
            </Form.Group>

            <Form.Group className="mb-3">
              <Form.Label className="fw-semibold" style={{ fontSize: 14 }}>Document Type</Form.Label>
              <Form.Select value={uploadType} onChange={e => setUploadType(e.target.value)} style={{ borderRadius: 8 }}>
                {DOC_TYPES.map(t => <option key={t}>{t}</option>)}
              </Form.Select>
            </Form.Group>

            <Form.Group>
              <Form.Label className="fw-semibold" style={{ fontSize: 14 }}>Who can see this?</Form.Label>
              <div className="d-flex flex-column gap-2 mt-1">
                {Object.entries(VIS_CONFIG).map(([key, v]) => {
                  // Judges can't use 'team' visibility
                  if (isJudge && key === 'team') return null;
                  return (
                    <label
                      key={key}
                      style={{
                        display: 'flex', alignItems: 'center', gap: 10,
                        padding: '10px 14px', borderRadius: 10, cursor: 'pointer',
                        border: `2px solid ${uploadVis === key ? v.color : '#e5e7eb'}`,
                        background: uploadVis === key ? v.bg : '#fff',
                        transition: 'all 0.15s',
                      }}
                    >
                      <input
                        type="radio" name="visibility" value={key}
                        checked={uploadVis === key}
                        onChange={() => setUploadVis(key)}
                        style={{ accentColor: v.color }}
                      />
                      <span style={{ color: v.color }}>{v.icon}</span>
                      <div>
                        <div style={{ fontWeight: 600, fontSize: 13, color: '#22304a' }}>{v.label}</div>
                        <div style={{ fontSize: 11, color: '#9ca3af' }}>
                          {key === 'court' && 'Judge, lawyers, registrar, and clients on this case'}
                          {key === 'team' && 'Only lawyers and clients on this case (not judge or registrar)'}
                          {key === 'private' && 'Only you can see this document'}
                        </div>
                      </div>
                    </label>
                  );
                })}
              </div>
            </Form.Group>
          </Modal.Body>
          <Modal.Footer>
            <Button variant="secondary" onClick={() => { setShowUpload(false); setUploadError(''); }}>Cancel</Button>
            <Button
              type="submit" disabled={uploading}
              style={{ background: '#1ec6b6', border: 'none', fontWeight: 600 }}
            >
              {uploading ? <Spinner size="sm" animation="border" /> : 'Upload'}
            </Button>
          </Modal.Footer>
        </form>
      </Modal>

      {/* Delete confirm */}
      <Modal show={!!deleteId} onHide={() => setDeleteId(null)} centered size="sm">
        <Modal.Body className="text-center p-4">
          <Trash2 size={32} style={{ color: '#ef4444', marginBottom: 12 }} />
          <div className="fw-bold mb-2">Delete this document?</div>
          <div style={{ fontSize: 13, color: '#6b7280', marginBottom: 20 }}>This cannot be undone.</div>
          <div className="d-flex gap-2 justify-content-center">
            <Button variant="secondary" size="sm" onClick={() => setDeleteId(null)}>Cancel</Button>
            <Button
              size="sm" disabled={deleting}
              style={{ background: '#ef4444', border: 'none' }}
              onClick={handleDelete}
            >
              {deleting ? <Spinner size="sm" animation="border" /> : 'Delete'}
            </Button>
          </div>
        </Modal.Body>
      </Modal>
    </div>
  );
}
