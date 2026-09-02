import sys
import os
from pathlib import Path
import time
import asyncio
from typing import List, Optional, Dict, Any
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# Ensure routing module is importable
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "routing"))
from engine import compute_route, haversine_distance

from config import (
    DEFAULT_TEAMS,
    SLOPE_PENALTY_FACTOR,
    OBSTACLE_PENALTY_MULTIPLIER,
    SLOPE_THRESHOLD,
    BASE_SPEED_KMH,
    SIMULATION_SCENARIOS
)

app = FastAPI(
    title="TrailBrain Dispatch & Autonomous Routing API",
    description="Real-time multi-team SAR dispatch and 3D terrain-aware navigation platform.",
    version="2.0.0"
)

# Enable CORS for frontend clients
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==========================================
# In-Memory State Store
# ==========================================
class SystemState:
    def __init__(self):
        self.teams: Dict[str, Dict[str, Any]] = {
            team["id"]: dict(team) for team in DEFAULT_TEAMS
        }
        self.targets: List[Dict[str, Any]] = []
        self.routes: Dict[str, Dict[str, Any]] = {}
        self.hazards: List[Dict[str, Any]] = []
        self.drone_telemetry: Dict[str, Any] = {
            "lat": 37.7550,
            "lon": -122.4450,
            "alt_m": 120.0,
            "battery_pct": 88,
            "heading_deg": 45,
            "gimbal_pitch_deg": -55.0,
            "status": "SEARCHING"
        }

    def reset(self):
        self.__init__()

state = SystemState()

# ==========================================
# WebSocket Connection Manager
# ==========================================
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        # Send initial state snapshot on connection
        await websocket.send_json({
            "type": "INIT_STATE",
            "data": {
                "teams": list(state.teams.values()),
                "targets": state.targets,
                "routes": list(state.routes.values()),
                "hazards": state.hazards,
                "drone": state.drone_telemetry
            }
        })

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, event_type: str, data: Any):
        payload = {"type": event_type, "data": data, "timestamp": time.time()}
        dead_connections = []
        for connection in self.active_connections:
            try:
                await connection.send_json(payload)
            except Exception:
                dead_connections.append(connection)
        for dead in dead_connections:
            self.disconnect(dead)

manager = ConnectionManager()

# ==========================================
# Data Models
# ==========================================
class DetectionPayload(BaseModel):
    lat: float = Field(..., description="Target Latitude")
    lon: float = Field(..., description="Target Longitude")
    confidence: float = Field(default=0.95, description="AI model confidence score")
    timestamp: Optional[float] = Field(default_factory=time.time)
    target_id: Optional[str] = None
    target_name: Optional[str] = "Missing Person"
    thermal: Optional[bool] = True
    assigned_team_id: Optional[str] = None

class TeamLocationUpdate(BaseModel):
    lat: float
    lon: float

class HazardZonePayload(BaseModel):
    lat: float
    lon: float
    radius_m: float = 60.0
    name: str = "Cliff / Landslide Hazard"

# ==========================================
# Core Helper Functions
# ==========================================
def find_optimal_team_for_target(target_lat: float, target_lon: float) -> str:
    """Finds the closest available team to the target based on Euclidean distance."""
    available_teams = [t for t in state.teams.values() if t["status"] in ["IDLE", "EN_ROUTE"]]
    if not available_teams:
        available_teams = list(state.teams.values())
    
    best_team = min(
        available_teams,
        key=lambda t: haversine_distance(t["lat"], t["lon"], target_lat, target_lon)
    )
    return best_team["id"]

# ==========================================
# REST API Endpoints
# ==========================================
@app.get("/api/state")
async def get_full_state():
    """Returns the complete live mission state."""
    return {
        "teams": list(state.teams.values()),
        "targets": state.targets,
        "routes": list(state.routes.values()),
        "hazards": state.hazards,
        "drone": state.drone_telemetry
    }

@app.post("/api/detection")
async def receive_detection(payload: DetectionPayload):
    """
    Ingests target detection from drone, selects the best SAR team,
    and computes terrain-aware optimal route asynchronously.
    """
    target_id = payload.target_id or f"target-{int(time.time() * 1000) % 100000}"
    target_data = {
        "id": target_id,
        "name": payload.target_name,
        "lat": payload.lat,
        "lon": payload.lon,
        "confidence": round(payload.confidence, 2),
        "thermal": payload.thermal,
        "timestamp": payload.timestamp or time.time(),
        "status": "DISPATCHED"
    }

    # Select team
    assigned_team_id = payload.assigned_team_id or find_optimal_team_for_target(payload.lat, payload.lon)
    assigned_team = state.teams.get(assigned_team_id)
    target_data["assigned_team_id"] = assigned_team_id

    # Compute terrain route in background thread pool (non-blocking)
    try:
        route_data = await asyncio.to_thread(
            compute_route,
            start_lat=assigned_team["lat"],
            start_lon=assigned_team["lon"],
            end_lat=payload.lat,
            end_lon=payload.lon,
            slope_penalty_factor=SLOPE_PENALTY_FACTOR,
            obstacle_penalty_multiplier=OBSTACLE_PENALTY_MULTIPLIER,
            slope_threshold=SLOPE_THRESHOLD,
            base_speed_kmh=assigned_team.get("speed_kmh", BASE_SPEED_KMH),
            hazard_zones=state.hazards
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Route calculation failed: {str(e)}")

    route_id = f"route-{target_id}"
    full_route_object = {
        "id": route_id,
        "target_id": target_id,
        "team_id": assigned_team_id,
        "team_name": assigned_team["name"],
        **route_data
    }

    # Update state
    state.targets.append(target_data)
    state.routes[route_id] = full_route_object
    state.teams[assigned_team_id]["status"] = "EN_ROUTE"
    state.teams[assigned_team_id]["active_route_id"] = route_id

    # Broadcast via WebSocket
    await manager.broadcast("DETECTION_RECEIVED", {
        "target": target_data,
        "team": state.teams[assigned_team_id],
        "route": full_route_object
    })

    return {
        "status": "success",
        "target": target_data,
        "route": full_route_object
    }

@app.get("/api/current-route")
async def get_current_route():
    """Returns the most recently computed route for backwards compatibility."""
    if not state.routes:
        return {"message": "No route available"}
    latest_route = list(state.routes.values())[-1]
    return latest_route

@app.get("/api/teams")
async def get_teams():
    return list(state.teams.values())

@app.post("/api/teams/{team_id}/location")
async def update_team_location(team_id: str, loc: TeamLocationUpdate):
    if team_id not in state.teams:
        raise HTTPException(status_code=404, detail="Team not found")
    
    state.teams[team_id]["lat"] = loc.lat
    state.teams[team_id]["lon"] = loc.lon

    # If team has active route, recompute route from new position asynchronously
    active_route_id = state.teams[team_id].get("active_route_id")
    if active_route_id and active_route_id in state.routes:
        target_id = state.routes[active_route_id]["target_id"]
        target = next((t for t in state.targets if t["id"] == target_id), None)
        if target:
            new_route_data = await asyncio.to_thread(
                compute_route,
                start_lat=loc.lat,
                start_lon=loc.lon,
                end_lat=target["lat"],
                end_lon=target["lon"],
                hazard_zones=state.hazards
            )
            state.routes[active_route_id].update(new_route_data)

    await manager.broadcast("TEAM_LOCATION_UPDATED", {
        "team": state.teams[team_id],
        "active_route": state.routes.get(active_route_id)
    })

    return {"status": "success", "team": state.teams[team_id]}

@app.get("/api/targets")
async def get_targets():
    return state.targets

@app.get("/api/routes")
async def get_routes():
    return list(state.routes.values())

@app.post("/api/simulate-detection")
async def simulate_detection(scenario: Optional[str] = "twin-peaks-ravine"):
    """Simulates a drone detection event using predefined realistic scenarios."""
    scen = SIMULATION_SCENARIOS.get(scenario, SIMULATION_SCENARIOS["twin-peaks-ravine"])
    payload = DetectionPayload(
        lat=scen["lat"],
        lon=scen["lon"],
        confidence=scen["confidence"],
        target_name=scen["name"],
        thermal=scen["thermal"],
        timestamp=time.time()
    )
    return await receive_detection(payload)

@app.post("/api/hazards")
async def add_hazard_zone(hazard: HazardZonePayload):
    hazard_obj = {
        "id": f"hazard-{int(time.time() * 1000) % 10000}",
        "lat": hazard.lat,
        "lon": hazard.lon,
        "radius_m": hazard.radius_m,
        "name": hazard.name
    }
    state.hazards.append(hazard_obj)
    await manager.broadcast("HAZARD_UPDATED", {"hazards": state.hazards})
    return {"status": "success", "hazard": hazard_obj}

@app.delete("/api/hazards")
async def clear_hazards():
    state.hazards.clear()
    await manager.broadcast("HAZARD_UPDATED", {"hazards": []})
    return {"status": "success", "message": "All hazard zones cleared"}

@app.post("/api/drone/telemetry")
async def update_drone_telemetry(telemetry: Dict[str, Any]):
    state.drone_telemetry.update(telemetry)
    await manager.broadcast("DRONE_TELEMETRY", state.drone_telemetry)
    return {"status": "success", "drone": state.drone_telemetry}

@app.post("/api/reset")
async def reset_system():
    state.reset()
    await manager.broadcast("INIT_STATE", {
        "teams": list(state.teams.values()),
        "targets": state.targets,
        "routes": list(state.routes.values()),
        "hazards": state.hazards,
        "drone": state.drone_telemetry
    })
    return {"status": "success", "message": "System reset to initial state"}

# ==========================================
# WebSocket Endpoint
# ==========================================
@app.websocket("/ws/dispatch")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            # Keep connection alive and accept incoming pings
            data = await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)
