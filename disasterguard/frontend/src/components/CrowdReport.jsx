import React, { useState } from 'react';
import { useSubmitCrowdReport } from '../api/disasterApi';

export default function CrowdReport() {
  const [form, setForm] = useState({
    latitude: '', longitude: '', disaster_type: 'flood',
    severity: 3, description: '', reporter_name: '',
  });
  const [submitted, setSubmitted] = useState(false);
  const mutation = useSubmitCrowdReport();

  const detectLocation = () => {
    if (navigator.geolocation) {
      navigator.geolocation.getCurrentPosition(
        (pos) => setForm((f) => ({ ...f, latitude: pos.coords.latitude.toFixed(4), longitude: pos.coords.longitude.toFixed(4) })),
        () => setForm((f) => ({ ...f, latitude: '8.7642', longitude: '78.1348' }))
      );
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      await mutation.mutateAsync({
        ...form,
        latitude: parseFloat(form.latitude) || 8.76,
        longitude: parseFloat(form.longitude) || 78.13,
        severity: parseInt(form.severity),
      });
      setSubmitted(true);
      setTimeout(() => setSubmitted(false), 3000);
      setForm({ latitude: '', longitude: '', disaster_type: 'flood', severity: 3, description: '', reporter_name: '' });
    } catch (err) {
      console.error('Submit failed:', err);
    }
  };

  return (
    <div>
      {submitted && (
        <div style={{
          padding: '10px', background: 'rgba(0,212,255,0.1)', border: '1px solid var(--color-safe)',
          borderRadius: '8px', marginBottom: '12px', fontSize: '13px', color: 'var(--color-safe)',
          textAlign: 'center',
        }}>
          ✅ Report submitted successfully!
        </div>
      )}

      <form className="crowd-form" onSubmit={handleSubmit}>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr auto', gap: '8px' }}>
          <div className="form-group">
            <label>Latitude</label>
            <input className="form-input" type="text" value={form.latitude}
              onChange={(e) => setForm({ ...form, latitude: e.target.value })}
              placeholder="8.7642" />
          </div>
          <div className="form-group">
            <label>Longitude</label>
            <input className="form-input" type="text" value={form.longitude}
              onChange={(e) => setForm({ ...form, longitude: e.target.value })}
              placeholder="78.1348" />
          </div>
          <div className="form-group" style={{ display: 'flex', alignItems: 'flex-end' }}>
            <button type="button" className="btn-primary" onClick={detectLocation}
              style={{ padding: '8px', fontSize: '16px', lineHeight: 1 }} title="Auto-detect GPS">
              📍
            </button>
          </div>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px' }}>
          <div className="form-group">
            <label>Disaster Type</label>
            <select className="form-select" value={form.disaster_type}
              onChange={(e) => setForm({ ...form, disaster_type: e.target.value })}>
              <option value="flood">🌊 Flood</option>
              <option value="cyclone">🌀 Cyclone</option>
              <option value="landslide">⛰️ Landslide</option>
              <option value="other">📌 Other</option>
            </select>
          </div>
          <div className="form-group">
            <label>Severity (1-5)</label>
            <select className="form-select" value={form.severity}
              onChange={(e) => setForm({ ...form, severity: e.target.value })}>
              {[1, 2, 3, 4, 5].map((s) => (
                <option key={s} value={s}>{s} — {['Minor', 'Low', 'Moderate', 'High', 'Critical'][s - 1]}</option>
              ))}
            </select>
          </div>
        </div>

        <div className="form-group">
          <label>Description</label>
          <textarea className="form-textarea" value={form.description}
            onChange={(e) => setForm({ ...form, description: e.target.value })}
            placeholder="Describe what you observe..." />
        </div>

        <div className="form-group">
          <label>Your Name (optional)</label>
          <input className="form-input" type="text" value={form.reporter_name}
            onChange={(e) => setForm({ ...form, reporter_name: e.target.value })}
            placeholder="Anonymous" />
        </div>

        <button type="submit" className="btn-primary" disabled={mutation.isPending}>
          {mutation.isPending ? '⏳ Submitting...' : '📤 Submit Report'}
        </button>
      </form>
    </div>
  );
}
