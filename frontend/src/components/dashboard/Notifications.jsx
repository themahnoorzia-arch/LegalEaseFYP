import React, { useState, useEffect, useCallback } from 'react';
import { Badge, Dropdown, ListGroup, Spinner } from 'react-bootstrap';
import { Bell, Check, AlertCircle, Info, CheckCheck } from 'lucide-react';

const TYPE_ICON = {
  success: <Check size={15} style={{ color: '#16a34a' }} />,
  warning: <AlertCircle size={15} style={{ color: '#d97706' }} />,
  error:   <AlertCircle size={15} style={{ color: '#dc2626' }} />,
  info:    <Info size={15} style={{ color: '#1ec6b6' }} />,
};

function timeAgo(iso) {
  const diff = Date.now() - new Date(iso).getTime();
  const m = Math.floor(diff / 60000);
  if (m < 1) return 'just now';
  if (m < 60) return `${m}m ago`;
  const h = Math.floor(m / 60);
  if (h < 24) return `${h}h ago`;
  return `${Math.floor(h / 24)}d ago`;
}

const Notifications = () => {
  const [notifications, setNotifications] = useState([]);
  const [loading, setLoading] = useState(false);

  const fetchNotifications = useCallback(async () => {
    try {
      const res = await fetch('/api/notifications', { credentials: 'include' });
      const data = await res.json();
      if (res.ok) setNotifications(data.notifications || []);
    } catch {
      // silently fail — notifications must never break the dashboard
    }
  }, []);

  useEffect(() => {
    fetchNotifications();
    const interval = setInterval(fetchNotifications, 30000);
    return () => clearInterval(interval);
  }, [fetchNotifications]);

  const markRead = async (id) => {
    setNotifications(prev =>
      prev.map(n => n.notificationid === id ? { ...n, is_read: true } : n)
    );
    try {
      await fetch(`/api/notifications/${id}/read`, { method: 'PATCH', credentials: 'include' });
    } catch { /* silent */ }
  };

  const markAllRead = async () => {
    setNotifications(prev => prev.map(n => ({ ...n, is_read: true })));
    try {
      await fetch('/api/notifications/read-all', { method: 'PATCH', credentials: 'include' });
    } catch { /* silent */ }
  };

  const unread = notifications.filter(n => !n.is_read).length;

  const CustomToggle = React.forwardRef(({ onClick }, ref) => (
    <div ref={ref} onClick={e => { e.preventDefault(); onClick(e); }}
      style={{ cursor: 'pointer', position: 'relative', display: 'inline-flex' }}>
      <Bell size={20} />
      {unread > 0 && (
        <Badge bg="danger" pill style={{
          position: 'absolute', top: -6, right: -6,
          fontSize: '0.65rem', padding: '0.2rem 0.38rem', minWidth: 16,
        }}>
          {unread > 99 ? '99+' : unread}
        </Badge>
      )}
    </div>
  ));

  return (
    <Dropdown align="end">
      <Dropdown.Toggle as={CustomToggle} />
      <Dropdown.Menu style={{ width: 330, maxHeight: 420, overflowY: 'auto', padding: 0, boxShadow: '0 4px 24px rgba(0,0,0,0.13)' }}>
        <div style={{ padding: '10px 14px', borderBottom: '1px solid #e5e7eb', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <span style={{ fontWeight: 700, fontSize: 15, color: '#22304a' }}>Notifications</span>
          {unread > 0 && (
            <button onClick={markAllRead} style={{
              background: 'none', border: 'none', cursor: 'pointer',
              fontSize: 12, color: '#1ec6b6', fontWeight: 600,
              display: 'flex', alignItems: 'center', gap: 4,
            }}>
              <CheckCheck size={13} /> Mark all read
            </button>
          )}
        </div>

        <ListGroup variant="flush">
          {notifications.length === 0 ? (
            <ListGroup.Item className="text-center py-4 text-muted" style={{ fontSize: 13 }}>
              <Bell size={22} style={{ opacity: 0.3, display: 'block', margin: '0 auto 6px' }} />
              No notifications yet
            </ListGroup.Item>
          ) : (
            notifications.map(n => (
              <ListGroup.Item
                key={n.notificationid}
                onClick={() => !n.is_read && markRead(n.notificationid)}
                style={{
                  cursor: n.is_read ? 'default' : 'pointer',
                  background: n.is_read ? '#fff' : '#f0fdfb',
                  borderLeft: n.is_read ? '3px solid transparent' : '3px solid #1ec6b6',
                  padding: '10px 14px',
                }}
              >
                <div style={{ display: 'flex', gap: 10, alignItems: 'flex-start' }}>
                  <div style={{ marginTop: 2, flexShrink: 0 }}>
                    {TYPE_ICON[n.notif_type] || TYPE_ICON.info}
                  </div>
                  <div style={{ flex: 1, minWidth: 0 }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline', gap: 6 }}>
                      <span style={{ fontWeight: n.is_read ? 500 : 700, fontSize: 13, color: '#22304a' }}>
                        {n.title}
                      </span>
                      <span style={{ fontSize: 11, color: '#9ca3af', flexShrink: 0 }}>
                        {timeAgo(n.created_at)}
                      </span>
                    </div>
                    <p style={{ margin: 0, fontSize: 12, color: '#6b7280', marginTop: 2 }}>
                      {n.message}
                    </p>
                  </div>
                </div>
              </ListGroup.Item>
            ))
          )}
        </ListGroup>
      </Dropdown.Menu>
    </Dropdown>
  );
};

export default Notifications;
