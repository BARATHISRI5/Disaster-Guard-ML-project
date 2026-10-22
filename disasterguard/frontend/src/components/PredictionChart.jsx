import React from 'react';
import {
  AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  LineChart, Line, Legend,
} from 'recharts';

const CustomTooltip = ({ active, payload, label }) => {
  if (!active || !payload) return null;
  return (
    <div style={{
      background: '#111827', border: '1px solid rgba(0,212,255,0.2)',
      borderRadius: '8px', padding: '10px 14px', fontSize: '12px',
      boxShadow: '0 4px 20px rgba(0,0,0,0.5)',
    }}>
      <div style={{ color: '#94a3b8', marginBottom: '6px', fontFamily: 'JetBrains Mono' }}>{label}</div>
      {payload.map((p, i) => (
        <div key={i} style={{ color: p.color, display: 'flex', justifyContent: 'space-between', gap: '16px' }}>
          <span>{p.name}</span>
          <span style={{ fontWeight: 600, fontFamily: 'JetBrains Mono' }}>{p.value}</span>
        </div>
      ))}
    </div>
  );
};

export default function PredictionChart({ timeSeriesData, district }) {
  const data = timeSeriesData?.data || [];

  if (!data.length) {
    return (
      <div className="chart-container">
        <h3>📈 Environmental Data</h3>
        <div style={{ textAlign: 'center', padding: '30px', color: 'var(--color-text-dim)', fontSize: '13px' }}>
          Select a district to view time-series data
        </div>
      </div>
    );
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
      {/* Rainfall Chart */}
      <div className="chart-container">
        <h3>🌧️ Rainfall — {district}</h3>
        <ResponsiveContainer width="100%" height={140}>
          <AreaChart data={data}>
            <defs>
              <linearGradient id="rainGrad" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#00d4ff" stopOpacity={0.3} />
                <stop offset="95%" stopColor="#00d4ff" stopOpacity={0} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="date" tick={{ fontSize: 10 }} tickFormatter={(d) => d.slice(5)} />
            <YAxis tick={{ fontSize: 10 }} />
            <Tooltip content={<CustomTooltip />} />
            <Area type="monotone" dataKey="rainfall_mm" stroke="#00d4ff" fill="url(#rainGrad)"
                  strokeWidth={2} name="Rainfall (mm)" />
          </AreaChart>
        </ResponsiveContainer>
      </div>

      {/* Multi-metric chart */}
      <div className="chart-container">
        <h3>📊 Environmental Indicators</h3>
        <ResponsiveContainer width="100%" height={160}>
          <LineChart data={data}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="date" tick={{ fontSize: 10 }} tickFormatter={(d) => d.slice(5)} />
            <YAxis tick={{ fontSize: 10 }} />
            <Tooltip content={<CustomTooltip />} />
            <Legend wrapperStyle={{ fontSize: '10px' }} />
            <Line type="monotone" dataKey="soil_moisture_pct" stroke="#f59e0b" strokeWidth={1.5}
                  dot={false} name="Soil Moisture %" />
            <Line type="monotone" dataKey="wind_speed_kmh" stroke="#a855f7" strokeWidth={1.5}
                  dot={false} name="Wind Speed km/h" />
            <Line type="monotone" dataKey="river_level_m" stroke="#ef4444" strokeWidth={2}
                  dot={false} name="River Level (m)" />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
