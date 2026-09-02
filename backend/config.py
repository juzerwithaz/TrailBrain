# Global Configuration for TrailBrain Dispatch System

# Default Ground Rescue Teams
DEFAULT_TEAMS = [
    {
        "id": "team-alpha",
        "name": "SAR Team Alpha",
        "type": "FOOT_PATROL",
        "status": "IDLE",  # IDLE, EN_ROUTE, ON_SCENE
        "lat": 37.7535,
        "lon": -122.4465,
        "speed_kmh": 5.0,
        "personnel_count": 4,
        "equipment": ["First Aid Level 3", "Stokes Litter", "Thermal Monocular"]
    },
    {
        "id": "team-bravo",
        "name": "SAR Team Bravo",
        "type": "ALPINE_RESCUE",
        "status": "IDLE",
        "lat": 37.7580,
        "lon": -122.4520,
        "speed_kmh": 4.5,
        "personnel_count": 3,
        "equipment": ["Technical Ropes", "Harnesses", "GPS Beacon Receiver"]
    },
    {
        "id": "team-k9",
        "name": "K9 Unit Rex",
        "type": "CANINE_SEARCH",
        "status": "IDLE",
        "lat": 37.7480,
        "lon": -122.4400,
        "speed_kmh": 5.5,
        "personnel_count": 2,
        "equipment": ["Tracking Dog", "Radio Collar", "Trauma Kit"]
    },
    {
        "id": "team-atv",
        "name": "ATV Rapid Response",
        "type": "VEHICLE",
        "status": "IDLE",
        "lat": 37.7510,
        "lon": -122.4480,
        "speed_kmh": 15.0,
        "personnel_count": 2,
        "equipment": ["4x4 Polaris ATV", "Winch", "Emergency Oxygen"]
    }
]

# Routing parameters
SLOPE_PENALTY_FACTOR = 0.0
OBSTACLE_PENALTY_MULTIPLIER = 50.0
SLOPE_THRESHOLD = 0.35
BASE_SPEED_KMH = 5.0

# Pre-configured Simulation Scenarios
SIMULATION_SCENARIOS = {
    "twin-peaks-ravine": {
        "name": "Twin Peaks Ravine (Missing Hiker)",
        "lat": 37.7565,
        "lon": -122.4435,
        "confidence": 0.96,
        "thermal": True,
        "description": "Thermal signature detected in steep drainage gully."
    },
    "sutro-ridge": {
        "name": "Mount Sutro Ridge (Lost Child)",
        "lat": 37.7595,
        "lon": -122.4490,
        "confidence": 0.92,
        "thermal": True,
        "description": "Movement detected near northwest tree line."
    },
    "glen-canyon-cliff": {
        "name": "Glen Canyon (Injured Climber)",
        "lat": 37.7495,
        "lon": -122.4380,
        "confidence": 0.98,
        "thermal": False,
        "description": "Visual confirmation of fallen hiker at cliff base."
    }
}
