import React from 'react';

export default function LoadingSkeleton({ type = 'card', count = 3 }) {
  if (type === 'map') {
    return (
      <div className="skeleton skeleton-map" style={{ display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        <div style={{ textAlign: 'center', color: 'var(--color-text-dim)' }}>
          <div style={{ fontSize: '40px', marginBottom: '12px' }}>🛰️</div>
          <div style={{ fontFamily: 'var(--font-mono)', fontSize: '13px' }}>Loading satellite data...</div>
        </div>
      </div>
    );
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
      {Array.from({ length: count }).map((_, i) => (
        <div key={i}>
          {type === 'card' && <div className="skeleton skeleton-card" />}
          {type === 'text' && (
            <>
              <div className="skeleton skeleton-title" style={{ width: `${50 + Math.random() * 40}%` }} />
              <div className="skeleton skeleton-text" style={{ width: `${70 + Math.random() * 25}%` }} />
              <div className="skeleton skeleton-text" style={{ width: `${60 + Math.random() * 30}%` }} />
            </>
          )}
        </div>
      ))}
    </div>
  );
}
