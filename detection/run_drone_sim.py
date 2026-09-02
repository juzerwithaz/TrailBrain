import sys
import time
import argparse
from pathlib import Path
import httpx

# Ensure detection module is importable
sys.path.insert(0, str(Path(__file__).resolve().parent))
from georeferencing import calculate_ground_coordinate
from detector import SARDetector

def run_simulation(backend_url: str = "http://localhost:8000", dry_run: bool = False):
    print("==================================================")
    print("   TRAILBRAIN DRONE SEARCH & CV SIMULATOR         ")
    print("==================================================")
    
    detector = SARDetector(confidence_threshold=0.85)
    
    # Simulated search flight path over Twin Peaks
    waypoints = [
        {"lat": 37.7540, "lon": -122.4470, "alt_m": 90.0, "heading": 45, "pitch": -45.0, "target": False},
        {"lat": 37.7550, "lon": -122.4455, "alt_m": 85.0, "heading": 55, "pitch": -50.0, "target": False},
        {"lat": 37.7558, "lon": -122.4442, "alt_m": 80.0, "heading": 60, "pitch": -48.0, "target": True, "u": 0.08, "v": -0.05}
    ]
    
    print(f"\n[1] Starting Aerial Search Mission across {len(waypoints)} waypoints...")
    
    for i, wp in enumerate(waypoints):
        print(f"\n>> Waypoint {i+1}/{len(waypoints)}: Drone at ({wp['lat']}, {wp['lon']}), Alt: {wp['alt_m']}m, Heading: {wp['heading']}°")
        
        # Check CV detector
        detections = detector.process_frame({"target_in_view": wp.get("target", False), "u_norm": wp.get("u", 0.0), "v_norm": wp.get("v", 0.0)})
        
        if detections:
            det = detections[0]
            print(f"   🚨 TARGET DETECTED! Class: {det['class_name'].upper()} | Confidence: {det['confidence']*100:.1f}% | Thermal: {det['thermal_signature']['apparent_temp_c']}°C")
            
            # Compute ground coordinate using georeferencing
            target_lat, target_lon, ground_dist = calculate_ground_coordinate(
                drone_lat=wp['lat'],
                drone_lon=wp['lon'],
                drone_alt_agl_m=wp['alt_m'],
                gimbal_pitch_deg=wp['pitch'],
                drone_heading_deg=wp['heading'],
                u_norm=wp.get("u", 0.0),
                v_norm=wp.get("v", 0.0)
            )
            
            print(f"   📍 Georeferenced Ground Target: ({target_lat}, {target_lon}) [~{ground_dist}m ahead]")
            
            payload = {
                "lat": target_lat,
                "lon": target_lon,
                "confidence": det['confidence'],
                "target_name": "Thermal Target (Aerial CV)",
                "thermal": True,
                "timestamp": time.time()
            }
            
            if dry_run:
                print("   [DRY-RUN] Detection payload prepared:", payload)
            else:
                try:
                    res = httpx.post(f"{backend_url}/api/detection", json=payload, timeout=10.0)
                    if res.status_code == 200:
                        data = res.json()
                        print("   ✅ Dispatched to Backend successfully!")
                        print(f"      Assigned: {data['route']['team_name']} | Distance: {data['route']['distance_km']} km | ETA: {data['route']['eta_minutes']} min")
                    else:
                        print(f"   ⚠️ Backend returned status {res.status_code}: {res.text}")
                except Exception as e:
                    print(f"   ⚠️ Could not reach backend: {e} (Run backend first to test live dispatch)")
        else:
            print("   🔍 Scanning... No targets detected in frame.")
        
        time.sleep(0.5)
        
    print("\n>> Drone Simulation Complete!")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="TrailBrain Drone Flight & Detection Simulator")
    parser.add_argument("--backend-url", default="http://localhost:8000", help="Backend API URL")
    parser.add_argument("--dry-run", action="store_true", help="Execute without sending network requests")
    args = parser.parse_args()
    
    run_simulation(backend_url=args.backend_url, dry_run=args.dry_run)
