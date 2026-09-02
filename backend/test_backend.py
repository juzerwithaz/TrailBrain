import json
from fastapi.testclient import TestClient

from main import app

client = TestClient(app)

def run_tests():
    print("Testing Backend API Loop...")
    
    # 1. Check current route (should be empty)
    print("\n--- 1. Fetching initial route ---")
    response = client.get("/api/current-route")
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    
    # 2. Trigger simulate-detection
    print("\n--- 2. Triggering simulate-detection ---")
    response = client.post("/api/simulate-detection")
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    
    # 3. Check current route again (should have the route JSON)
    print("\n--- 3. Fetching updated route ---")
    response = client.get("/api/current-route")
    print(f"Status: {response.status_code}")
    
    data = response.json()
    if "route" in data:
        print(f"Success! Route contains {len(data['route'])} nodes.")
        print(f"Distance: {data['distance_km']} km")
        print(f"ETA: {data['eta_minutes']} minutes")
        print("First 3 coordinates:", data['route'][:3])
    else:
        print("Failed to get route data. Response:", data)

if __name__ == "__main__":
    run_tests()
