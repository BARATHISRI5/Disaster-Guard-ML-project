import React from 'react';

export default function TopBar({ overallRisk, lastUpdated, alerts }) {
  const riskClass = overallRisk >= 0.65 ? 'critical' : overallRisk >= 0.3 ? 'moderate' : 'safe';
  const riskLabel = overallRisk >= 0.65 ? 'HIGH ALERT' : overallRisk >= 0.3 ? 'ELEVATED' : 'NORMAL';

  const tickerAlerts = alerts && alerts.length > 0 ? alerts : [
    { district: 'Thoothukudi', risk_score: 0.82, risk_level: 'critical' },
    { district: 'Nagapattinam', risk_score: 0.71, risk_level: 'critical' },
    { district: 'Cuddalore', risk_score: 0.68, risk_level: 'critical' },
    { district: 'Ramanathapuram', risk_score: 0.62, risk_level: 'moderate' },
  ];

  // Duplicate for seamless scroll
  const doubled = [...tickerAlerts, ...tickerAlerts];

  return (
    <div className="topbar">
      <div className="topbar-brand">
        <span className="shield">🛡️</span>
        <span className="logo">DISASTERGUARD</span>
      </div>

      <div className="alert-ticker">
        <div className="alert-ticker-inner">
          {doubled.map((a, i) => (
            <span key={i} className={`ticker-item ${a.risk_level === 'critical' ? 'critical' : ''}`}>
              ⚠️ {a.district}: {Math.round((a.risk_score || 0) * 100)}% flood risk
            </span>
          ))}
        </div>
      </div>

      <div className="topbar-meta">
        <span className={`risk-badge ${riskClass}`}>
          {riskLabel}
        </span>
        <span>
          {lastUpdated ? new Date(lastUpdated).toLocaleTimeString() : new Date().toLocaleTimeString()}
        </span>
      </div>
    </div>
  );
}
