import React, { useState, useEffect } from 'react';

export default function Navbar({ 
  wsConnected, 
  activeScenario, 
  onTriggerScenario, 
  onReset, 
  onAddHazard, 
  hazardCount,
  missionStatus 
}) {
  const [timeStr, setTimeStr] = useState('');

  useEffect(() => {
    const update = () => {
      const now = new Date();
      setTimeStr(now.toTimeString().split(' ')[0] + ' UTC');
    };
    update();
    const interval = setInterval(update, 1000);
    return () => clearInterval(interval);
  }, []);

  return (
    <header style={{
      height: '64px',
      background: 'rgba(15, 23, 42, 0.95)',
      borderBottom: '1px solid rgba(255, 255, 255, 0.1)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'space-between',
      padding: '0 20px',
      zIndex: 1000
    }}>
      {/* Left: Branding & Status */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <div style={{
            width: '34px',
            height: '34px',
            borderRadius: '8px',
            background: 'linear-gradient(135deg, #0284c7 0%, #06b6d4 100%)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            boxShadow: '0 0 15px rgba(6, 182, 212, 0.5)',
            fontSize: '18px'
          }}>
            🏔️
          </div>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <span style={{ fontSize: '1.15rem', fontWeight: '800', letterSpacing: '-0.02em', color: '#f8fafc' }}>
                TRAIL<span style={{ color: '#06b6d4' }}>BRAIN</span>
              </span>
              <span className="mono" style={{ fontSize: '0.68rem', padding: '1px 5px', background: '#0369a1', borderRadius: '4px', color: '#e0f2fe' }}>
                v2.0 P2
              </span>
            </div>
            <div style={{ fontSize: '0.72rem', color: '#94a3b8' }}>AI SAR Tactical Dispatcher</div>
          </div>
        </div>

        <div style={{ height: '28px', width: '1px', background: 'rgba(255,255,255,0.1)' }} />

        {/* Mission Status Badge */}
        <div className={`badge ${missionStatus === 'DISPATCHED' ? 'badge-alert' : missionStatus === 'ACTIVE' ? 'badge-en-route' : 'badge-idle'}`}>
          <span style={{
            width: '6px',
            height: '6px',
            borderRadius: '50%',
            background: missionStatus === 'DISPATCHED' ? '#f43f5e' : missionStatus === 'ACTIVE' ? '#10b981' : '#94a3b8'
          }} />
          {missionStatus === 'DISPATCHED' ? 'RESCUE DISPATCH ACTIVE' : missionStatus === 'ACTIVE' ? 'SEARCH IN PROGRESS' : 'STANDBY MODE'}
        </div>
      </div>

      {/* Center: Scenario Quick-Triggers */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
        <span style={{ fontSize: '0.75rem', color: '#94a3b8', fontWeight: '600', marginRight: '4px' }}>
          SIMULATE SCENARIO:
        </span>
        <button 
          className={`btn ${activeScenario === 'twin-peaks-ravine' ? 'btn-primary' : 'btn-secondary'}`}
          style={{ fontSize: '0.78rem', padding: '6px 12px' }}
          onClick={() => onTriggerScenario('twin-peaks-ravine')}
        >
          ⛰️ Twin Peaks Hiker
        </button>
        <button 
          className={`btn ${activeScenario === 'sutro-ridge' ? 'btn-primary' : 'btn-secondary'}`}
          style={{ fontSize: '0.78rem', padding: '6px 12px' }}
          onClick={() => onTriggerScenario('sutro-ridge')}
        >
          🌲 Mount Sutro Child
        </button>
        <button 
          className={`btn ${activeScenario === 'glen-canyon-cliff' ? 'btn-primary' : 'btn-secondary'}`}
          style={{ fontSize: '0.78rem', padding: '6px 12px' }}
          onClick={() => onTriggerScenario('glen-canyon-cliff')}
        >
          🧗 Glen Canyon Cliff
        </button>
      </div>

      {/* Right: Actions, Clock & Connection Status */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '14px' }}>
        <button 
          className="btn btn-secondary"
          style={{ fontSize: '0.78rem', padding: '6px 10px', color: '#fb7185', borderColor: 'rgba(244,63,94,0.3)' }}
          onClick={onAddHazard}
        >
          ⚠️ Add Hazard ({hazardCount})
        </button>

        <button 
          className="btn btn-secondary"
          style={{ fontSize: '0.78rem', padding: '6px 10px' }}
          onClick={onReset}
          title="Reset System State"
        >
          🔄 Reset
        </button>

        <div style={{ height: '28px', width: '1px', background: 'rgba(255,255,255,0.1)' }} />

        <div style={{ textAlign: 'right' }}>
          <div className="mono" style={{ fontSize: '0.8rem', fontWeight: '600', color: '#cbd5e1' }}>
            {timeStr}
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '5px', justifyContent: 'flex-end', marginTop: '2px' }}>
            <div style={{
              width: '7px',
              height: '7px',
              borderRadius: '50%',
              background: wsConnected ? '#10b981' : '#f59e0b',
              boxShadow: wsConnected ? '0 0 8px #10b981' : 'none'
            }} />
            <span style={{ fontSize: '0.68rem', color: wsConnected ? '#34d399' : '#f59e0b', fontWeight: '500' }}>
              {wsConnected ? 'LIVE WEBSOCKET' : 'POLLING MODE'}
            </span>
          </div>
        </div>
      </div>
    </header>
  );
}
