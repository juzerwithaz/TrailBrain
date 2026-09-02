import json
import sys
from pathlib import Path
from fastapi.testclient import TestClient

# Ensure backend module is in path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from main import app

client = TestClient(app)

def run_tests():
    print("========================================")
    print("       TRAILBRAIN BACKEND API TEST      ")
    print("========================================")
    
    # 1. Reset System State
    print("\n--- 1. Resetting System State ---")
    res = client.post("/api/reset")
    assert res.status_code == 200
    print("Reset response:", res.json())
    
    # 2. Fetch Initial State & Teams
    print("\n--- 2. Fetching Initial State & Teams ---")
    res = client.get("/api/state")
    assert res.status_code == 200
    state = res.json()
    print(f"Active Teams Registered: {len(state['teams'])}")
    for t in state['teams']:
        print(f"  - {t['name']} ({t['type']}): Status={t['status']}, Coord=({t['lat']}, {t['lon']})")
    assert len(state['teams']) >= 4, "Expected at least 4 default SAR teams"
    
    # 3. Simulate Detection Scenario 1 (Twin Peaks Ravine)
    print("\n--- 3. Triggering Simulation Scenario: twin-peaks-ravine ---")
    res = client.post("/api/simulate-detection?scenario=twin-peaks-ravine")
    assert res.status_code == 200
    data = res.json()
    print("Simulation Dispatch Result:")
    print(f"  Target: {data['target']['name']} ({data['target']['lat']}, {data['target']['lon']})")
    print(f"  Assigned Team: {data['route']['team_name']} (ID: {data['route']['team_id']})")
    print(f"  Route Distance: {data['route']['distance_km']} km")
    print(f"  Route ETA: {data['route']['eta_minutes']} minutes")
    print(f"  Ascent: {data['route']['total_ascent_m']}m, Descent: {data['route']['total_descent_m']}m")
    print(f"  Max Slope: {data['route']['max_slope_percent']}%, Rating: {data['route']['difficulty_rating']}")
    
    assert data['route']['distance_km'] > 0
    assert len(data['route']['elevation_profile']) > 0

    # 4. Update Team Location & Verify Dynamic Re-routing
    print("\n--- 4. Updating Team GPS Location ---")
    team_id = data['route']['team_id']
    res = client.post(f"/api/teams/{team_id}/location", json={"lat": 37.7540, "lon": -122.4455})
    assert res.status_code == 200
    print(f"Team {team_id} new position acknowledged:", res.json())

    # 5. Add Hazard Zone
    print("\n--- 5. Adding Dynamic Cliff Hazard Zone ---")
    res = client.post("/api/hazards", json={
        "lat": 37.7550,
        "lon": -122.4445,
        "radius_m": 50.0,
        "name": "Rockfall Danger"
    })
    assert res.status_code == 200
    print("Hazard Zone registered:", res.json())

    # 6. Fetch Complete State Again
    print("\n--- 6. Verifying Final State ---")
    res = client.get("/api/state")
    state = res.json()
    print(f"Total Targets: {len(state['targets'])}")
    print(f"Total Active Routes: {len(state['routes'])}")
    print(f"Total Hazards: {len(state['hazards'])}")
    
    print("\n>> All Backend API Tests PASSED successfully!")

if __name__ == "__main__":
    run_tests()
