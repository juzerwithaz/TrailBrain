import os
import sys
from pathlib import Path
import numpy as np
import rasterio
from rasterio.transform import from_origin
import json

# Ensure routing module is importable
sys.path.insert(0, str(Path(__file__).resolve().parent))
from engine import compute_route, tobler_hiking_speed_kmh

def run_test():
    print("========================================")
    print("       TRAILBRAIN ROUTING ENGINE TEST    ")
    print("========================================")
    
    # 1. Test Tobler's Hiking Speed Formula
    print("\n--- 1. Testing Tobler Hiking Physics ---")
    flat_speed = tobler_hiking_speed_kmh(0.0)
    downhill_speed = tobler_hiking_speed_kmh(-0.05)
    uphill_gentle = tobler_hiking_speed_kmh(0.15)
    uphill_steep = tobler_hiking_speed_kmh(0.40)
    
    print(f"Flat Ground (0% grade):      {flat_speed:.2f} km/h (Expected ~5.03 km/h)")
    print(f"Gentle Downhill (-5% grade): {downhill_speed:.2f} km/h (Expected ~6.00 km/h - Peak)")
    print(f"Gentle Uphill (+15% grade):  {uphill_gentle:.2f} km/h (Expected ~2.98 km/h)")
    print(f"Steep Uphill (+40% grade):   {uphill_steep:.2f} km/h (Expected ~1.25 km/h)")
    
    assert downhill_speed > flat_speed > uphill_gentle > uphill_steep, "Tobler curve monotonicity failure!"
    print(">> Tobler Hiking Curve: PASS")

    # 2. Test Terrain-Aware Pathfinding over Central Hill
    print("\n--- 2. Testing 3D Terrain A* Pathfinding ---")
    start_lat = 37.7535
    start_lon = -122.4465
    end_lat = 37.7565
    end_lon = -122.4435
    
    # Run A: Low obstacle penalty (goes straight across hill)
    result_straight = compute_route(
        start_lat=start_lat,
        start_lon=start_lon,
        end_lat=end_lat,
        end_lon=end_lon,
        obstacle_penalty_multiplier=1.0,
        slope_threshold=0.6
    )
    
    # Run B: High obstacle penalty (skirts around the hill)
    result_skirt = compute_route(
        start_lat=start_lat,
        start_lon=start_lon,
        end_lat=end_lat,
        end_lon=end_lon,
        obstacle_penalty_multiplier=50.0,
        slope_threshold=0.3
    )
    
    print(f"Straight-through route length: {len(result_straight['route'])} nodes, Dist: {result_straight['distance_km']} km, ETA: {result_straight['eta_minutes']} min, Max Slope: {result_straight['max_slope_percent']}%, Rating: {result_straight['difficulty_rating']}")
    print(f"Terrain-avoiding route length: {len(result_skirt['route'])} nodes, Dist: {result_skirt['distance_km']} km, ETA: {result_skirt['eta_minutes']} min, Max Slope: {result_skirt['max_slope_percent']}%, Rating: {result_skirt['difficulty_rating']}")
    
    print(f"Ascent straight: {result_straight['total_ascent_m']}m vs Ascent skirt: {result_skirt['total_ascent_m']}m")
    print(f"Elevation Profile samples: {len(result_skirt['elevation_profile'])} points")
    print(f"First waypoint profile: {result_skirt['elevation_profile'][0]}")
    print(f"Last waypoint profile:  {result_skirt['elevation_profile'][-1]}")
    
    assert len(result_skirt['route']) > 0, "No route generated!"
    assert len(result_skirt['elevation_profile']) == len(result_skirt['route']), "Elevation profile mismatch!"
    
    print("\n>> All Routing Engine Tests PASSED successfully!")

if __name__ == "__main__":
    run_test()
