import math
import os
from pathlib import Path
import rasterio
from rasterio.transform import from_origin
import networkx as nx
import numpy as np

def haversine_distance(lat1, lon1, lat2, lon2):
    """Calculate the great circle distance in meters between two points on the earth."""
    R = 6371000.0  # Earth radius in meters
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = math.sin(delta_phi / 2.0) ** 2 + \
        math.cos(phi1) * math.cos(phi2) * \
        math.sin(delta_lambda / 2.0) ** 2
    
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return R * c

def tobler_hiking_speed_kmh(slope: float) -> float:
    """
    Computes human hiking speed using Tobler's Hiking Function:
    V = 6 * exp(-3.5 * |slope + 0.05|) in km/h
    where slope = tan(theta) = elevation_diff / horizontal_dist (signed).
    
    - Maximum speed (~6.0 km/h) occurs on gentle downhill (-0.05 slope).
    - Flat ground (0.0 slope) is ~5.03 km/h.
    - Uphill and steep slopes progressively slow down to crawl speeds.
    """
    speed = 6.0 * math.exp(-3.5 * abs(slope + 0.05))
    return max(0.1, speed)  # Minimum 0.1 km/h to prevent divide-by-zero

def ensure_dem_exists(filepath: Path):
    """Generates a default synthetic Gaussian hill DEM if no DEM tile exists."""
    if filepath.exists():
        return
    
    filepath.parent.mkdir(parents=True, exist_ok=True)
    
    # 100x100 grid centered around SF Twin Peaks area
    x = np.linspace(-5, 5, 100)
    y = np.linspace(-5, 5, 100)
    X, Y = np.meshgrid(x, y)
    
    # Central peak with 300m elevation prominence
    Z = 300.0 * np.exp(-(X**2 + Y**2) / 2.0) + 100.0
    
    lon_start = -122.45
    lat_start = 37.75
    pixel_size = 0.0001  # ~10 meters per pixel
    
    transform = from_origin(lon_start, lat_start + (100 * pixel_size), pixel_size, pixel_size)
    
    with rasterio.open(
        filepath,
        'w',
        driver='GTiff',
        height=Z.shape[0],
        width=Z.shape[1],
        count=1,
        dtype=np.float32,
        crs='+proj=latlong',
        transform=transform,
    ) as dst:
        dst.write(Z.astype(np.float32), 1)

def compute_route(
    start_lat: float, 
    start_lon: float, 
    end_lat: float, 
    end_lon: float, 
    slope_penalty_factor: float = 0.0, 
    obstacle_penalty_multiplier: float = 50.0, 
    slope_threshold: float = 0.45, 
    base_speed_kmh: float = 5.0,
    hazard_zones: list = None,
    dem_path: str = None
):
    """
    Computes a terrain-aware, physiological shortest/safest path using A* over DEM rasters.
    Uses Tobler's Hiking Function for physics-accurate speed and energy budgeting.
    
    Returns:
    {
        "route": [[lat, lon], ...],
        "elevation_profile": [{"lat": float, "lon": float, "elevation_m": float, "distance_m": float}, ...],
        "distance_km": float,
        "total_ascent_m": float,
        "total_descent_m": float,
        "max_slope_percent": float,
        "eta_minutes": float,
        "difficulty_rating": str
    }
    """
    if dem_path is None:
        default_dem = Path(__file__).resolve().parent.parent / "data" / "dem_tile.tif"
        ensure_dem_exists(default_dem)
        dem_path = str(default_dem)
    else:
        ensure_dem_exists(Path(dem_path))

    hazard_zones = hazard_zones or []

    with rasterio.open(dem_path) as src:
        dem_data = src.read(1)
        transform = src.transform
        rows, cols = dem_data.shape

        def rc_to_latlon(r, c):
            lon, lat = rasterio.transform.xy(transform, r, c, offset='center')
            return lat, lon

        # Convert start/end GPS to raster row/col
        try:
            start_row, start_col = rasterio.transform.rowcol(transform, start_lon, start_lat)
            end_row, end_col = rasterio.transform.rowcol(transform, end_lon, end_lat)
        except Exception as e:
            raise ValueError(f"Start or end point is outside the DEM bounds: {e}")

        # Clamp inside boundaries
        start_row = max(0, min(rows - 1, start_row))
        start_col = max(0, min(cols - 1, start_col))
        end_row = max(0, min(rows - 1, end_row))
        end_col = max(0, min(cols - 1, end_col))

        # Dynamic bounding box with padding
        padding = max(20, int(max(abs(start_row - end_row), abs(start_col - end_col)) * 0.4))
        min_r = max(0, min(start_row, end_row) - padding)
        max_r = min(rows - 1, max(start_row, end_row) + padding)
        min_c = max(0, min(start_col, end_col) - padding)
        max_c = min(cols - 1, max(start_col, end_col) + padding)

        G = nx.DiGraph()
        latlons = {}
        
        for r in range(min_r, max_r + 1):
            for c in range(min_c, max_c + 1):
                latlons[(r, c)] = rc_to_latlon(r, c)
                G.add_node((r, c))

        directions = [
            (-1, 0), (1, 0), (0, -1), (0, 1),
            (-1, -1), (-1, 1), (1, -1), (1, 1)
        ]

        nodata = src.nodata

        # Helper: check if a point is in any hazard zone
        def is_in_hazard(lat, lon):
            for hz in hazard_zones:
                hz_lat = hz.get("lat")
                hz_lon = hz.get("lon")
                hz_radius = hz.get("radius_m", 50.0)
                if hz_lat is not None and hz_lon is not None:
                    if haversine_distance(lat, lon, hz_lat, hz_lon) <= hz_radius:
                        return True
            return False

        for r in range(min_r, max_r + 1):
            for c in range(min_c, max_c + 1):
                if nodata is not None and dem_data[r, c] == nodata:
                    continue

                lat1, lon1 = latlons[(r, c)]
                z1 = float(dem_data[r, c])

                for dr, dc in directions:
                    nr, nc = r + dr, c + dc
                    if min_r <= nr <= max_r and min_c <= nc <= max_c:
                        if nodata is not None and dem_data[nr, nc] == nodata:
                            continue

                        lat2, lon2 = latlons[(nr, nc)]
                        z2 = float(dem_data[nr, nc])

                        base_dist = haversine_distance(lat1, lon1, lat2, lon2)
                        if base_dist <= 0:
                            continue

                        elev_diff = z2 - z1
                        signed_slope = elev_diff / base_dist
                        abs_slope = abs(signed_slope)

                        # Tobler speed in km/h -> m/s
                        tobler_speed_kmh = tobler_hiking_speed_kmh(signed_slope)
                        speed_ms = (tobler_speed_kmh * 1000.0) / 3600.0
                        
                        # Base traversal time in seconds
                        traversal_time_sec = base_dist / speed_ms

                        # Apply additional obstacle penalties for extreme slopes (cliffs)
                        penalty_multiplier = 1.0
                        if abs_slope > slope_threshold:
                            penalty_multiplier *= obstacle_penalty_multiplier
                        
                        # Extra penalty if inside dynamic hazard zone
                        if is_in_hazard(lat2, lon2):
                            penalty_multiplier *= 500.0

                        # Edge weight is traversal time in seconds * penalties
                        edge_weight = traversal_time_sec * penalty_multiplier

                        G.add_edge(
                            (r, c), (nr, nc), 
                            weight=edge_weight, 
                            base_dist=base_dist, 
                            time_sec=traversal_time_sec,
                            elev_diff=elev_diff,
                            slope=signed_slope
                        )

        # Admissible A* heuristic: minimal travel time assuming optimal gentle downhill speed (6.0 km/h = 1.667 m/s)
        max_speed_ms = (6.0 * 1000.0) / 3600.0
        def heuristic(n1, n2):
            lat1, lon1 = latlons[n1]
            lat2, lon2 = latlons[n2]
            dist = haversine_distance(lat1, lon1, lat2, lon2)
            return dist / max_speed_ms

        start_node = (start_row, start_col)
        end_node = (end_row, end_col)

        try:
            path = nx.astar_path(G, start_node, end_node, heuristic=heuristic, weight='weight')
        except (nx.NetworkXNoPath, nx.NodeNotFound):
            raise ValueError(f"No viable terrain path found between ({start_lat}, {start_lon}) and ({end_lat}, {end_lon}). Terrain may be impassable.")

        # Reconstruct path and metrics
        total_dist_m = 0.0
        total_time_sec = 0.0
        total_ascent_m = 0.0
        total_descent_m = 0.0
        max_slope_percent = 0.0

        route_coords = []
        elevation_profile = []

        first_node = path[0]
        first_lat, first_lon = latlons[first_node]
        first_elev = float(dem_data[first_node[0], first_node[1]])

        route_coords.append([first_lat, first_lon])
        elevation_profile.append({
            "lat": round(first_lat, 6),
            "lon": round(first_lon, 6),
            "elevation_m": round(first_elev, 1),
            "distance_m": 0.0
        })

        for i in range(len(path) - 1):
            u = path[i]
            v = path[i + 1]
            edge = G[u][v]

            total_dist_m += edge['base_dist']
            total_time_sec += edge['time_sec']
            
            diff = edge['elev_diff']
            if diff > 0:
                total_ascent_m += diff
            else:
                total_descent_m += abs(diff)

            slope_pct = abs(edge['slope']) * 100.0
            if slope_pct > max_slope_percent:
                max_slope_percent = slope_pct

            v_lat, v_lon = latlons[v]
            v_elev = float(dem_data[v[0], v[1]])

            route_coords.append([v_lat, v_lon])
            elevation_profile.append({
                "lat": round(v_lat, 6),
                "lon": round(v_lon, 6),
                "elevation_m": round(v_elev, 1),
                "distance_m": round(total_dist_m, 1)
            })

        distance_km = total_dist_m / 1000.0
        eta_minutes = total_time_sec / 60.0

        # Determine difficulty rating
        if max_slope_percent >= 45.0 or total_ascent_m >= 600:
            difficulty = "TECHNICAL_TERRAIN"
        elif max_slope_percent >= 25.0 or total_ascent_m >= 250:
            difficulty = "STRENUOUS"
        elif max_slope_percent >= 12.0 or total_ascent_m >= 80:
            difficulty = "MODERATE"
        else:
            difficulty = "EASY"

        return {
            "route": route_coords,
            "elevation_profile": elevation_profile,
            "distance_km": round(distance_km, 3),
            "total_ascent_m": round(total_ascent_m, 1),
            "total_descent_m": round(total_descent_m, 1),
            "max_slope_percent": round(max_slope_percent, 1),
            "eta_minutes": round(eta_minutes, 1),
            "difficulty_rating": difficulty
        }
