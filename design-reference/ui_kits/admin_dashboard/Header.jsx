// Header.jsx — UB CSE Admin Design System

const BREADCRUMBS = {
  dashboard:   ['Dashboard'],
  activity:    ['Activity Feed'],
  submissions: ['Review', 'Submissions'],
  events:      ['Review', 'Events'],
  enrollments: ['Review', 'Enrollments'],
  flagged:     ['Review', 'Flagged Items'],
  analytics:   ['Reports', 'Analytics'],
  auditlog:    ['Reports', 'Audit Log'],
  detail:      ['Review', 'Submissions', 'Item Detail'],
};

const Header = ({ activeId, onSearch, searchValue = '' }) => {
  const crumbs = BREADCRUMBS[activeId] || ['Dashboard'];
  return (
    <div style={{
      height: 48, background: 'white', borderBottom: '1px solid #DDE1E7',
      display: 'flex', alignItems: 'center', padding: '0 16px', gap: 12,
      flexShrink: 0, position: 'relative', zIndex: 10,
    }}>
      {/* Breadcrumb */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 6, flex: 1 }}>
        {crumbs.map((crumb, i) => (
          <React.Fragment key={i}>
            {i > 0 && <span style={{ color: '#DDE1E7', fontSize: 14 }}>/</span>}
            <span style={{
              fontSize: 13,
              color: i === crumbs.length - 1 ? '#0D1117' : '#8A95A3',
              fontWeight: i === crumbs.length - 1 ? 600 : 400,
            }}>{crumb}</span>
          </React.Fragment>
        ))}
      </div>

      {/* Search */}
      <div style={{ position: 'relative', flexShrink: 0 }}>
        <svg style={{ position: 'absolute', left: 8, top: '50%', transform: 'translateY(-50%)', color: '#B0B8C4' }} width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>
        <input
          type="text"
          placeholder="Search…"
          value={searchValue}
          onChange={e => onSearch && onSearch(e.target.value)}
          style={{
            fontFamily: "'IBM Plex Sans', sans-serif", fontSize: 12,
            color: '#0D1117', background: '#F4F5F7', border: '1px solid #DDE1E7',
            borderRadius: 4, padding: '0 10px 0 28px', height: 28, width: 200, outline: 'none',
          }}
        />
      </div>

      {/* Actions */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
        <div style={{ position: 'relative' }}>
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#8A95A3" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"><path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"/><path d="M13.73 21a2 2 0 0 1-3.46 0"/></svg>
          <span style={{ position: 'absolute', top: -4, right: -4, width: 14, height: 14, borderRadius: '50%', background: '#C0392B', color: 'white', fontSize: 9, fontWeight: 700, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>7</span>
        </div>
        <div style={{ width: 1, height: 20, background: '#DDE1E7' }}></div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 6, cursor: 'pointer' }}>
          <div style={{ width: 26, height: 26, borderRadius: '50%', background: '#005BBB', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 10, fontWeight: 700, color: 'white' }}>SA</div>
          <span style={{ fontSize: 12, fontWeight: 500, color: '#0D1117' }}>sys.admin</span>
          <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="#8A95A3" strokeWidth="2"><polyline points="6 9 12 15 18 9"/></svg>
        </div>
      </div>
    </div>
  );
};

Object.assign(window, { Header, BREADCRUMBS });
