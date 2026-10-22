import React, { useState, useEffect, useRef } from 'react';

export default function AlertPanel({ alerts, prediction, onTriggerAlert, selectedDistrict, alertResult }) {
  const [showTriggerModal, setShowTriggerModal] = useState(false);
  const [isSending, setIsSending] = useState(false);
  const [sendResult, setSendResult] = useState(null);
  const [countdown, setCountdown] = useState(null);
  const countdownRef = useRef(null);

  const displayAlerts = alerts && alerts.length > 0 ? alerts : [];

  // Clear result after 8 seconds
  useEffect(() => {
    if (sendResult) {
      const t = setTimeout(() => setSendResult(null), 8000);
      return () => clearTimeout(t);
    }
  }, [sendResult]);

  // Countdown timer
  useEffect(() => {
    if (countdown !== null && countdown > 0) {
      countdownRef.current = setTimeout(() => setCountdown(countdown - 1), 1000);
      return () => clearTimeout(countdownRef.current);
    }
    if (countdown === 0) {
      handleSendAlert();
    }
  }, [countdown]);

  const handleSendAlert = async () => {
    if (!selectedDistrict || !prediction) return;
    setIsSending(true);
    setCountdown(null);
    try {
      const result = await onTriggerAlert({
        district: selectedDistrict,
        risk_score: prediction.combined_risk,
      });
      setSendResult({ success: true, data: result });
    } catch (err) {
      setSendResult({ success: false, error: err.message || 'Alert trigger failed' });
    } finally {
      setIsSending(false);
      setShowTriggerModal(false);
    }
  };

  const cancelCountdown = () => {
    clearTimeout(countdownRef.current);
    setCountdown(null);
    setShowTriggerModal(false);
  };

  const startCountdown = () => {
    setShowTriggerModal(true);
    setCountdown(5);
  };

  const riskPct = prediction ? Math.round(prediction.combined_risk * 100) : 0;
  const riskLevel = prediction?.risk_level || 'safe';

  const smsPreview = prediction
    ? `🚨 DISASTERGUARD ALERT | ${selectedDistrict} | Flood Risk: ${riskPct}% | 48h window | Evacuate: https://disasterguard.app/evacuate/${(selectedDistrict || '').toLowerCase()} | NDRF helpline: 011-24363260`
    : '';

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>

      {/* ====== SUCCESS / ERROR TOAST ====== */}
      {sendResult && (
        <div
          className={sendResult.success ? 'alert-toast-success' : 'alert-toast-error'}
          style={{
            padding: '12px 16px',
            borderRadius: '10px',
            border: `1px solid ${sendResult.success ? '#22c55e' : '#ef4444'}`,
            background: sendResult.success ? 'rgba(34,197,94,0.12)' : 'rgba(239,68,68,0.12)',
            animation: 'fadeSlideIn 0.4s ease',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '4px' }}>
            <span style={{ fontSize: '18px' }}>{sendResult.success ? '✅' : '❌'}</span>
            <strong style={{ fontSize: '13px', color: sendResult.success ? '#22c55e' : '#ef4444' }}>
              {sendResult.success ? 'Alert Triggered Successfully!' : 'Alert Failed'}
            </strong>
          </div>
          {sendResult.success && (
            <div style={{ fontSize: '11px', color: 'var(--color-text-muted)', fontFamily: 'var(--font-mono)' }}>
              <div>📲 SMS: {sendResult.data?.sms?.mock ? 'Simulated (mock mode)' : 'Sent'}</div>
              <div>📱 Push: {sendResult.data?.push?.mock ? 'Simulated (mock mode)' : 'Sent'}</div>
              <div style={{ marginTop: '4px', color: 'var(--color-text-dim)' }}>
                {sendResult.data?.alert?.message}
              </div>
            </div>
          )}
          {!sendResult.success && (
            <div style={{ fontSize: '12px', color: 'var(--color-text-muted)' }}>
              {sendResult.error}
            </div>
          )}
        </div>
      )}

      {/* ====== TRIGGER ALERT BUTTON ====== */}
      {selectedDistrict && prediction && (
        <div
          style={{
            background: riskLevel === 'critical'
              ? 'linear-gradient(135deg, rgba(239,68,68,0.1), rgba(239,68,68,0.05))'
              : 'rgba(255,255,255,0.02)',
            border: `1px solid ${riskLevel === 'critical' ? 'rgba(239,68,68,0.3)' : 'var(--border-subtle)'}`,
            borderRadius: 'var(--radius)',
            padding: '14px',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '10px' }}>
            <div>
              <div style={{ fontFamily: 'var(--font-mono)', fontSize: '11px', textTransform: 'uppercase', letterSpacing: '1px', color: riskLevel === 'critical' ? '#ef4444' : 'var(--color-text-muted)', marginBottom: '2px' }}>
                Emergency Alert System
              </div>
              <div style={{ fontSize: '13px' }}>
                {selectedDistrict} — <span style={{ color: prediction.color, fontWeight: 600 }}>{riskPct}% Risk</span>
              </div>
            </div>
            <div style={{
              width: '40px', height: '40px', borderRadius: '50%',
              background: riskLevel === 'critical' ? 'rgba(239,68,68,0.15)' : riskLevel === 'moderate' ? 'rgba(245,158,11,0.15)' : 'rgba(0,212,255,0.15)',
              display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '18px',
              animation: riskLevel === 'critical' ? 'pulse-badge 1.5s infinite' : 'none',
            }}>
              {riskLevel === 'critical' ? '🔴' : riskLevel === 'moderate' ? '🟡' : '🟢'}
            </div>
          </div>

          {/* SMS Preview */}
          <div style={{
            background: 'rgba(0,0,0,0.3)', borderRadius: '8px', padding: '10px', marginBottom: '10px',
            fontSize: '11px', fontFamily: 'var(--font-mono)', color: 'var(--color-text-muted)',
            lineHeight: 1.6, wordBreak: 'break-word',
          }}>
            <div style={{ fontSize: '9px', textTransform: 'uppercase', letterSpacing: '1px', color: 'var(--color-text-dim)', marginBottom: '6px' }}>
              📨 SMS Preview
            </div>
            {smsPreview}
          </div>

          {/* Channels */}
          <div style={{ display: 'flex', gap: '8px', marginBottom: '12px' }}>
            <div style={{ flex: 1, padding: '8px', background: 'rgba(0,0,0,0.2)', borderRadius: '8px', textAlign: 'center' }}>
              <div style={{ fontSize: '16px', marginBottom: '2px' }}>📲</div>
              <div style={{ fontSize: '10px', color: 'var(--color-text-muted)' }}>Twilio SMS</div>
              <div style={{ fontSize: '9px', color: 'var(--color-safe)' }}>Ready</div>
            </div>
            <div style={{ flex: 1, padding: '8px', background: 'rgba(0,0,0,0.2)', borderRadius: '8px', textAlign: 'center' }}>
              <div style={{ fontSize: '16px', marginBottom: '2px' }}>📱</div>
              <div style={{ fontSize: '10px', color: 'var(--color-text-muted)' }}>Firebase Push</div>
              <div style={{ fontSize: '9px', color: 'var(--color-safe)' }}>Ready</div>
            </div>
            <div style={{ flex: 1, padding: '8px', background: 'rgba(0,0,0,0.2)', borderRadius: '8px', textAlign: 'center' }}>
              <div style={{ fontSize: '16px', marginBottom: '2px' }}>🔔</div>
              <div style={{ fontSize: '10px', color: 'var(--color-text-muted)' }}>NDRF Notify</div>
              <div style={{ fontSize: '9px', color: 'var(--color-safe)' }}>Ready</div>
            </div>
          </div>

          <button
            className="btn-danger"
            onClick={startCountdown}
            disabled={isSending}
            style={{
              width: '100%', padding: '12px', fontSize: '14px', fontWeight: 700,
              letterSpacing: '0.5px', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '8px',
            }}
          >
            {isSending ? (
              <>⏳ Sending Alert...</>
            ) : (
              <>🚨 TRIGGER EMERGENCY ALERT</>
            )}
          </button>
        </div>
      )}

      {/* ====== COUNTDOWN MODAL OVERLAY ====== */}
      {showTriggerModal && countdown !== null && (
        <div style={{
          position: 'fixed', inset: 0, zIndex: 9999,
          background: 'rgba(0,0,0,0.85)', backdropFilter: 'blur(8px)',
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          animation: 'fadeIn 0.3s ease',
        }}>
          <div style={{
            background: 'var(--bg-card)', border: '2px solid rgba(239,68,68,0.5)',
            borderRadius: '20px', padding: '40px', maxWidth: '420px', width: '90%',
            textAlign: 'center', boxShadow: '0 0 60px rgba(239,68,68,0.2)',
            animation: 'scaleIn 0.3s ease',
          }}>
            {/* Siren animation */}
            <div style={{
              width: '80px', height: '80px', borderRadius: '50%', margin: '0 auto 20px',
              background: 'rgba(239,68,68,0.15)', display: 'flex', alignItems: 'center', justifyContent: 'center',
              animation: 'sirenPulse 0.5s infinite alternate',
            }}>
              <span style={{ fontSize: '40px' }}>🚨</span>
            </div>

            <h2 style={{ fontFamily: 'var(--font-mono)', fontSize: '18px', marginBottom: '8px', color: '#ef4444' }}>
              EMERGENCY ALERT
            </h2>
            <p style={{ fontSize: '14px', color: 'var(--color-text-muted)', marginBottom: '6px' }}>
              Sending alert for <strong style={{ color: 'var(--color-text)' }}>{selectedDistrict}</strong>
            </p>
            <p style={{ fontSize: '13px', color: 'var(--color-text-dim)', marginBottom: '24px' }}>
              Flood Risk: <span style={{ color: '#ef4444', fontWeight: 700, fontFamily: 'var(--font-mono)' }}>{riskPct}%</span>
            </p>

            {/* Countdown ring */}
            <div style={{
              width: '120px', height: '120px', margin: '0 auto 24px', position: 'relative',
              borderRadius: '50%', border: '4px solid rgba(239,68,68,0.2)',
            }}>
              <svg width="120" height="120" style={{ position: 'absolute', inset: 0, transform: 'rotate(-90deg)' }}>
                <circle cx="60" cy="60" r="56" fill="none" stroke="#ef4444" strokeWidth="4"
                  strokeDasharray={`${(countdown / 5) * 352} 352`}
                  strokeLinecap="round"
                  style={{ transition: 'stroke-dasharray 1s linear' }}
                />
              </svg>
              <div style={{
                position: 'absolute', inset: 0, display: 'flex', flexDirection: 'column',
                alignItems: 'center', justifyContent: 'center',
              }}>
                <span style={{ fontSize: '40px', fontWeight: 800, fontFamily: 'var(--font-mono)', color: '#ef4444' }}>
                  {countdown}
                </span>
                <span style={{ fontSize: '10px', color: 'var(--color-text-dim)', textTransform: 'uppercase' }}>
                  seconds
                </span>
              </div>
            </div>

            <p style={{ fontSize: '11px', color: 'var(--color-text-dim)', marginBottom: '20px' }}>
              SMS + Push notifications will be dispatched to all registered authorities and NDRF coordinators.
            </p>

            <div style={{ display: 'flex', gap: '10px' }}>
              <button onClick={cancelCountdown} style={{
                flex: 1, padding: '12px', borderRadius: '10px', fontSize: '13px', fontWeight: 600,
                background: 'rgba(255,255,255,0.05)', border: '1px solid var(--border-subtle)',
                color: 'var(--color-text-muted)', cursor: 'pointer',
              }}>
                ✕ Cancel
              </button>
              <button onClick={() => { setCountdown(0); }} style={{
                flex: 1, padding: '12px', borderRadius: '10px', fontSize: '13px', fontWeight: 600,
                background: 'rgba(239,68,68,0.2)', border: '1px solid #ef4444',
                color: '#ef4444', cursor: 'pointer',
              }}>
                ⚡ Send Now
              </button>
            </div>
          </div>
        </div>
      )}

      {/* ====== PREDICTION CARD ====== */}
      {prediction && (
        <div className="alert-card" style={{ borderLeft: `3px solid ${prediction.color}` }}>
          <div className="alert-card-header">
            <h4>{prediction.district}</h4>
            <span className={`risk-badge ${prediction.risk_level}`}>
              {riskPct}%
            </span>
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '6px', margin: '8px 0' }}>
            {['24h', '48h', '72h'].map((w) => (
              <div key={w} style={{ textAlign: 'center', padding: '6px', background: 'rgba(0,0,0,0.2)', borderRadius: '6px' }}>
                <div style={{ fontSize: '10px', color: 'var(--color-text-muted)', fontFamily: 'var(--font-mono)' }}>{w}</div>
                <div style={{ fontSize: '18px', fontWeight: 700, fontFamily: 'var(--font-mono)', color: prediction.lstm_prediction?.[w] >= 0.65 ? '#ef4444' : prediction.lstm_prediction?.[w] >= 0.3 ? '#f59e0b' : '#00d4ff' }}>
                  {Math.round((prediction.lstm_prediction?.[w] || 0) * 100)}%
                </div>
              </div>
            ))}
          </div>
          <div className="alert-card-action">
            {prediction.recommended_action}
          </div>
        </div>
      )}

      {/* ====== ALERT HISTORY ====== */}
      {displayAlerts.length > 0 && (
        <div style={{ fontFamily: 'var(--font-mono)', fontSize: '10px', textTransform: 'uppercase', letterSpacing: '1px', color: 'var(--color-text-dim)', marginTop: '4px' }}>
          Alert History ({displayAlerts.length})
        </div>
      )}
      {displayAlerts.map((alert, i) => (
        <div key={alert.id || i} className={`alert-card ${alert.risk_level}`}>
          <div className="alert-card-header">
            <h4>{alert.district}</h4>
            <span className={`risk-badge ${alert.risk_level}`}>
              {Math.round((alert.risk_score || 0) * 100)}%
            </span>
          </div>
          <div className="alert-card-body">
            {alert.message}
          </div>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: '6px' }}>
            <span style={{ fontSize: '10px', color: 'var(--color-text-dim)', fontFamily: 'var(--font-mono)' }}>
              {alert.type?.toUpperCase() || 'FLOOD'} · {alert.status?.toUpperCase() || 'ACTIVE'}
              {alert.sms_sent !== undefined && (
                <> · SMS {alert.sms_sent ? '✓' : '✗'}</>
              )}
            </span>
            <span style={{ fontSize: '10px', color: 'var(--color-text-dim)' }}>
              {alert.created_at ? new Date(alert.created_at).toLocaleTimeString() : ''}
            </span>
          </div>
        </div>
      ))}

      {displayAlerts.length === 0 && !prediction && (
        <div style={{ textAlign: 'center', padding: '30px 16px', color: 'var(--color-text-dim)', fontSize: '13px' }}>
          <div style={{ fontSize: '32px', marginBottom: '8px' }}>🛡️</div>
          Select a district to view predictions and trigger alerts
        </div>
      )}
    </div>
  );
}
