import React from 'react';

export default function Sidebar({
  districts,
  selectedDistrict,
  onSelectDistrict,
  timeWindow,
  onTimeWindowChange,
  disasterType,
  onDisasterTypeChange,
  isLoading,
}) {
  const sortedDistricts = districts
    ? [...districts].sort((a, b) => b.risk_score - a.risk_score)
    : [];

  const getRiskColor = (score) => {
    if (score >= 0.65) return '#ef4444';
    if (score >= 0.3) return '#f59e0b';
    return '#00d4ff';
  };

  return (
    <div className="sidebar">
      {/* District Selector */}
      <div className="sidebar-section">
        <h3>📍 Districts</h3>
        {isLoading ? (
          Array.from({ length: 8 }).map((_, i) => (
            <div key={i} className="skeleton skeleton-text" style={{ width: `${60 + Math.random() * 30}%` }} />
          ))
        ) : (
          <div className="district-list">
            {sortedDistricts.map((d) => (
              <div
                key={d.name}
                className={`district-item ${selectedDistrict === d.name ? 'active' : ''}`}
                onClick={() => onSelectDistrict(d.name)}
              >
                <span>{d.name}</span>
                <span
                  className="district-risk"
                  style={{
                    color: getRiskColor(d.risk_score),
                    background: `${getRiskColor(d.risk_score)}15`,
                  }}
                >
                  {Math.round(d.risk_score * 100)}%
                </span>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Time Window */}
      <div className="sidebar-section">
        <h3>⏱️ Forecast Window</h3>
        <div className="time-toggle">
          {['24h', '48h', '72h'].map((t) => (
            <button
              key={t}
              className={`time-btn ${timeWindow === t ? 'active' : ''}`}
              onClick={() => onTimeWindowChange(t)}
            >
              {t}
            </button>
          ))}
        </div>
      </div>

      {/* Disaster Type Filter */}
      <div className="sidebar-section">
        <h3>🌊 Disaster Type</h3>
        <div className="disaster-filter">
          {[
            { key: 'all', label: 'All' },
            { key: 'flood', label: '🌊 Flood' },
            { key: 'cyclone', label: '🌀 Cyclone' },
            { key: 'landslide', label: '⛰️ Landslide' },
          ].map((f) => (
            <button
              key={f.key}
              className={`filter-chip ${disasterType === f.key ? 'active' : ''}`}
              onClick={() => onDisasterTypeChange(f.key)}
            >
              {f.label}
            </button>
          ))}
        </div>
      </div>

      {/* Quick Stats */}
      <div className="sidebar-section">
        <h3>📊 Quick Stats</h3>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '13px' }}>
            <span style={{ color: 'var(--color-text-muted)' }}>Critical Districts</span>
            <span style={{ color: 'var(--color-critical)', fontFamily: 'var(--font-mono)', fontWeight: 600 }}>
              {sortedDistricts.filter((d) => d.risk_score >= 0.65).length}
            </span>
          </div>
          <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '13px' }}>
            <span style={{ color: 'var(--color-text-muted)' }}>Moderate Districts</span>
            <span style={{ color: 'var(--color-moderate)', fontFamily: 'var(--font-mono)', fontWeight: 600 }}>
              {sortedDistricts.filter((d) => d.risk_score >= 0.3 && d.risk_score < 0.65).length}
            </span>
          </div>
          <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '13px' }}>
            <span style={{ color: 'var(--color-text-muted)' }}>Safe Districts</span>
            <span style={{ color: 'var(--color-safe)', fontFamily: 'var(--font-mono)', fontWeight: 600 }}>
              {sortedDistricts.filter((d) => d.risk_score < 0.3).length}
            </span>
          </div>
          <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '13px', marginTop: '4px', paddingTop: '8px', borderTop: '1px solid var(--border-subtle)' }}>
            <span style={{ color: 'var(--color-text-muted)' }}>Monitoring</span>
            <span style={{ fontFamily: 'var(--font-mono)', fontWeight: 600, color: 'var(--color-safe)' }}>
              {sortedDistricts.length} / 38
            </span>
          </div>
        </div>
      </div>
    </div>
  );
}
