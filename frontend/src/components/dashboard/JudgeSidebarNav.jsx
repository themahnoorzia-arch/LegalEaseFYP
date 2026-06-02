import React from 'react';
import { ListGroup } from 'react-bootstrap';
import { Briefcase, Calendar3, Folder } from 'react-bootstrap-icons';

const navItems = [
  { view: 'assigned', label: 'Assigned Cases', icon: <Briefcase className="me-2" /> },
  { view: 'schedule', label: 'Hearing Schedule', icon: <Calendar3 className="me-2" /> },
  { view: 'documents', label: 'Documents', icon: <Folder className="me-2" /> },
];

const JudgeSidebarNav = ({ activeView, onViewChange }) => {
  return (
    <div
      style={{
        background: 'linear-gradient(135deg, #1ec6b6 0%, #22304a 100%)',
        borderTopRightRadius: 18,
        borderBottomRightRadius: 18,
        boxShadow: '2px 0 16px 0 rgba(34,48,74,0.08)',
        padding: '18px 0',
        minHeight: '100%',
        color: '#fff',
        width: '100%',
        display: 'flex',
        flexDirection: 'column',
      }}
    >
      <div style={{ fontWeight: 700, fontSize: 20, padding: '0 24px 18px 24px', letterSpacing: 1 }}>
        Judge Portal
      </div>
      <ListGroup variant="flush" className="d-flex flex-column gap-1" style={{ background: 'transparent' }}>
        {navItems.map((item) => (
          <ListGroup.Item
            key={item.view}
            action
            onClick={() => onViewChange(item.view)}
            active={activeView === item.view}
            className={`d-flex align-items-center px-3 py-2 border-0 rounded-2 ${
              activeView === item.view ? 'bg-white fw-bold shadow-sm' : 'text-white'
            }`}
            style={{
              background: activeView === item.view ? '#fff' : 'transparent',
              color: activeView === item.view ? '#1ec6b6' : '#fff',
              fontWeight: activeView === item.view ? 700 : 500,
              fontSize: 15,
              borderLeft: activeView === item.view ? '4px solid #1ec6b6' : '4px solid transparent',
              marginBottom: 2,
              transition: 'all 0.18s',
              cursor: 'pointer',
            }}
          >
            {item.icon}
            <span style={{ fontSize: 14 }}>{item.label}</span>
          </ListGroup.Item>
        ))}
      </ListGroup>
    </div>
  );
};

export default JudgeSidebarNav;
