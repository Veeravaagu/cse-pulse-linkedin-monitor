// StatsPanel.jsx — UB CSE Admin Design System

const STAT_CONFIGS = [
  {
    key: 'highPriority',
    label: 'High Priority',
    value: 7,
    delta: '+3 since yesterday',
    deltaUp: true,
    variant: 'warn',
    icon: <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#B8860B" strokeWidth="1.5"><path d="M4 15s1-1 4-1 5 2 8 2 4-1 4-1V3s-1 1-4 1-5-2-8-2-4 1-4 1z"/><line x1="4" y1="22" x2="4" y2="15"/></svg>,
  },
  {
    key: 'urgentFlags',
    label: 'Urgent Flags',
    value: 3,
    delta: '+1 new today',
    deltaUp: true,
    variant: 'alert',
    icon: <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#C0392B" strokeWidth="1.5"><path d="M10.29 3.86L1.82 18a2 2 0 001.71 3h16.94a2 2 0 001.71-3L13.71 3.86a2 2 0 00-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>,
  },
  {
    key: 'pendingReview',
    label: 'Pending Review',
    value: 48,
    delta: 'no change',
    deltaUp: null,
    variant: 'neutral',
    icon: <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#8A95A3" strokeWidth="1.5"><polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/></svg>,
  },
  {
    key: 'resolved',
    label: 'Resolved This Week',
    value: 124,
    delta: '−8 vs. last week',
    deltaUp: false,
    variant: 'success',
    icon: <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#1A7F4B" strokeWidth="1.5"><polyline points="20 6 9 17 4 12"/></svg>,
  },
];

const STAT_STYLES = {
  warn:    { border: '#F0D080', bg: '#FFFBEB', valColor: '#B8860B' },
  alert:   { border: '#F0A99F', bg: '#FFF5F5', valColor: '#C0392B' },
  neutral: { border: '#DDE1E7', bg: 'white',   valColor: '#0D1117' },
  success: { border: '#A3D4B5', bg: 'white',   valColor: '#1A7F4B' },
};

const StatsPanel = ({ onStatClick }) => {
  return (
    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 8, padding: '12px 16px', borderBottom: '1px solid #DDE1E7', background: 'white' }}>
      {STAT_CONFIGS.map(stat => {
        const s = STAT_STYLES[stat.variant];
        const deltaColor = stat.deltaUp === null ? '#8A95A3' : stat.deltaUp ? '#C0392B' : '#1A7F4B';
        return (
          <div
            key={stat.key}
            onClick={() => onStatClick && onStatClick(stat.key)}
            style={{ border: `1px solid ${s.border}`, background: s.bg, borderRadius: 4, padding: '10px 12px', cursor: 'pointer' }}
          >
            <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', marginBottom: 4 }}>
              <span style={{ fontFamily: "'IBM Plex Mono', monospace", fontSize: 26, fontWeight: 700, color: s.valColor, lineHeight: 1 }}>
                {String(stat.value).padStart(2, '0')}
              </span>
              {stat.icon}
            </div>
            <div style={{ fontSize: 11, fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.05em', color: '#8A95A3' }}>{stat.label}</div>
            <div style={{ fontFamily: "'IBM Plex Mono', monospace", fontSize: 11, color: deltaColor, marginTop: 3 }}>
              {stat.deltaUp === true ? '↑ ' : stat.deltaUp === false ? '↓ ' : '— '}{stat.delta}
            </div>
          </div>
        );
      })}
    </div>
  );
};

Object.assign(window, { StatsPanel, STAT_CONFIGS });
