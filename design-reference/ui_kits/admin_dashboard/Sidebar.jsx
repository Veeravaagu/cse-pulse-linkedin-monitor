// Sidebar.jsx — UB CSE Admin Design System

const NAV_ITEMS = [
  {
    section: 'OVERVIEW',
    items: [
      { id: 'dashboard', label: 'Dashboard', icon: 'grid' },
      { id: 'activity',  label: 'Activity Feed', icon: 'activity', count: 48 },
    ]
  },
  {
    section: 'REVIEW',
    items: [
      { id: 'submissions', label: 'Submissions', icon: 'file-text', count: 7,  countVariant: 'alert' },
      { id: 'events',      label: 'Events',      icon: 'calendar',  count: 3,  countVariant: 'warn' },
      { id: 'enrollments', label: 'Enrollments', icon: 'users' },
      { id: 'flagged',     label: 'Flagged Items', icon: 'flag',    count: 12, countVariant: 'alert' },
    ]
  },
  {
    section: 'REPORTS',
    items: [
      { id: 'analytics', label: 'Analytics',  icon: 'bar-chart-2' },
      { id: 'auditlog',  label: 'Audit Log',  icon: 'radio' },
    ]
  }
];

const ICONS = {
  'grid': <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"><rect x="3" y="3" width="7" height="7"/><rect x="14" y="3" width="7" height="7"/><rect x="14" y="14" width="7" height="7"/><rect x="3" y="14" width="7" height="7"/></svg>,
  'activity': <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"><polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/></svg>,
  'file-text': <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/><polyline points="10 9 9 9 8 9"/></svg>,
  'calendar': <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"><rect x="3" y="4" width="18" height="18" rx="2" ry="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/></svg>,
  'users': <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/></svg>,
  'flag': <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"><path d="M4 15s1-1 4-1 5 2 8 2 4-1 4-1V3s-1 1-4 1-5-2-8-2-4 1-4 1z"/><line x1="4" y1="22" x2="4" y2="15"/></svg>,
  'bar-chart-2': <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"><line x1="18" y1="20" x2="18" y2="10"/><line x1="12" y1="20" x2="12" y2="4"/><line x1="6" y1="20" x2="6" y2="14"/></svg>,
  'radio': <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="2"/><path d="M16.24 7.76a6 6 0 0 1 0 8.49m-8.48-.01a6 6 0 0 1 0-8.49m11.31-2.82a10 10 0 0 1 0 14.14m-14.14 0a10 10 0 0 1 0-14.14"/></svg>,
  'settings': <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="3"/><path d="M19.07 4.93a10 10 0 0 1 0 14.14M4.93 4.93a10 10 0 0 0 0 14.14"/></svg>,
};

const Sidebar = ({ activeId, onNavigate }) => {
  const sidebarStyles = {
    width: 220, background: '#0D1117', height: '100%',
    display: 'flex', flexDirection: 'column', flexShrink: 0,
    borderRight: '1px solid rgba(255,255,255,0.06)',
  };

  return (
    <div style={sidebarStyles}>
      {/* Header */}
      <div style={{ padding: '10px 16px', borderBottom: '1px solid rgba(255,255,255,0.08)', display: 'flex', alignItems: 'center', gap: 10, height: 48 }}>
        <svg width="24" height="28" viewBox="0 0 48 56" fill="none">
          <path d="M4 4 L4 36 Q4 52 24 56 Q44 52 44 36 L44 4 Z" fill="#005BBB"/>
          <path d="M10 10 L10 36 Q10 48 24 51 Q38 48 38 36 L38 10 Z" fill="white"/>
          <text x="24" y="37" fontFamily="'IBM Plex Sans',Arial,sans-serif" fontSize="16" fontWeight="700" fill="#005BBB" textAnchor="middle">UB</text>
        </svg>
        <div>
          <div style={{ fontSize: 13, fontWeight: 600, color: 'white', lineHeight: 1.2 }}>CSE Admin</div>
          <div style={{ fontSize: 10, color: 'rgba(255,255,255,0.35)', letterSpacing: '0.05em', textTransform: 'uppercase' }}>Activity Monitor</div>
        </div>
      </div>

      {/* Nav */}
      <div style={{ flex: 1, overflow: 'auto', paddingTop: 8 }}>
        {NAV_ITEMS.map(group => (
          <div key={group.section} style={{ marginBottom: 4 }}>
            <div style={{ fontSize: 10, fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.08em', color: 'rgba(255,255,255,0.28)', padding: '6px 16px 3px' }}>
              {group.section}
            </div>
            {group.items.map(item => {
              const isActive = item.id === activeId;
              return (
                <div
                  key={item.id}
                  onClick={() => onNavigate(item.id)}
                  style={{
                    display: 'flex', alignItems: 'center', gap: 9,
                    padding: '7px 16px', fontSize: 13, cursor: 'pointer',
                    color: isActive ? 'white' : 'rgba(255,255,255,0.58)',
                    background: isActive ? '#005BBB' : 'transparent',
                    transition: 'background 0.1s',
                  }}
                  onMouseEnter={e => { if (!isActive) e.currentTarget.style.background = 'rgba(255,255,255,0.05)'; }}
                  onMouseLeave={e => { if (!isActive) e.currentTarget.style.background = 'transparent'; }}
                >
                  {ICONS[item.icon]}
                  <span style={{ flex: 1 }}>{item.label}</span>
                  {item.count && <CountBadge count={item.count} variant={isActive ? 'default' : (item.countVariant || 'default')} />}
                </div>
              );
            })}
          </div>
        ))}
      </div>

      {/* Footer */}
      <div style={{ padding: '10px 16px', borderTop: '1px solid rgba(255,255,255,0.08)', display: 'flex', alignItems: 'center', gap: 9 }}>
        <div style={{ width: 26, height: 26, borderRadius: '50%', background: '#005BBB', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 10, fontWeight: 700, color: 'white', flexShrink: 0 }}>SA</div>
        <div style={{ flex: 1, overflow: 'hidden' }}>
          <div style={{ fontSize: 12, color: 'rgba(255,255,255,0.7)', fontWeight: 500 }}>sys.admin</div>
          <div style={{ fontSize: 10, color: 'rgba(255,255,255,0.3)' }}>CSE Dept.</div>
        </div>
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="rgba(255,255,255,0.3)" strokeWidth="1.5"><circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83-2.83l.06-.06A1.65 1.65 0 0 0 4.68 15a1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 2.83-2.83l.06.06A1.65 1.65 0 0 0 9 4.68a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 2.83l-.06.06A1.65 1.65 0 0 0 19.4 9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z"/></svg>
      </div>
    </div>
  );
};

Object.assign(window, { Sidebar, NAV_ITEMS, ICONS });
