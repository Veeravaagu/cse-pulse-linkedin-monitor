// FilterBar.jsx — UB CSE Admin Design System

const FilterBar = ({ search, onSearch, statusFilter, onStatusFilter, typeFilter, onTypeFilter, onBulkApprove, selectedCount = 0 }) => {
  const inputStyle = {
    fontFamily: "'IBM Plex Sans', sans-serif", fontSize: 12, color: '#0D1117',
    background: 'white', border: '1px solid #DDE1E7', borderRadius: 4,
    padding: '0 8px', height: 28, outline: 'none',
  };
  const selectWrap = { position: 'relative', display: 'flex', alignItems: 'center' };
  const chevron = (
    <svg style={{ position: 'absolute', right: 6, pointerEvents: 'none', color: '#8A95A3' }} width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><polyline points="6 9 12 15 18 9"/></svg>
  );

  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 8, padding: '8px 16px', background: '#F9FAFB', borderBottom: '1px solid #DDE1E7', flexWrap: 'wrap' }}>
      {/* Search */}
      <div style={{ position: 'relative', flex: '0 0 220px' }}>
        <svg style={{ position: 'absolute', left: 7, top: '50%', transform: 'translateY(-50%)', color: '#B0B8C4' }} width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>
        <input
          type="text"
          value={search}
          onChange={e => onSearch(e.target.value)}
          placeholder="Filter by title, author, ID…"
          style={{ ...inputStyle, paddingLeft: 26, width: '100%' }}
        />
      </div>

      {/* Status filter */}
      <div style={selectWrap}>
        <select value={statusFilter} onChange={e => onStatusFilter(e.target.value)} style={{ ...inputStyle, paddingRight: 22, appearance: 'none', cursor: 'pointer', minWidth: 130 }}>
          <option value="all">Status: All</option>
          <option value="HIGH PRIORITY">High Priority</option>
          <option value="URGENT">Urgent</option>
          <option value="PENDING">Pending</option>
          <option value="IN REVIEW">In Review</option>
          <option value="APPROVED">Approved</option>
          <option value="REJECTED">Rejected</option>
        </select>
        {chevron}
      </div>

      {/* Type filter */}
      <div style={selectWrap}>
        <select value={typeFilter} onChange={e => onTypeFilter(e.target.value)} style={{ ...inputStyle, paddingRight: 22, appearance: 'none', cursor: 'pointer', minWidth: 130 }}>
          <option value="all">Type: All</option>
          <option value="Submission">Submission</option>
          <option value="Event">Event</option>
          <option value="Report">Report</option>
          <option value="Request">Request</option>
          <option value="Appeal">Appeal</option>
          <option value="Enrollment">Enrollment</option>
        </select>
        {chevron}
      </div>

      {/* Sort */}
      <div style={selectWrap}>
        <select style={{ ...inputStyle, paddingRight: 22, appearance: 'none', cursor: 'pointer', minWidth: 130 }}>
          <option>Sort: Newest</option>
          <option>Sort: Priority</option>
          <option>Sort: Status</option>
        </select>
        {chevron}
      </div>

      <div style={{ flex: 1 }}></div>

      {/* Bulk actions */}
      {selectedCount > 0 && (
        <div style={{ display: 'flex', alignItems: 'center', gap: 6, padding: '3px 10px', background: '#EEF2F8', border: '1px solid #C5D6EF', borderRadius: 4 }}>
          <span style={{ fontSize: 12, color: '#005BBB', fontWeight: 500 }}>{selectedCount} selected</span>
          <button onClick={onBulkApprove} style={{ fontFamily: "'IBM Plex Sans',sans-serif", fontSize: 11, fontWeight: 500, background: '#1A7F4B', color: 'white', border: 'none', borderRadius: 2, padding: '2px 8px', cursor: 'pointer' }}>Approve All</button>
          <button style={{ fontFamily: "'IBM Plex Sans',sans-serif", fontSize: 11, fontWeight: 500, background: '#C0392B', color: 'white', border: 'none', borderRadius: 2, padding: '2px 8px', cursor: 'pointer' }}>Reject All</button>
        </div>
      )}

      <button style={{ fontFamily: "'IBM Plex Sans',sans-serif", fontSize: 12, fontWeight: 500, background: 'white', color: '#4A5568', border: '1px solid #DDE1E7', borderRadius: 4, padding: '0 12px', height: 28, cursor: 'pointer', display: 'flex', alignItems: 'center', gap: 5 }}>
        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>
        Export
      </button>
    </div>
  );
};

Object.assign(window, { FilterBar });
