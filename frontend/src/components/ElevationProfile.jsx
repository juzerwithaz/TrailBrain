import React from 'react';

export default function ElevationProfile({ activeRoute }) {
  if (!activeRoute || !activeRoute.elevation_profile || activeRoute.elevation_profile.length === 0) {
    return (
      <div className="glass-panel" style={{ padding: '16px', color: '#94a3b8', fontSize: '0.8rem', textAlign: 'center' }}>
        No active terrain path selected. Trigger a simulation or click on a target to compute optimal route.
      </div>
    );
  }

  const profile = activeRoute.elevation_profile;
  const elevations = profile.map(p => p.elevation_m);
  const minElev = Math.min(...elevations);
  const maxElev = Math.max(...elevations);
  const elevRange = Math.max(20, maxElev - minElev);

  const width = 450;
  const height = 110;
  const padX = 35;
  const padY = 20;

  // Generate SVG path coordinates
  const points = profile.map((p, idx) => {
    const x = padX + (idx / (profile.length - 1)) * (width - 2 * padX);
    const y = height - padY - ((p.elevation_m - minElev) / elevRange) * (height - 2 * padY);
    return `${x},${y}`;
  });

  const pathD = `M ${points.join(' L ')}`;
  const areaD = `M ${padX},${height - padY} L ${points.join(' L ')} L ${width - padX},${height - padY} Z`;

  const difficultyColors = {
    EASY: '#10b981',
    MODERATE: '#06b6d4',
    STRENUOUS: '#f59e0b',
    TECHNICAL_TERRAIN: '#f43f5e'
  };

  const diffColor = difficultyColors[activeRoute.difficulty_rating] || '#06b6d4';

  return (
    <div className="glass-panel" style={{ padding: '14px 18px', display: 'flex', flexDirection: 'column', gap: '12px' }}>
      {/* Header & Difficulty */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <span style={{ fontSize: '15px' }}>📈</span>
          <span style={{ fontSize: '0.85rem', fontWeight: '700', color: '#f8fafc' }}>
            TERRAIN ELEVATION CROSS-SECTION
          </span>
          <span style={{ fontSize: '0.72rem', color: '#94a3b8' }}>({activeRoute.team_name})</span>
        </div>
        <div style={{
          fontSize: '0.7rem',
          fontWeight: '700',
          padding: '2px 8px',
          borderRadius: '4px',
          background: `${diffColor}22`,
          color: diffColor,
          border: `1px solid ${diffColor}66`
        }}>
          {activeRoute.difficulty_rating.replace('_', ' ')}
        </div>
      </div>

      {/* 6 Key Telemetry Metric Cards */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(6, 1fr)', gap: '8px' }}>
        <div className="glass-card" style={{ padding: '8px', textAlign: 'center' }}>
          <div style={{ fontSize: '0.65rem', color: '#94a3b8' }}>DISTANCE</div>
          <div className="mono" style={{ fontSize: '0.95rem', fontWeight: '700', color: '#38bdf8' }}>
            {activeRoute.distance_km} <span style={{ fontSize: '0.65rem' }}>km</span>
          </div>
        </div>

        <div className="glass-card" style={{ padding: '8px', textAlign: 'center' }}>
          <div style={{ fontSize: '0.65rem', color: '#94a3b8' }}>TOBLER ETA</div>
          <div className="mono" style={{ fontSize: '0.95rem', fontWeight: '700', color: '#34d399' }}>
            {activeRoute.eta_minutes} <span style={{ fontSize: '0.65rem' }}>min</span>
          </div>
        </div>

        <div className="glass-card" style={{ padding: '8px', textAlign: 'center' }}>
          <div style={{ fontSize: '0.65rem', color: '#94a3b8' }}>TOTAL ASCENT</div>
          <div className="mono" style={{ fontSize: '0.95rem', fontWeight: '700', color: '#fb923c' }}>
            +{activeRoute.total_ascent_m} <span style={{ fontSize: '0.65rem' }}>m</span>
          </div>
        </div>

        <div className="glass-card" style={{ padding: '8px', textAlign: 'center' }}>
          <div style={{ fontSize: '0.65rem', color: '#94a3b8' }}>TOTAL DESCENT</div>
          <div className="mono" style={{ fontSize: '0.95rem', fontWeight: '700', color: '#818cf8' }}>
            -{activeRoute.total_descent_m} <span style={{ fontSize: '0.65rem' }}>m</span>
          </div>
        </div>

        <div className="glass-card" style={{ padding: '8px', textAlign: 'center' }}>
          <div style={{ fontSize: '0.65rem', color: '#94a3b8' }}>MAX GRADE</div>
          <div className="mono" style={{ fontSize: '0.95rem', fontWeight: '700', color: '#f43f5e' }}>
            {activeRoute.max_slope_percent}%
          </div>
        </div>

        <div className="glass-card" style={{ padding: '8px', textAlign: 'center' }}>
          <div style={{ fontSize: '0.65rem', color: '#94a3b8' }}>WAYPOINTS</div>
          <div className="mono" style={{ fontSize: '0.95rem', fontWeight: '700', color: '#cbd5e1' }}>
            {profile.length} <span style={{ fontSize: '0.65rem' }}>pts</span>
          </div>
        </div>
      </div>

      {/* SVG Elevation Profile Curve */}
      <div style={{
        background: 'rgba(0, 0, 0, 0.4)',
        borderRadius: '8px',
        padding: '6px',
        border: '1px solid rgba(255, 255, 255, 0.05)'
      }}>
        <svg viewBox={`0 0 ${width} ${height}`} style={{ width: '100%', height: '90px', display: 'block' }}>
          <defs>
            <linearGradient id="elevGrad" x1="0%" y1="0%" x2="0%" y2="100%">
              <stop offset="0%" stopColor="#06b6d4" stopOpacity="0.5" />
              <stop offset="100%" stopColor="#06b6d4" stopOpacity="0.02" />
            </linearGradient>
          </defs>

          {/* Grid lines */}
          <line x1={padX} y1={padY} x2={width - padX} y2={padY} stroke="rgba(255,255,255,0.06)" strokeDasharray="3,3" />
          <line x1={padX} y1={height / 2} x2={width - padX} y2={height / 2} stroke="rgba(255,255,255,0.06)" strokeDasharray="3,3" />
          <line x1={padX} y1={height - padY} x2={width - padX} y2={height - padY} stroke="rgba(255,255,255,0.15)" />

          {/* Elevation Labels */}
          <text x={padX - 6} y={padY + 4} fill="#64748b" fontSize="8" textAnchor="end" className="mono">{Math.round(maxElev)}m</text>
          <text x={padX - 6} y={height - padY + 3} fill="#64748b" fontSize="8" textAnchor="end" className="mono">{Math.round(minElev)}m</text>

          {/* Area & Line */}
          <path d={areaD} fill="url(#elevGrad)" />
          <path d={pathD} fill="none" stroke="#06b6d4" strokeWidth="2.5" strokeLinecap="round" />

          {/* Start Point Marker */}
          {points.length > 0 && (
            <circle cx={points[0].split(',')[0]} cy={points[0].split(',')[1]} r="4" fill="#10b981" stroke="#ffffff" strokeWidth="1.5" />
          )}

          {/* End Target Marker */}
          {points.length > 0 && (
            <circle cx={points[points.length - 1].split(',')[0]} cy={points[points.length - 1].split(',')[1]} r="4" fill="#f43f5e" stroke="#ffffff" strokeWidth="1.5" />
          )}
        </svg>
      </div>
    </div>
  );
}
