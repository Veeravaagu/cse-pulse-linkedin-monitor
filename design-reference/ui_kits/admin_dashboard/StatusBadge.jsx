// StatusBadge.jsx — UB CSE Admin Design System
// Renders status, type, count, and priority badges

const StatusBadge = ({ status, size = 'sm' }) => {
  const configs = {
    'HIGH PRIORITY': { bg: '#FFFBEB', color: '#B8860B', border: '#F0D080', dot: '#FFB81C' },
    'URGENT':        { bg: '#FFF5F5', color: '#C0392B', border: '#F0A99F' },
    'PENDING':       { bg: '#F4F5F7', color: '#4A5568', border: '#DDE1E7' },
    'IN REVIEW':     { bg: '#EEF2F8', color: '#005BBB', border: '#C5D6EF' },
    'APPROVED':      { bg: '#EAF5EE', color: '#1A7F4B', border: '#A3D4B5' },
    'REJECTED':      { bg: '#FDECEB', color: '#C0392B', border: '#F0A99F' },
    'CLOSED':        { bg: '#F4F5F7', color: '#8A95A3', border: '#DDE1E7' },
    'ESCALATED':     { bg: '#FDECEB', color: '#C0392B', border: '#F0A99F' },
  };
  const cfg = configs[status] || configs['PENDING'];
  const style = {
    display: 'inline-flex', alignItems: 'center', gap: '4px',
    fontSize: size === 'xs' ? '10px' : '11px',
    fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.05em',
    padding: size === 'xs' ? '1px 5px' : '2px 7px',
    borderRadius: '2px',
    background: cfg.bg, color: cfg.color,
    border: `1px solid ${cfg.border}`,
    whiteSpace: 'nowrap',
    fontFamily: "'IBM Plex Sans', sans-serif",
  };
  return (
    <span style={style}>
      {cfg.dot && <span style={{ width: 5, height: 5, borderRadius: '50%', background: cfg.dot, flexShrink: 0 }}></span>}
      {status}
    </span>
  );
};

const TypeBadge = ({ type }) => {
  const configs = {
    'Submission': { bg: '#EEF2F8', color: '#005BBB' },
    'Event':      { bg: '#EAF5EE', color: '#1A7F4B' },
    'Report':     { bg: '#FDECEB', color: '#C0392B' },
    'Request':    { bg: '#F4F5F7', color: '#4A5568' },
    'Project':    { bg: '#EEF2F8', color: '#3380CC' },
    'Appeal':     { bg: '#FFFBEB', color: '#B8860B' },
    'Enrollment': { bg: '#EAF5EE', color: '#156B3F' },
  };
  const cfg = configs[type] || { bg: '#F4F5F7', color: '#4A5568' };
  return (
    <span style={{
      display: 'inline-flex', alignItems: 'center',
      fontSize: '11px', fontWeight: 600, textTransform: 'uppercase',
      letterSpacing: '0.04em', padding: '1px 6px', borderRadius: '2px',
      background: cfg.bg, color: cfg.color,
      fontFamily: "'IBM Plex Sans', sans-serif",
      whiteSpace: 'nowrap',
    }}>{type}</span>
  );
};

const CountBadge = ({ count, variant = 'default' }) => {
  const variants = {
    default: { bg: '#E8EAED', color: '#4A5568' },
    alert:   { bg: '#C0392B', color: 'white' },
    warn:    { bg: '#FFB81C', color: '#0D1117' },
    primary: { bg: '#005BBB', color: 'white' },
  };
  const v = variants[variant] || variants.default;
  return (
    <span style={{
      display: 'inline-flex', alignItems: 'center', justifyContent: 'center',
      fontFamily: "'IBM Plex Mono', monospace", fontSize: '11px', fontWeight: 500,
      minWidth: 20, height: 18, borderRadius: '2px', padding: '0 4px',
      background: v.bg, color: v.color,
    }}>{count}</span>
  );
};

Object.assign(window, { StatusBadge, TypeBadge, CountBadge });
