import React, { useState, useRef, useEffect } from 'react';
import { Container, Row, Col, Card, Form, Button, Image } from 'react-bootstrap';
import { Mail, Phone, MapPin, Briefcase, Award, Upload, User } from 'lucide-react';

const PROFILE_IMAGE_KEY = 'judgeProfileImage';

const JudgeProfile = () => {
  const [isEditing, setIsEditing] = useState(false);
  const [profileImage, setProfileImage] = useState(null);
  const fileInputRef = useRef(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const [profileData, setProfileData] = useState({
    firstName: '',
    lastName: '',
    name: '',
    email: '',
    phone: '',
    specialization: '',
    cnic: '',
    dob: '',
    position: '',
    experience: '',
  });

  useEffect(() => {
    const storedImage = localStorage.getItem(PROFILE_IMAGE_KEY);
    if (storedImage) setProfileImage(storedImage);

    const fetchProfile = async () => {
      try {
        const res = await fetch('/api/judgeprofile', {
          method: 'GET',
          headers: { 'Content-Type': 'application/json' },
          credentials: 'include',
        });

        const result = await res.json();
        if (!res.ok || !result.success) throw new Error(result.message || 'Failed to load profile');

        const data = result.data;
        setProfileData({
          firstName: data.firstName || '',
          lastName: data.lastName || '',
          name: data.firstName + " " + data.lastName|| '',
          email: data.email || '',
          phone: data.phone || '',
          specialization: data.specialization || '',
          cnic: data.cnic || '',
          dob: data.dob || '',
          position: data.position || '',
          experience: data.experience || '',
        });
      } catch (err) {
        setError(null);
        setProfileData({
          firstName: 'Mock',
          lastName: 'Judge',
          name: 'Hon. Mock Judge',
          email: 'mockjudge@email.com',
          phone: '123-456-7890',
          specialization: 'Criminal Law',
          cnic: '12345-6789012-3',
          dob: '1970-01-01',
          position: 'Senior Judge',
          experience: '15',
        });
        setProfileImage('https://via.placeholder.com/150');
        setLoading(false);
      } finally {
        setLoading(false);
      }
    };

    fetchProfile();
  }, []);

  const handleEdit = () => setIsEditing(!isEditing);

  const handleSave = async () => {
    try {
      const res = await fetch('/api/judgeprofile', {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify(profileData),
      });

      const result = await res.json();
      if (!res.ok || !result.success) throw new Error(result.message || 'Failed to update profile');

      setIsEditing(false);
    } catch (err) {
      alert(err.message);
    }
  };

  const handleImageUpload = (event) => {
    const file = event.target.files[0];
    if (file) {
      const reader = new FileReader();
      reader.onloadend = () => {
        setProfileImage(reader.result);
        localStorage.setItem(PROFILE_IMAGE_KEY, reader.result);
      };
      reader.readAsDataURL(file);
    }
  };

  const triggerImageUpload = () => fileInputRef.current.click();

  if (loading) return <div className="text-center mt-5">Loading profile...</div>;
  if (error) return <div className="alert alert-danger mt-5">{error}</div>;

  return (
    <div
      style={{
        minHeight: '100vh',
        background: 'linear-gradient(120deg, #f8f9fa 0%, #e9ecef 100%)',
        padding: '2rem 1rem',
        overflowY: 'auto',
      }}
    >
      <Container fluid className="p-0">
        <Row className="g-4">
          {/* Profile Header */}
          <Col xs={12} md={6} lg={4}>
            <Card className="shadow-sm h-100" style={{ 
              borderRadius: '1.5rem',
              border: '1px solid rgba(255,255,255,0.18)',
              background: 'white',
              padding: '1.2em 0.8em 1em 0.8em',
              minWidth: 0
            }}>
              <Card.Body className="text-center">
                <div className="position-relative d-inline-block mb-3">
                  <Image
                    src={profileImage || 'https://via.placeholder.com/150'}
                    roundedCircle
                    width={110}
                    height={110}
                    className="border border-4"
                    style={{ 
                      objectFit: 'cover',
                      borderColor: '#1ec6b6 !important'
                    }}
                  />
                  {isEditing && (
                    <Button
                      variant="primary"
                      size="sm"
                      className="position-absolute bottom-0 end-0 rounded-circle"
                      style={{ 
                        width: '28px', 
                        height: '28px',
                        background: 'linear-gradient(90deg, #22304a 0%, #1ec6b6 100%)',
                        border: 'none',
                        boxShadow: '0 4px 12px rgba(30,198,182,0.15)'
                      }}
                      onClick={triggerImageUpload}
                    >
                      <Upload size={14} />
                    </Button>
                  )}
                  <input
                    type="file"
                    ref={fileInputRef}
                    onChange={handleImageUpload}
                    accept="image/*"
                    className="d-none"
                  />
                </div>
                <h4 className="mb-1 gradient-text" style={{
                  background: 'linear-gradient(90deg, #22304a 0%, #1ec6b6 100%)',
                  WebkitBackgroundClip: 'text',
                  WebkitTextFillColor: 'transparent',
                  backgroundClip: 'text',
                  textFillColor: 'transparent',
                  fontSize: '1.3rem',
                }}>
                  {profileData.name || `${profileData.firstName} ${profileData.lastName}`}
                </h4>
                <p className="text-muted mb-2" style={{ fontSize: '0.97rem' }}>{profileData.specialization}</p>
                <div className="d-flex justify-content-center gap-2 mb-2">
                  <Button 
                    variant="outline-primary" 
                    size="sm"
                    style={{
                      borderColor: '#1ec6b6',
                      color: '#1ec6b6',
                      borderRadius: '0.75rem',
                      fontSize: '0.97rem',
                      padding: '0.3rem 0.7rem'
                    }}
                  >
                    <Mail size={14} className="me-1" /> Email
                  </Button>
                  <Button 
                    variant="outline-primary" 
                    size="sm"
                    style={{
                      borderColor: '#1ec6b6',
                      color: '#1ec6b6',
                      borderRadius: '0.75rem',
                      fontSize: '0.97rem',
                      padding: '0.3rem 0.7rem'
                    }}
                  >
                    <Phone size={14} className="me-1" /> Call
                  </Button>
                </div>
                <hr />
                <div className="text-start">
                  <p className="mb-2">
                    <MapPin size={14} className="me-2" style={{ color: '#1ec6b6' }} />
                    Position: {profileData.position}
                  </p>
                  <p className="mb-2">
                    <Briefcase size={14} className="me-2" style={{ color: '#1ec6b6' }} />
                    {profileData.experience} Years Experience
                  </p>
                  <p className="mb-0">
                    <Award size={14} className="me-2" style={{ color: '#1ec6b6' }} />
                    Specialization: {profileData.specialization}
                  </p>
                </div>
              </Card.Body>
            </Card>
          </Col>

          {/* Profile Details */}
          <Col xs={12} md={6} lg={8}>
            <Card className="shadow-sm mb-4" style={{ 
              borderRadius: '1.5rem',
              border: '1px solid rgba(255,255,255,0.18)',
              background: 'white',
              padding: '1.2em 0.8em 1em 0.8em',
              minWidth: 0
            }}>
              <Card.Body>
                <div className="d-flex justify-content-between align-items-center mb-3">
                  <h5 className="mb-0 fw-bold gradient-text" style={{ color: '#22304a', fontSize: '1.1rem', background: 'linear-gradient(90deg, #22304a 0%, #1ec6b6 100%)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent', backgroundClip: 'text', textFillColor: 'transparent' }}>Professional Information</h5>
                  <Button
                    variant={isEditing ? 'success' : 'outline-primary'}
                    size="sm"
                    onClick={isEditing ? handleSave : handleEdit}
                    style={{
                      background: isEditing ? 'linear-gradient(90deg, #22304a 0%, #1ec6b6 100%)' : 'transparent',
                      borderColor: '#1ec6b6',
                      color: isEditing ? 'white' : '#1ec6b6',
                      borderRadius: '0.75rem',
                      fontWeight: '600',
                      boxShadow: isEditing ? '0 4px 12px rgba(30,198,182,0.15)' : 'none',
                      fontSize: '0.97rem',
                      padding: '0.3rem 0.7rem'
                    }}
                  >
                    {isEditing ? 'Save Changes' : 'Edit Profile'}
                  </Button>
                </div>
                <Form>
                  <Row className="g-2">
                    <Col md={6}>
                      <Form.Group>
                        <Form.Label className="fw-bold" style={{ fontSize: '0.97rem' }}>First Name</Form.Label>
                        <Form.Control
                          type="text"
                          value={profileData.firstName}
                          disabled={!isEditing}
                          onChange={(e) =>
                            setProfileData({ ...profileData, firstName: e.target.value })
                          }
                          style={{ 
                            borderRadius: '0.75rem',
                            padding: '0.5rem 0.75rem',
                            border: '1px solid rgba(30,198,182,0.2)',
                            fontSize: '0.97rem'
                          }}
                        />
                      </Form.Group>
                    </Col>
                    <Col md={6}>
                      <Form.Group>
                        <Form.Label className="fw-bold" style={{ fontSize: '0.97rem' }}>Last Name</Form.Label>
                        <Form.Control
                          type="text"
                          value={profileData.lastName}
                          disabled={!isEditing}
                          onChange={(e) =>
                            setProfileData({ ...profileData, lastName: e.target.value })
                          }
                          style={{ 
                            borderRadius: '0.75rem',
                            padding: '0.5rem 0.75rem',
                            border: '1px solid rgba(30,198,182,0.2)',
                            fontSize: '0.97rem'
                          }}
                        />
                      </Form.Group>
                    </Col>
                    <Col md={6}>
                      <Form.Group>
                        <Form.Label className="fw-bold" style={{ fontSize: '0.97rem' }}>Full Name</Form.Label>
                        <Form.Control
                          type="text"
                          value={profileData.name}
                          disabled={!isEditing}
                          onChange={(e) =>
                            setProfileData({ ...profileData, name: e.target.value })
                          }
                          style={{ 
                            borderRadius: '0.75rem',
                            padding: '0.5rem 0.75rem',
                            border: '1px solid rgba(30,198,182,0.2)',
                            fontSize: '0.97rem'
                          }}
                        />
                      </Form.Group>
                    </Col>
                    <Col md={6}>
                      <Form.Group>
                        <Form.Label className="fw-bold" style={{ fontSize: '0.97rem' }}>Email</Form.Label>
                        <Form.Control
                          type="email"
                          value={profileData.email}
                          disabled={!isEditing}
                          onChange={(e) =>
                            setProfileData({ ...profileData, email: e.target.value })
                          }
                          style={{ 
                            borderRadius: '0.75rem',
                            padding: '0.5rem 0.75rem',
                            border: '1px solid rgba(30,198,182,0.2)',
                            fontSize: '0.97rem'
                          }}
                        />
                      </Form.Group>
                    </Col>
                    <Col md={6}>
                      <Form.Group>
                        <Form.Label className="fw-bold" style={{ fontSize: '0.97rem' }}>Date of Birth</Form.Label>
                        <Form.Control
                          type="date"
                          value={profileData.dob}
                          disabled={!isEditing}
                          onChange={(e) =>
                            setProfileData({ ...profileData, dob: e.target.value })
                          }
                          style={{ 
                            borderRadius: '0.75rem',
                            padding: '0.5rem 0.75rem',
                            border: '1px solid rgba(30,198,182,0.2)',
                            fontSize: '0.97rem'
                          }}
                        />
                      </Form.Group>
                    </Col>
                    <Col md={6}>
                      <Form.Group>
                        <Form.Label className="fw-bold" style={{ fontSize: '0.97rem' }}>Phone</Form.Label>
                        <Form.Control
                          type="tel"
                          value={profileData.phone}
                          disabled={!isEditing}
                          onChange={(e) =>
                            setProfileData({ ...profileData, phone: e.target.value })
                          }
                          style={{ 
                            borderRadius: '0.75rem',
                            padding: '0.5rem 0.75rem',
                            border: '1px solid rgba(30,198,182,0.2)',
                            fontSize: '0.97rem'
                          }}
                        />
                      </Form.Group>
                    </Col>
                    <Col md={6}>
                      <Form.Group>
                        <Form.Label className="fw-bold" style={{ fontSize: '0.97rem' }}>CNIC</Form.Label>
                        <Form.Control
                          type="text"
                          value={profileData.cnic}
                          disabled={!isEditing}
                          onChange={(e) =>
                            setProfileData({ ...profileData, cnic: e.target.value })
                          }
                          style={{ 
                            borderRadius: '0.75rem',
                            padding: '0.5rem 0.75rem',
                            border: '1px solid rgba(30,198,182,0.2)',
                            fontSize: '0.97rem'
                          }}
                        />
                      </Form.Group>
                    </Col>
                    <Col md={6}>
                      <Form.Group>
                        <Form.Label className="fw-bold" style={{ fontSize: '0.97rem' }}>Specialization</Form.Label>
                        <Form.Control
                          type="text"
                          value={profileData.specialization}
                          disabled={!isEditing}
                          onChange={(e) =>
                            setProfileData({ ...profileData, specialization: e.target.value })
                          }
                          style={{ 
                            borderRadius: '0.75rem',
                            padding: '0.5rem 0.75rem',
                            border: '1px solid rgba(30,198,182,0.2)',
                            fontSize: '0.97rem'
                          }}
                        />
                      </Form.Group>
                    </Col>
                    <Col md={6}>
                      <Form.Group>
                        <Form.Label className="fw-bold" style={{ fontSize: '0.97rem' }}>Position</Form.Label>
                        <Form.Control
                          type="text"
                          value={profileData.position}
                          disabled={!isEditing}
                          onChange={(e) =>
                            setProfileData({ ...profileData, position: e.target.value })
                          }
                          style={{ 
                            borderRadius: '0.75rem',
                            padding: '0.5rem 0.75rem',
                            border: '1px solid rgba(30,198,182,0.2)',
                            fontSize: '0.97rem'
                          }}
                        />
                      </Form.Group>
                    </Col>
                    <Col md={6}>
                      <Form.Group>
                        <Form.Label className="fw-bold" style={{ fontSize: '0.97rem' }}>Years of Experience</Form.Label>
                        <Form.Control
                          type="number"
                          value={profileData.experience}
                          disabled={!isEditing}
                          onChange={(e) =>
                            setProfileData({ ...profileData, experience: e.target.value })
                          }
                          style={{ 
                            borderRadius: '0.75rem',
                            padding: '0.5rem 0.75rem',
                            border: '1px solid rgba(30,198,182,0.2)',
                            fontSize: '0.97rem'
                          }}
                        />
                      </Form.Group>
                    </Col>
                  </Row>
                </Form>
              </Card.Body>
            </Card>
          </Col>
        </Row>
      </Container>
    </div>
  );
};

export default JudgeProfile; 