import React, { useState, useEffect } from 'react';

export default function DroneHUD({ drone, targets }) {
  const [thermalMode, setThermalMode] = useState(true);
  const [frameTick, setFrameTick] = useState(0);

  useEffect(() => {
    const interval = setInterval(() => {
      setFrameTick(t => (t + 1) % 1000);
    }, 100);
    return () => clearInterval(interval);
  }, []);

  const hasTarget = targets && targets.length > 0;
  const latestTarget = hasTarget ? targets[targets.length - 1] : null;

  return (
    <div className="glass-panel" style={{
      width: '320px',
      overflow: 'hidden',
      display: 'flex',
      flexDirection: 'column'
    }}>
      {/* HUD Header */}
      <div style={{
        padding: '10px 14px',
        borderBottom: '1px solid rgba(255, 255, 255, 0.08)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        background: 'rgba(0, 0, 0, 0.3)'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
          <span style={{ fontSize: '13px' }}>📹</span>
          <span style={{ fontSize: '0.82rem', fontWeight: '700', letterSpacing: '0.04em', color: '#f8fafc' }}>
            DRONE OPTICAL / FLIR HUD
          </span>
        </div>
        <button
          className="btn btn-secondary"
          style={{ fontSize: '0.68rem', padding: '2px 8px' }}
          onClick={() => setThermalMode(!thermalMode)}
        >
          {thermalMode ? '🔥 FLIR THERMAL' : '📷 RGB OPTICAL'}
        </button>
      </div>

      {/* Simulated Video Canvas Viewport */}
      <div style={{
        position: 'relative',
        height: '190px',
        background: thermalMode 
          ? 'radial-gradient(ellipse at center, #1e1b4b 0%, #030712 100%)' 
          : 'linear-gradient(180deg, #1e293b 0%, #0f172a 100%)',
        overflow: 'hidden',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center'
      }}>
        {/* Scanlines / Noise Overlay */}
        <div style={{
          position: 'absolute',
          inset: 0,
          backgroundImage: 'linear-gradient(rgba(18, 16, 16, 0) 50%, rgba(0, 0, 0, 0.25) 50%)',
          backgroundSize: '100% 4px',
          pointerEvents: 'none',
          opacity: 0.6
        }} />

        {/* Tactical Crosshairs */}
        <div style={{
          position: 'absolute',
          width: '60px',
          height: '60px',
          border: '1px solid rgba(6, 182, 212, 0.4)',
          borderRadius: '50%',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center'
        }}>
          <div style={{ width: '8px', height: '1px', background: '#06b6d4' }} />
          <div style={{ height: '8px', width: '1px', background: '#06b6d4', position: 'absolute' }} />
        </div>

        {/* Pitch Angle Ladder Simulation */}
        <div className="mono" style={{
          position: 'absolute',
          left: '12px',
          top: '40px',
          fontSize: '0.65rem',
          color: 'rgba(56, 189, 248, 0.7)',
          lineHeight: '1.6'
        }}>
          <div>+20 ──</div>
          <div>+10 ────</div>
          <div>-00 ──────</div>
          <div>-10 ────</div>
          <div>-20 ──</div>
        </div>

        {/* Detected Target Bounding Box Overlay */}
        {latestTarget && (
          <div style={{
            position: 'absolute',
            width: '70px',
            height: '85px',
            border: '2px solid #f43f5e',
            borderRadius: '4px',
            top: '45px',
            left: '120px',
            boxShadow: '0 0 15px rgba(244, 63, 94, 0.6)',
            display: 'flex',
            flexDirection: 'column',
            justifyContent: 'space-between',
            padding: '2px',
            animation: 'pulse-border 1.5s infinite'
          }}>
            <div style={{
              background: '#e11d48',
              color: 'white',
              fontSize: '0.58rem',
              fontWeight: '700',
              padding: '1px 3px',
              borderRadius: '2px',
              width: 'fit-content'
            }}>
              PERSON [{(latestTarget.confidence * 100).toFixed(0)}%]
            </div>

            {/* Thermal Hotspot Simulation */}
            <div style={{
              alignSelf: 'center',
              width: '30px',
              height: '45px',
              borderRadius: '40%',
              background: thermalMode ? 'radial-gradient(circle, #ffffff 0%, #fb923c 60%, transparent 100%)' : 'rgba(255,255,255,0.2)',
              filter: 'blur(2px)'
            }} />

            <div className="mono" style={{
              background: 'rgba(0,0,0,0.8)',
              color: '#38bdf8',
              fontSize: '0.55rem',
              textAlign: 'center'
            }}>
              36.4°C | GEO-LOCK
            </div>
          </div>
        )}

        {/* Live Top HUD Telemetry */}
        <div className="mono" style={{
          position: 'absolute',
          top: '8px',
          left: '12px',
          right: '12px',
          display: 'flex',
          justifyContent: 'space-between',
          fontSize: '0.68rem',
          color: '#38bdf8',
          textShadow: '0 0 4px rgba(6,182,212,0.8)'
        }}>
          <span>ALT: <b>{drone?.alt_m || 85}m</b> AGL</span>
          <span>SPD: <b>18.4 km/h</b></span>
          <span>HDG: <b>{drone?.heading_deg || 55}°</b></span>
        </div>

        {/* Live Bottom HUD Telemetry */}
        <div className="mono" style={{
          position: 'absolute',
          bottom: '8px',
          left: '12px',
          right: '12px',
          display: 'flex',
          justifyContent: 'space-between',
          fontSize: '0.65rem',
          color: '#94a3b8'
        }}>
          <span>LAT: {drone?.lat?.toFixed(4) || '37.7558'}</span>
          <span>LON: {drone?.lon?.toFixed(4) || '-122.4442'}</span>
          <span style={{ color: '#10b981' }}>BAT: {drone?.battery_pct || 88}%</span>
        </div>
      </div>

      {/* Target Info Summary */}
      <div style={{ padding: '10px 14px', background: 'rgba(15, 23, 42, 0.6)', fontSize: '0.75rem' }}>
        {latestTarget ? (
          <div>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '4px' }}>
              <span style={{ fontWeight: '700', color: '#fb7185' }}>🚨 {latestTarget.name}</span>
              <span className="badge badge-alert">CONFIRMED</span>
            </div>
            <div className="mono" style={{ fontSize: '0.7rem', color: '#94a3b8' }}>
              Target GPS: {latestTarget.lat.toFixed(5)}, {latestTarget.lon.toFixed(5)}
            </div>
          </div>
        ) : (
          <div style={{ color: '#94a3b8', fontStyle: 'italic', textAlign: 'center' }}>
            No target in current optical frame. Sweep in progress.
          </div>
        )}
      </div>
    </div>
  );
}
