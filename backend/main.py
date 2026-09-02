import sys
import os
import time
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Add the routing directory to the python path to import the engine directly
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'routing')))
from engine import compute_route

from config import (
    START_LAT, 
    START_LON, 
    SLOPE_PENALTY_FACTOR, 
    OBSTACLE_PENALTY_MULTIPLIER, 
    SLOPE_THRESHOLD, 
    BASE_SPEED_KMH,
    SIMULATE_TARGET_LAT,
    SIMULATE_TARGET_LON
)

app = FastAPI(title="TrailBrain Backend")

# Enable CORS for hackathon
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory store for the latest route
current_route = None

class DetectionPayload(BaseModel):
    lat: float
    lon: float
    confidence: float
    timestamp: float


@app.post("/api/detection")
def receive_detection(payload: DetectionPayload):
    global current_route
    
    try:
        route_data = compute_route(
            start_lat=START_LAT,
            start_lon=START_LON,
            end_lat=payload.lat,
            end_lon=payload.lon,
            slope_penalty_factor=SLOPE_PENALTY_FACTOR,
            obstacle_penalty_multiplier=OBSTACLE_PENALTY_MULTIPLIER,
            slope_threshold=SLOPE_THRESHOLD,
            base_speed_kmh=BASE_SPEED_KMH
        )
        current_route = route_data
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/current-route")
def get_current_route():
    if current_route is None:
        return {"message": "No route available"}
    return current_route


@app.post("/api/simulate-detection")
def simulate_detection():
    # Simulate a detection event using our target coordinates
    payload = DetectionPayload(
        lat=SIMULATE_TARGET_LAT,
        lon=SIMULATE_TARGET_LON,
        confidence=0.95,
        timestamp=time.time()
    )
    return receive_detection(payload)
