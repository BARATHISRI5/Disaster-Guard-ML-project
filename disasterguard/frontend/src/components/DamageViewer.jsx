import React, { useState, useRef, useCallback } from 'react';

export default function DamageViewer({ damageData, district }) {
  const [sliderPos, setSliderPos] = useState(50);
  const containerRef = useRef(null);

  const handleMouseMove = useCallback((e) => {
    if (!containerRef.current) return;
    const rect = containerRef.current.getBoundingClientRect();
    const x = ((e.clientX - rect.left) / rect.width) * 100;
    setSliderPos(Math.max(0, Math.min(100, x)));
  }, []);

  if (!damageData) {
    return (
      <div className="damage-viewer">
        <h3 style={{ fontFamily: 'var(--font-mono)', fontSize: '11px', textTransform: 'uppercase', letterSpacing: '1.5px', color: 'var(--color-safe)', marginBottom: '12px' }}>
          🛰️ Damage Assessment
        </h3>
        <div style={{ textAlign: 'center', padding: '20px', color: 'var(--color-text-dim)', fontSize: '13px' }}>
          Select a district to compare pre/post satellite imagery
        </div>
      </div>
    );
  }

  const preCoverage = damageData.pre_event?.water_coverage_pct || 0;
  const postCoverage = damageData.post_event?.water_coverage_pct || 0;

  return (
    <div className="damage-viewer">
      <h3 style={{ fontFamily: 'var(--font-mono)', fontSize: '11px', textTransform: 'uppercase', letterSpacing: '1.5px', color: 'var(--color-safe)', marginBottom: '12px' }}>
        🛰️ Damage Assessment — {district}
      </h3>

      {/* Comparison slider */}
      <div
        ref={containerRef}
        className="comparison-slider"
        onMouseMove={handleMouseMove}
        onTouchMove={(e) => {
          const touch = e.touches[0];
          handleMouseMove({ clientX: touch.clientX });
        }}
      >
        {/* Pre-event (left) */}
        <div style={{
          position: 'absolute', inset: 0,
          background: 'linear-gradient(135deg, #1a3a2a 0%, #0d2818 50%, #1a3a2a 100%)',
          clipPath: `inset(0 ${100 - sliderPos}% 0 0)`,
        }}>
          <div style={{ position: 'absolute', inset: 0, opacity: 0.3, background: `repeating-linear-gradient(45deg, transparent, transparent 10px, rgba(0,180,80,0.1) 10px, rgba(0,180,80,0.1) 20px)` }} />
          <span className="comparison-label pre">PRE-FLOOD</span>
        </div>

        {/* Post-event (right) */}
        <div style={{
          position: 'absolute', inset: 0,
          background: 'linear-gradient(135deg, #1a2040 0%, #0d1830 50%, #2a1525 100%)',
          clipPath: `inset(0 0 0 ${sliderPos}%)`,
        }}>
          <div style={{ position: 'absolute', inset: 0, opacity: 0.4, background: `repeating-linear-gradient(-45deg, transparent, transparent 8px, rgba(0,100,200,0.15) 8px, rgba(0,100,200,0.15) 16px)` }} />
          <span className="comparison-label post">POST-FLOOD</span>
        </div>

        {/* Slider line */}
        <div style={{
          position: 'absolute', top: 0, bottom: 0, left: `${sliderPos}%`,
          width: '2px', background: '#ffffff', zIndex: 3,
          boxShadow: '0 0 10px rgba(255,255,255,0.5)',
        }}>
          <div style={{
            position: 'absolute', top: '50%', left: '50%', transform: 'translate(-50%, -50%)',
            width: '24px', height: '24px', borderRadius: '50%', background: 'white',
            display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '12px',
            boxShadow: '0 2px 8px rgba(0,0,0,0.4)',
          }}>⟺</div>
        </div>
      </div>

      {/* Stats */}
      <div className="damage-stats">
        <div className="damage-stat">
          <div className="value" style={{ color: 'var(--color-safe)' }}>{preCoverage}%</div>
          <div className="label">Pre-flood Water</div>
        </div>
        <div className="damage-stat">
          <div className="value" style={{ color: 'var(--color-critical)' }}>{postCoverage}%</div>
          <div className="label">Post-flood Water</div>
        </div>
        <div className="damage-stat">
          <div className="value" style={{ color: 'var(--color-moderate)' }}>{damageData.water_expansion_factor}x</div>
          <div className="label">Expansion</div>
        </div>
        <div className="damage-stat">
          <div className="value" style={{ color: 'var(--color-critical)' }}>{damageData.estimated_affected_area_sqkm}</div>
          <div className="label">Affected km²</div>
        </div>
      </div>
    </div>
  );
}
