import math
import rasterio
import networkx as nx
import numpy as np
from pyproj import Geod

def haversine_distance(lat1, lon1, lat2, lon2):
    """Calculate the great circle distance in meters between two points on the earth."""
    R = 6371000  # Radius of earth in meters
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = math.sin(delta_phi / 2.0) ** 2 + \
        math.cos(phi1) * math.cos(phi2) * \
        math.sin(delta_lambda / 2.0) ** 2
    
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

def compute_route(start_lat, start_lon, end_lat, end_lon, 
                  slope_penalty_factor, obstacle_penalty_multiplier, 
                  slope_threshold, base_speed_kmh):
    """
    Computes terrain-aware shortest path using A*.
    Returns dict: { "route": [[lat, lon], ...], "distance_km": float, "eta_minutes": float }
    """
    # 1. Load DEM
    dem_path = '../data/dem_tile.tif'
    with rasterio.open(dem_path) as src:
        dem_data = src.read(1)
        transform = src.transform
        crs = src.crs

        # Function to get lat/lon from row/col
        def rc_to_latlon(r, c):
            lon, lat = rasterio.transform.xy(transform, r, c, offset='center')
            return lat, lon

        # Find closest pixels for start and end
        try:
            start_row, start_col = rasterio.transform.rowcol(transform, start_lon, start_lat)
            end_row, end_col = rasterio.transform.rowcol(transform, end_lon, end_lat)
        except Exception as e:
            raise ValueError(f"Start or end point is outside the DEM bounds: {e}")

        rows, cols = dem_data.shape

        # Bound checks
        start_row = max(0, min(rows - 1, start_row))
        start_col = max(0, min(cols - 1, start_col))
        end_row = max(0, min(rows - 1, end_row))
        end_col = max(0, min(cols - 1, end_col))

        # 2. Build Graph (on the fly or fully, we'll build it fully for this prototype)
        # To avoid massive memory usage for large DEMs, a custom A* is better, but NetworkX is required/allowed.
        # We will build a bounded graph around the bounding box of start/end with some padding to save time/memory.
        
        # Bounding box with tighter padding to prevent excessive detours
        # and keep the search focused around the direct path
        padding = max(15, int(max(abs(start_row - end_row), abs(start_col - end_col)) * 0.3))
        min_r = max(0, min(start_row, end_row) - padding)
        max_r = min(rows - 1, max(start_row, end_row) + padding)
        min_c = max(0, min(start_col, end_col) - padding)
        max_c = min(cols - 1, max(start_col, end_col) + padding)

        G = nx.DiGraph()
        
        # Precompute coordinates for the subset to speed up distance calculation
        # This assumes a geographic CRS for the raster for haversine
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

        for r in range(min_r, max_r + 1):
            for c in range(min_c, max_c + 1):
                lat1, lon1 = latlons[(r, c)]
                # Cast to float to prevent uint16/int16 overflow when subtracting
                z1 = float(dem_data[r, c])
                
                # Treat NoData as an impassable obstacle by not adding edges from it
                if nodata is not None and dem_data[r, c] == nodata:
                    continue
                
                for dr, dc in directions:
                    nr, nc = r + dr, c + dc
                    if min_r <= nr <= max_r and min_c <= nc <= max_c:
                        if nodata is not None and dem_data[nr, nc] == nodata:
                            continue
                            
                        lat2, lon2 = latlons[(nr, nc)]
                        z2 = float(dem_data[nr, nc])
                        
                        base_dist = haversine_distance(lat1, lon1, lat2, lon2)
                        if base_dist == 0:
                            continue
                            
                        elev_diff = z2 - z1
                        # Slope is absolute elevation diff over base distance
                        slope = abs(elev_diff) / base_dist
                        
                        penalty = 1.0 + (slope_penalty_factor * slope)
                        if slope > slope_threshold:
                            penalty *= obstacle_penalty_multiplier
                            
                        weight = base_dist * penalty
                        
                        G.add_edge((r, c), (nr, nc), weight=weight, base_dist=base_dist, penalty=penalty)

        # 3. A* Search
        def heuristic(n1, n2):
            lat1, lon1 = latlons[n1]
            lat2, lon2 = latlons[n2]
            return haversine_distance(lat1, lon1, lat2, lon2)

        start_node = (start_row, start_col)
        end_node = (end_row, end_col)

        try:
            path = nx.astar_path(G, start_node, end_node, heuristic=heuristic, weight='weight')
        except nx.NetworkXNoPath:
            raise ValueError("No path found between start and end.")

        # 4. Compute metrics
        total_dist_m = 0.0
        total_effective_weight = 0.0
        
        route_coords = []
        route_coords.append([latlons[path[0]][0], latlons[path[0]][1]])
        
        for i in range(len(path) - 1):
            u = path[i]
            v = path[i+1]
            edge_data = G[u][v]
            total_dist_m += edge_data['base_dist']
            total_effective_weight += edge_data['weight']
            
            route_coords.append([latlons[v][0], latlons[v][1]])

        distance_km = total_dist_m / 1000.0
        
        # Speed is reduced proportionally by the slope penalty factor.
        # This means time = (distance * penalty) / base_speed = effective_weight / base_speed
        effective_dist_km = total_effective_weight / 1000.0
        time_hours = effective_dist_km / base_speed_kmh
        eta_minutes = time_hours * 60.0

        return {
            "route": route_coords,
            "distance_km": round(distance_km, 3),
            "eta_minutes": round(eta_minutes, 2)
        }
