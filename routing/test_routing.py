import os
import sys
import numpy as np
import rasterio
from rasterio.transform import from_origin
import json

def generate_dummy_dem(filepath):
    """Generates a dummy 100x100 DEM file for testing."""
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    
    # 100x100 grid
    x = np.linspace(-5, 5, 100)
    y = np.linspace(-5, 5, 100)
    X, Y = np.meshgrid(x, y)
    
    # A moderate hill in the center
    Z = 300 * np.exp(-(X**2 + Y**2) / 2.0)
    
    # Base elevation of 100m
    Z += 100.0
    
    # Coordinates for SF area roughly
    lon_start = -122.45
    lat_start = 37.75
    # Pixel size roughly 10 meters (in degrees approx 0.0001)
    pixel_size = 0.0001
    
    transform = from_origin(lon_start, lat_start + (100 * pixel_size), pixel_size, pixel_size)
    
    with rasterio.open(
        filepath,
        'w',
        driver='GTiff',
        height=Z.shape[0],
        width=Z.shape[1],
        count=1,
        dtype=Z.dtype,
        crs='+proj=latlong',
        transform=transform,
    ) as dst:
        dst.write(Z, 1)


def run_test():
    dem_path = '../data/dem_tile.tif'
    # Always generate to pick up any changes to the hill shape
    print("Generating steep dummy DEM...")
    generate_dummy_dem(dem_path)
    
    # Must add current dir to path to import engine
    sys.path.append(os.path.dirname(__file__))
    from engine import compute_route
    
    # Start and end coordinates closer to the central hill 
    # to force traversal of slopes rather than skirting flat map boundaries
    start_lat = 37.7535
    start_lon = -122.4465
    end_lat = 37.7565
    end_lon = -122.4435
    
    print(f"Testing route computation...")
    print(f"Start: ({start_lat}, {start_lon})")
    print(f"End: ({end_lat}, {end_lon})\n")
    
    # Run 1: No obstacle penalty (multiplier = 1)
    # Using slope_penalty_factor = 0.0 means this will just find the shortest 2D path (a straight line)
    print("--- Run 1: obstacle_penalty_multiplier = 1 ---")
    result_1 = compute_route(
        start_lat=start_lat,
        start_lon=start_lon,
        end_lat=end_lat,
        end_lon=end_lon,
        slope_penalty_factor=0.0,
        obstacle_penalty_multiplier=1.0,
        slope_threshold=0.5,
        base_speed_kmh=15.0
    )
    
    nodes_1 = len(result_1['route'])
    print(f"Route length: {nodes_1} nodes")
    print(f"Distance: {result_1['distance_km']} km")
    print(f"ETA: {result_1['eta_minutes']} minutes")
    print("Route Coordinates:")
    for c in result_1['route']:
        print(f"  [{c[0]:.4f}, {c[1]:.4f}]")
    print("\n")

    # Run 2: High obstacle penalty (multiplier = 50)
    # This will curve around the hill to avoid slopes > 0.5
    print("--- Run 2: obstacle_penalty_multiplier = 50 ---")
    result_500 = compute_route(
        start_lat=start_lat,
        start_lon=start_lon,
        end_lat=end_lat,
        end_lon=end_lon,
        slope_penalty_factor=0.0,
        obstacle_penalty_multiplier=50.0,
        slope_threshold=0.5,
        base_speed_kmh=15.0
    )
    
    nodes_500 = len(result_500['route'])
    print(f"Route length: {nodes_500} nodes")
    print(f"Distance: {result_500['distance_km']} km")
    print(f"ETA: {result_500['eta_minutes']} minutes")
    print("Route Coordinates:")
    for c in result_500['route']:
        print(f"  [{c[0]:.4f}, {c[1]:.4f}]")
    print("\n")
    
    # Compare
    routes_are_identical = result_1['route'] == result_500['route']
    print(f"Are the two routes identical? {'YES' if routes_are_identical else 'NO'}")

if __name__ == "__main__":
    run_test()
