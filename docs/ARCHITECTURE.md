# TrailBrain Architecture

TrailBrain is an AI-assisted search-and-rescue dispatcher composed of four distinct modules. This document outlines the contract and communication flow between these modules.

## Modules

1. **Detection (`/detection`)**: Computer Vision pipeline in Python.
2. **Routing (`/routing`)**: Terrain-aware pathfinding engine in Python.
3. **Backend (`/backend`)**: Integration/event layer connecting detection to routing. Written in Python with FastAPI.
4. **Frontend (`/frontend`)**: Dispatch UI built with React.

## System Contract & Data Flow

### 1. Detection Output
The Detection module processes data (e.g., aerial footage) and outputs a JSON object when a target is detected.
```json
{
  "lat": 37.7749,
  "lon": -122.4194,
  "confidence": 0.95,
  "timestamp": 1693630800.0
}
```

### 2. Backend Ingestion
The JSON output from the Detection module is `POST`ed to the Backend.
- **Endpoint**: `POST /api/detection`
- **Payload**: Detection JSON object.

### 3. Routing Trigger
Upon receiving a detection, the Backend triggers the Routing module.
- **Start Point**: The ground team's start position is defined as a single constant in backend/config.py (START_LAT, START_LON) and passed into every routing call — routing itself holds no hardcoded coordinates.
- **Target Point**: The `lat`/`lon` from the detection payload.

### 4. Routing Response
The Routing module computes the optimal path and returns the following structure to the Backend:
```json
{
  "route": [
    [37.7749, -122.4194],
    [37.7750, -122.4190]
  ],
  "distance_km": 1.2,
  "eta_minutes": 15.5
}
```

### 5. Frontend Polling / Push
The Backend pushes this route to the Frontend, which the Frontend retrieves via a simple polling endpoint (or WebSocket).
- **Endpoint**: `GET /api/current-route`
- **Response**: The routing response JSON object.
