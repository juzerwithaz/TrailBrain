import React, { useEffect, useRef } from 'react';
import L from 'leaflet';

export default function TacticalMap({ 
  teams, 
  targets, 
  routes, 
  hazards, 
  drone,
  selectedRouteId,
  onSelectRoute,
  onMapClick
}) {
  const mapContainerRef = useRef(null);
  const mapInstanceRef = useRef(null);
  const layersRef = useRef({
    teams: L.layerGroup(),
    targets: L.layerGroup(),
    routes: L.layerGroup(),
    hazards: L.layerGroup(),
    drone: L.layerGroup()
  });

  // 1. Initialize Map
  useEffect(() => {
    if (!mapContainerRef.current || mapInstanceRef.current) return;

    // Center around San Francisco / Twin Peaks SAR area
    const map = L.map(mapContainerRef.current, {
      center: [37.7545, -122.4450],
      zoom: 15,
      zoomControl: false,
      attributionControl: false
    });

    // Dark tactical basemap tiles
    L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
      maxZoom: 19,
      subdomains: 'abcd'
    }).addTo(map);

    // Optional topographic hillshade overlay for terrain feeling
    L.tileLayer('https://{s}.tile.opentopomap.org/{z}/{x}/{y}.png', {
      maxZoom: 17,
      opacity: 0.25
    }).addTo(map);

    L.control.zoom({ position: 'bottomright' }).addTo(map);

    // Add layer groups
    Object.values(layersRef.current).forEach(layer => layer.addTo(map));

    map.on('click', (e) => {
      if (onMapClick) {
        onMapClick(e.latlng.lat, e.latlng.lng);
      }
    });

    mapInstanceRef.current = map;

    return () => {
      map.remove();
      mapInstanceRef.current = null;
    };
  }, []);

  // 2. Render Drone Marker
  useEffect(() => {
    const layer = layersRef.current.drone;
    layer.clearLayers();
    if (!drone || !mapInstanceRef.current) return;

    const droneHtml = `
      <div style="position: relative; width: 32px; height: 32px; display: flex; align-items: center; justify-content: center;">
        <div class="drone-radar-ring"></div>
        <div style="
          width: 24px;
          height: 24px;
          border-radius: 50%;
          background: #0284c7;
          border: 2px solid #38bdf8;
          display: flex;
          align-items: center;
          justify-content: center;
          font-size: 13px;
          box-shadow: 0 0 12px #38bdf8;
          transform: rotate(${drone.heading_deg || 0}deg);
        ">
          🚁
        </div>
      </div>
    `;

    const customIcon = L.divIcon({
      html: droneHtml,
      className: 'custom-drone-icon',
      iconSize: [32, 32],
      iconAnchor: [16, 16]
    });

    const marker = L.marker([drone.lat, drone.lon], { icon: customIcon });
    marker.bindPopup(`
      <div style="padding: 4px; font-size: 12px;">
        <b style="color: #38bdf8;">🚁 Recon Drone Alpha</b><br/>
        <b>Altitude:</b> ${drone.alt_m}m AGL<br/>
        <b>Battery:</b> ${drone.battery_pct}%<br/>
        <b>Status:</b> ${drone.status || 'SEARCHING'}<br/>
        <b>Coordinates:</b> ${drone.lat.toFixed(4)}, ${drone.lon.toFixed(4)}
      </div>
    `);
    layer.addLayer(marker);
  }, [drone]);

  // 3. Render SAR Teams
  useEffect(() => {
    const layer = layersRef.current.teams;
    layer.clearLayers();
    if (!teams || !mapInstanceRef.current) return;

    const typeIcons = {
      FOOT_PATROL: '🥾',
      ALPINE_RESCUE: '🧗',
      CANINE_SEARCH: '🐕',
      VEHICLE: '🚜'
    };

    teams.forEach(team => {
      const isEnRoute = team.status === 'EN_ROUTE';
      const teamHtml = `
        <div style="
          display: flex;
          align-items: center;
          gap: 4px;
          background: ${isEnRoute ? 'rgba(16, 185, 129, 0.9)' : 'rgba(30, 41, 59, 0.9)'};
          border: 1px solid ${isEnRoute ? '#34d399' : '#64748b'};
          padding: 2px 8px;
          border-radius: 12px;
          color: white;
          font-size: 11px;
          font-weight: 700;
          white-space: nowrap;
          box-shadow: 0 2px 8px rgba(0,0,0,0.5);
        ">
          <span>${typeIcons[team.type] || '🥾'}</span>
          <span>${team.name.replace('SAR Team ', '')}</span>
        </div>
      `;

      const customIcon = L.divIcon({
        html: teamHtml,
        className: 'custom-team-icon',
        iconSize: [80, 24],
        iconAnchor: [40, 12]
      });

      const marker = L.marker([team.lat, team.lon], { icon: customIcon });
      marker.bindPopup(`
        <div style="padding: 4px; font-size: 12px;">
          <b style="color: #34d399;">${team.name}</b> (${team.type})<br/>
          <b>Status:</b> <span style="color: ${isEnRoute ? '#34d399' : '#94a3b8'}">${team.status}</span><br/>
          <b>Personnel:</b> ${team.personnel_count} rescuers<br/>
          <b>Equipment:</b> ${team.equipment.join(', ')}<br/>
          <b>Location:</b> ${team.lat.toFixed(4)}, ${team.lon.toFixed(4)}
        </div>
      `);
      layer.addLayer(marker);
    });
  }, [teams]);

  // 4. Render Targets
  useEffect(() => {
    const layer = layersRef.current.targets;
    layer.clearLayers();
    if (!targets || !mapInstanceRef.current) return;

    targets.forEach(target => {
      const targetHtml = `
        <div style="position: relative; width: 32px; height: 32px; display: flex; align-items: center; justify-content: center;">
          <div style="
            position: absolute;
            width: 32px;
            height: 32px;
            border-radius: 50%;
            background: rgba(244, 63, 94, 0.25);
            border: 1px solid #f43f5e;
            animation: pulse-glow 1.5s infinite;
          "></div>
          <div style="
            width: 20px;
            height: 20px;
            border-radius: 50%;
            background: #e11d48;
            border: 2px solid #ffffff;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 11px;
            box-shadow: 0 0 12px #f43f5e;
          ">
            🎯
          </div>
        </div>
      `;

      const customIcon = L.divIcon({
        html: targetHtml,
        className: 'custom-target-icon',
        iconSize: [32, 32],
        iconAnchor: [16, 16]
      });

      const marker = L.marker([target.lat, target.lon], { icon: customIcon });
      marker.bindPopup(`
        <div style="padding: 4px; font-size: 12px;">
          <b style="color: #fb7185;">🚨 ${target.name}</b><br/>
          <b>Confidence:</b> ${(target.confidence * 100).toFixed(0)}% AI Match<br/>
          <b>Sensor:</b> ${target.thermal ? '🔥 FLIR Thermal Infrared' : '📷 High-Res RGB'}<br/>
          <b>Assigned Team:</b> ${target.assigned_team_id || 'Auto-Dispatching'}<br/>
          <b>Coordinates:</b> ${target.lat.toFixed(5)}, ${target.lon.toFixed(5)}
        </div>
      `);
      layer.addLayer(marker);
    });
  }, [targets]);

  // 5. Render Hazards
  useEffect(() => {
    const layer = layersRef.current.hazards;
    layer.clearLayers();
    if (!hazards || !mapInstanceRef.current) return;

    hazards.forEach(hazard => {
      const circle = L.circle([hazard.lat, hazard.lon], {
        radius: hazard.radius_m || 60,
        color: '#f43f5e',
        weight: 2,
        dashArray: '4, 6',
        fillColor: '#f43f5e',
        fillOpacity: 0.2
      });

      circle.bindPopup(`
        <div style="padding: 4px; font-size: 12px;">
          <b style="color: #fb7185;">⚠️ Keep-Out Hazard Zone</b><br/>
          <b>Type:</b> ${hazard.name}<br/>
          <b>Radius:</b> ${hazard.radius_m}m buffer<br/>
          <i>A* terrain pathfinder will route around this zone.</i>
        </div>
      `);
      layer.addLayer(circle);
    });
  }, [hazards]);

  // 6. Render A* Terrain Routes
  useEffect(() => {
    const layer = layersRef.current.routes;
    layer.clearLayers();
    if (!routes || !mapInstanceRef.current) return;

    routes.forEach(routeObj => {
      if (!routeObj.route || routeObj.route.length === 0) return;

      const isSelected = !selectedRouteId || selectedRouteId === routeObj.id;
      const polyline = L.polyline(routeObj.route, {
        color: isSelected ? '#06b6d4' : '#64748b',
        weight: isSelected ? 5 : 3,
        opacity: isSelected ? 0.95 : 0.6,
        dashArray: isSelected ? null : '6, 6'
      });

      polyline.bindPopup(`
        <div style="padding: 4px; font-size: 12px;">
          <b style="color: #06b6d4;">Terrain A* Path: ${routeObj.team_name}</b><br/>
          <b>Distance:</b> ${routeObj.distance_km} km<br/>
          <b>Tobler ETA:</b> ${routeObj.eta_minutes} mins<br/>
          <b>Elevation Gain:</b> +${routeObj.total_ascent_m}m / -${routeObj.total_descent_m}m<br/>
          <b>Max Grade:</b> ${routeObj.max_slope_percent}% (${routeObj.difficulty_rating})
        </div>
      `);

      polyline.on('click', () => {
        if (onSelectRoute) onSelectRoute(routeObj.id);
      });

      layer.addLayer(polyline);

      // Add start and end point markers
      if (routeObj.route.length > 0) {
        const startPoint = routeObj.route[0];
        const endPoint = routeObj.route[routeObj.route.length - 1];

        const startMarker = L.circleMarker(startPoint, {
          radius: 5,
          color: '#10b981',
          fillColor: '#34d399',
          fillOpacity: 1
        });
        layer.addLayer(startMarker);

        const endMarker = L.circleMarker(endPoint, {
          radius: 5,
          color: '#f43f5e',
          fillColor: '#fb7185',
          fillOpacity: 1
        });
        layer.addLayer(endMarker);
      }
    });

    // Auto-fit bounds if we have routes
    if (routes.length > 0 && routes[0].route && routes[0].route.length > 0) {
      const bounds = L.latLngBounds(routes[0].route);
      mapInstanceRef.current.fitBounds(bounds, { padding: [60, 60], maxZoom: 16 });
    }
  }, [routes, selectedRouteId]);

  return (
    <div style={{ position: 'relative', width: '100%', height: '100%' }}>
      <div ref={mapContainerRef} style={{ width: '100%', height: '100%' }} />

      {/* Map Overlay Badge */}
      <div style={{
        position: 'absolute',
        top: '16px',
        left: '16px',
        zIndex: 500,
        background: 'rgba(15, 23, 42, 0.85)',
        backdropFilter: 'blur(8px)',
        padding: '6px 12px',
        borderRadius: '8px',
        border: '1px solid rgba(255, 255, 255, 0.1)',
        fontSize: '0.75rem',
        color: '#94a3b8',
        display: 'flex',
        alignItems: 'center',
        gap: '8px'
      }}>
        <span>🗺️ <b>DEM Elevation Grid:</b> SF Twin Peaks (10m Resolution)</span>
        <span style={{ color: '#64748b' }}>|</span>
        <span style={{ color: '#06b6d4' }}>Active Pathfinding: <b>Tobler A*</b></span>
      </div>
    </div>
  );
}
