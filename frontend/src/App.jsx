import React, { useState, useEffect, useRef } from 'react';
import Navbar from './components/Navbar.jsx';
import TacticalMap from './components/TacticalMap.jsx';
import DroneHUD from './components/DroneHUD.jsx';
import TeamsPanel from './components/TeamsPanel.jsx';
import ElevationProfile from './components/ElevationProfile.jsx';

const BACKEND_HTTP = 'http://localhost:8000';
const BACKEND_WS = 'ws://localhost:8000/ws/dispatch';

export default function App() {
  const [teams, setTeams] = useState([]);
  const [targets, setTargets] = useState([]);
  const [routes, setRoutes] = useState([]);
  const [hazards, setHazards] = useState([]);
  const [drone, setDrone] = useState(null);
  const [selectedRouteId, setSelectedRouteId] = useState(null);
  const [activeScenario, setActiveScenario] = useState(null);
  const [wsConnected, setWsConnected] = useState(false);
  const [alertBanner, setAlertBanner] = useState(null);

  const wsRef = useRef(null);

  // 1. WebSocket Setup with Auto-Reconnect & Polling Fallback
  useEffect(() => {
    let reconnectTimeout = null;

    const connectWs = () => {
      try {
        const ws = new WebSocket(BACKEND_WS);
        wsRef.current = ws;

        ws.onopen = () => {
          setWsConnected(true);
        };

        ws.onmessage = (event) => {
          try {
            const msg = JSON.parse(event.data);
            handleWsMessage(msg);
          } catch (err) {
            console.error('Error parsing WS message:', err);
          }
        };

        ws.onclose = () => {
          setWsConnected(false);
          reconnectTimeout = setTimeout(connectWs, 3000);
        };

        ws.onerror = () => {
          setWsConnected(false);
          ws.close();
        };
      } catch (e) {
        setWsConnected(false);
        reconnectTimeout = setTimeout(connectWs, 3000);
      }
    };

    connectWs();

    // Initial HTTP fetch to prime state immediately
    fetchStateHttp();

    return () => {
      if (wsRef.current) wsRef.current.close();
      if (reconnectTimeout) clearTimeout(reconnectTimeout);
    };
  }, []);

  const handleWsMessage = (msg) => {
    switch (msg.type) {
      case 'INIT_STATE':
        setTeams(msg.data.teams || []);
        setTargets(msg.data.targets || []);
        setRoutes(msg.data.routes || []);
        setHazards(msg.data.hazards || []);
        setDrone(msg.data.drone || null);
        if (msg.data.routes && msg.data.routes.length > 0) {
          setSelectedRouteId(msg.data.routes[msg.data.routes.length - 1].id);
        }
        break;

      case 'DETECTION_RECEIVED':
        setTargets(prev => [...prev.filter(t => t.id !== msg.data.target.id), msg.data.target]);
        setTeams(prev => prev.map(t => t.id === msg.data.team.id ? msg.data.team : t));
        setRoutes(prev => [...prev.filter(r => r.id !== msg.data.route.id), msg.data.route]);
        setSelectedRouteId(msg.data.route.id);

        showAlert(
          `🚨 NEW TARGET DETECTED: ${msg.data.target.name}! Auto-dispatched ${msg.data.team.name}.`,
          'danger'
        );
        break;

      case 'TEAM_LOCATION_UPDATED':
        setTeams(prev => prev.map(t => t.id === msg.data.team.id ? msg.data.team : t));
        if (msg.data.active_route) {
          setRoutes(prev => prev.map(r => r.id === msg.data.active_route.id ? msg.data.active_route : r));
        }
        break;

      case 'HAZARD_UPDATED':
        setHazards(msg.data.hazards || []);
        break;

      case 'DRONE_TELEMETRY':
        setDrone(msg.data);
        break;

      default:
        break;
    }
  };

  const fetchStateHttp = async () => {
    try {
      const res = await fetch(`${BACKEND_HTTP}/api/state`);
      if (res.ok) {
        const data = await res.json();
        setTeams(data.teams || []);
        setTargets(data.targets || []);
        setRoutes(data.routes || []);
        setHazards(data.hazards || []);
        setDrone(data.drone || null);
        if (data.routes && data.routes.length > 0) {
          setSelectedRouteId(data.routes[data.routes.length - 1].id);
        }
      }
    } catch (e) {
      console.warn('Backend not yet reachable on HTTP:', e.message);
    }
  };

  const showAlert = (message, type = 'info') => {
    setAlertBanner({ message, type });
    setTimeout(() => setAlertBanner(null), 5000);
  };

  // 2. Scenario Trigger Action
  const handleTriggerScenario = async (scenarioKey) => {
    setActiveScenario(scenarioKey);
    try {
      const res = await fetch(`${BACKEND_HTTP}/api/simulate-detection?scenario=${scenarioKey}`, {
        method: 'POST'
      });
      if (res.ok) {
        const data = await res.json();
        setSelectedRouteId(data.route.id);
        fetchStateHttp();
      }
    } catch (err) {
      console.error('Failed to trigger scenario:', err);
      showAlert('Failed to contact backend API.', 'danger');
    }
  };

  // 3. Reset Mission Action
  const handleReset = async () => {
    try {
      await fetch(`${BACKEND_HTTP}/api/reset`, { method: 'POST' });
      setActiveScenario(null);
      setSelectedRouteId(null);
      fetchStateHttp();
      showAlert('Mission state reset to initial conditions.', 'info');
    } catch (err) {
      console.error('Failed to reset:', err);
    }
  };

  // 4. Add Dynamic Hazard Action
  const handleAddHazard = async () => {
    try {
      const res = await fetch(`${BACKEND_HTTP}/api/hazards`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          lat: 37.7550,
          lon: -122.4445,
          radius_m: 60.0,
          name: 'Rockfall / Cliff Hazard'
        })
      });
      if (res.ok) {
        fetchStateHttp();
        showAlert('⚠️ Added Cliff Keep-Out Hazard Zone. Recomputing terrain paths.', 'danger');
      }
    } catch (err) {
      console.error('Failed to add hazard:', err);
    }
  };

  const activeRoute = routes.find(r => r.id === selectedRouteId) || routes[routes.length - 1] || null;
  const missionStatus = targets.length > 0 ? 'DISPATCHED' : drone ? 'ACTIVE' : 'IDLE';

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100vh', width: '100vw', background: 'var(--bg-primary)' }}>
      {/* Top Tactical Navigation Header */}
      <Navbar
        wsConnected={wsConnected}
        activeScenario={activeScenario}
        onTriggerScenario={handleTriggerScenario}
        onReset={handleReset}
        onAddHazard={handleAddHazard}
        hazardCount={hazards.length}
        missionStatus={missionStatus}
      />

      {/* Emergency Alert Banner */}
      {alertBanner && (
        <div style={{
          background: alertBanner.type === 'danger' ? 'rgba(225, 29, 72, 0.9)' : 'rgba(2, 132, 199, 0.9)',
          color: 'white',
          padding: '8px 20px',
          fontSize: '0.82rem',
          fontWeight: '700',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          boxShadow: '0 4px 12px rgba(0,0,0,0.4)',
          zIndex: 999
        }}>
          <span>{alertBanner.message}</span>
          <button 
            style={{ background: 'none', border: 'none', color: 'white', cursor: 'pointer', fontWeight: 'bold' }}
            onClick={() => setAlertBanner(null)}
          >
            ✕
          </button>
        </div>
      )}

      {/* Main Workspace Layout */}
      <div style={{ flex: 1, display: 'flex', position: 'relative', overflow: 'hidden' }}>
        {/* Left/Center: Tactical Map Area */}
        <div style={{ flex: 1, position: 'relative', height: '100%' }}>
          <TacticalMap
            teams={teams}
            targets={targets}
            routes={routes}
            hazards={hazards}
            drone={drone}
            selectedRouteId={selectedRouteId}
            onSelectRoute={(id) => setSelectedRouteId(id)}
          />

          {/* Bottom Floating Elevation Profile */}
          <div style={{
            position: 'absolute',
            bottom: '16px',
            left: '16px',
            right: '16px',
            maxWidth: '750px',
            zIndex: 400
          }}>
            <ElevationProfile activeRoute={activeRoute} />
          </div>
        </div>

        {/* Right Sidebar: Optical HUD + Teams List */}
        <div style={{
          width: '340px',
          padding: '16px',
          display: 'flex',
          flexDirection: 'column',
          gap: '14px',
          background: 'rgba(8, 12, 20, 0.75)',
          backdropFilter: 'blur(12px)',
          borderLeft: '1px solid rgba(255, 255, 255, 0.08)',
          overflowY: 'auto',
          zIndex: 500
        }}>
          <DroneHUD drone={drone} targets={targets} />
          <TeamsPanel teams={teams} activeRoute={activeRoute} />
        </div>
      </div>
    </div>
  );
}
