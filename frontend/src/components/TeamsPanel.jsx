import React from 'react';

export default function TeamsPanel({ teams, activeRoute, onSelectTeam }) {
  const typeIcons = {
    FOOT_PATROL: '🥾',
    ALPINE_RESCUE: '🧗',
    CANINE_SEARCH: '🐕',
    VEHICLE: '🚜'
  };

  return (
    <div className="glass-panel" style={{
      width: '320px',
      display: 'flex',
      flexDirection: 'column',
      overflow: 'hidden'
    }}>
      {/* Header */}
      <div style={{
        padding: '10px 14px',
        borderBottom: '1px solid rgba(255, 255, 255, 0.08)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        background: 'rgba(0, 0, 0, 0.2)'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
          <span style={{ fontSize: '14px' }}>👥</span>
          <span style={{ fontSize: '0.82rem', fontWeight: '700', letterSpacing: '0.04em', color: '#f8fafc' }}>
            GROUND RESCUE UNITS ({teams?.length || 0})
          </span>
        </div>
      </div>

      {/* Teams List */}
      <div style={{ padding: '10px', display: 'flex', flexDirection: 'column', gap: '8px', overflowY: 'auto', maxHeight: '230px' }}>
        {teams && teams.map(team => {
          const isAssigned = activeRoute && activeRoute.team_id === team.id;
          const isEnRoute = team.status === 'EN_ROUTE';

          return (
            <div 
              key={team.id}
              className="glass-card"
              style={{
                padding: '10px',
                borderColor: isAssigned ? '#06b6d4' : isEnRoute ? '#10b981' : 'rgba(255, 255, 255, 0.08)',
                boxShadow: isAssigned ? '0 0 12px rgba(6, 182, 212, 0.25)' : 'none',
                cursor: 'pointer'
              }}
              onClick={() => onSelectTeam && onSelectTeam(team.id)}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '4px' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                  <span style={{ fontSize: '14px' }}>{typeIcons[team.type] || '🥾'}</span>
                  <span style={{ fontWeight: '700', fontSize: '0.82rem', color: '#f8fafc' }}>{team.name}</span>
                </div>
                <span className={`badge ${isEnRoute ? 'badge-en-route' : 'badge-idle'}`}>
                  {team.status}
                </span>
              </div>

              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.7rem', color: '#94a3b8', marginBottom: '6px' }}>
                <span>Type: <b>{team.type.replace('_', ' ')}</b></span>
                <span>Team: <b>{team.personnel_count} SAR</b></span>
              </div>

              <div style={{ display: 'flex', flexWrap: 'wrap', gap: '4px' }}>
                {team.equipment && team.equipment.map((eq, i) => (
                  <span key={i} style={{
                    fontSize: '0.62rem',
                    background: 'rgba(255, 255, 255, 0.05)',
                    padding: '2px 5px',
                    borderRadius: '3px',
                    color: '#cbd5e1'
                  }}>
                    {eq}
                  </span>
                ))}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
