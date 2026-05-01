// ItemRow.jsx — UB CSE Admin Design System
// Single activity/submission list row with approve/reject actions

const FLAG_ICON = (
  <svg width="13" height="13" viewBox="0 0 24 24" fill="#FFB81C" stroke="#B8860B" strokeWidth="1.5">
    <path d="M4 15s1-1 4-1 5 2 8 2 4-1 4-1V3s-1 1-4 1-5-2-8-2-4 1-4 1z"/>
    <line x1="4" y1="22" x2="4" y2="15"/>
  </svg>
);

const ALERT_ICON = (
  <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="#C0392B" strokeWidth="1.5">
    <path d="M10.29 3.86L1.82 18a2 2 0 001.71 3h16.94a2 2 0 001.71-3L13.71 3.86a2 2 0 00-3.42 0z"/>
    <line x1="12" y1="9" x2="12" y2="13"/>
    <line x1="12" y1="17" x2="12.01" y2="17"/>
  </svg>
);

const DOC_ICON = (
  <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="#B0B8C4" strokeWidth="1.5">
    <path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z"/>
    <polyline points="14 2 14 8 20 8"/>
  </svg>
);

const ItemRow = ({ item, isSelected, onSelect, onApprove, onReject, onView, compact = false }) => {
  const [hovered, setHovered] = React.useState(false);

  const rowHeight = compact ? 36 : 44;
  const isPriority = item.status === 'HIGH PRIORITY';
  const isUrgent   = item.status === 'URGENT';
  const isResolved = item.status === 'APPROVED' || item.status === 'REJECTED' || item.status === 'CLOSED';

  let bg = hovered ? '#EEF2F8' : (isSelected ? '#D6E4F5' : 'white');
  let borderLeft = 'none';
  let borderColor = '#E8EAED';

  if (isPriority) { bg = hovered ? '#FFF3C4' : '#FFFBEB'; borderLeft = '3px solid #FFB81C'; borderColor = '#F0D080'; }
  if (isUrgent)   { bg = hovered ? '#FDDCDA' : '#FFF5F5'; borderLeft = '3px solid #C0392B'; borderColor = '#F0A99F'; }

  const titleColor = isPriority ? '#7A5B00' : isUrgent ? '#7A1A1A' : isResolved ? '#8A95A3' : '#0D1117';

  const leadIcon = isPriority ? FLAG_ICON : isUrgent ? ALERT_ICON : DOC_ICON;

  return (
    <div
      style={{
        display: 'flex', alignItems: 'center', gap: 10,
        padding: `0 12px 0 ${isPriority || isUrgent ? '9px' : '12px'}`,
        height: rowHeight, background: bg,
        borderLeft, borderBottom: `1px solid ${borderColor}`,
        cursor: 'pointer', transition: 'background 0.08s',
      }}
      onMouseEnter={() => setHovered(true)}
      onMouseLeave={() => setHovered(false)}
      onClick={() => onView && onView(item)}
    >
      {/* Checkbox */}
      <input
        type="checkbox"
        checked={isSelected}
        onChange={e => { e.stopPropagation(); onSelect && onSelect(item.id); }}
        onClick={e => e.stopPropagation()}
        style={{ width: 12, height: 12, flexShrink: 0, accentColor: '#005BBB' }}
      />

      {/* Icon */}
      <div style={{ flexShrink: 0 }}>{leadIcon}</div>

      {/* Title + meta */}
      <div style={{ flex: 1, overflow: 'hidden', display: 'flex', alignItems: 'baseline', gap: 8 }}>
        <span style={{ fontSize: 13, fontWeight: 500, color: titleColor, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
          {item.title}
        </span>
        {item.author && (
          <span style={{ fontSize: 11, color: '#8A95A3', whiteSpace: 'nowrap', flexShrink: 0 }}>
            {item.author} · {item.dept}
          </span>
        )}
      </div>

      {/* Type */}
      <TypeBadge type={item.type} />

      {/* Status */}
      <StatusBadge status={item.status} size="xs" />

      {/* Timestamp */}
      <span style={{ fontFamily: "'IBM Plex Mono', monospace", fontSize: 11, color: '#8A95A3', flexShrink: 0, minWidth: 80, textAlign: 'right' }}>
        {item.timestamp}
      </span>

      {/* Actions */}
      <div style={{ display: 'flex', gap: 4, flexShrink: 0 }} onClick={e => e.stopPropagation()}>
        {!isResolved && (
          <>
            <button
              onClick={() => onApprove && onApprove(item.id)}
              style={{ fontFamily: "'IBM Plex Sans',sans-serif", fontSize: 11, fontWeight: 500, background: '#1A7F4B', color: 'white', border: 'none', borderRadius: 2, padding: '3px 8px', cursor: 'pointer' }}
            >Approve</button>
            <button
              onClick={() => onReject && onReject(item.id)}
              style={{ fontFamily: "'IBM Plex Sans',sans-serif", fontSize: 11, fontWeight: 500, background: '#C0392B', color: 'white', border: 'none', borderRadius: 2, padding: '3px 8px', cursor: 'pointer' }}
            >Reject</button>
          </>
        )}
        <button
          onClick={() => onView && onView(item)}
          style={{ fontFamily: "'IBM Plex Sans',sans-serif", fontSize: 11, fontWeight: 500, background: '#E8EAED', color: '#4A5568', border: 'none', borderRadius: 2, padding: '3px 8px', cursor: 'pointer' }}
        >View</button>
      </div>
    </div>
  );
};

Object.assign(window, { ItemRow });
