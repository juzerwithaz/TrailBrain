import math

def calculate_ground_coordinate(
    drone_lat: float,
    drone_lon: float,
    drone_alt_agl_m: float,
    gimbal_pitch_deg: float = -45.0,
    drone_heading_deg: float = 0.0,
    u_norm: float = 0.0,
    v_norm: float = 0.0,
    fov_h_deg: float = 84.0,
    fov_v_deg: float = 56.0
):
    """
    Projects a 2D bounding box center from drone camera sensor to real-world ground GPS coordinates.
    
    Parameters:
    - drone_lat, drone_lon: Drone's GPS position in degrees.
    - drone_alt_agl_m: Altitude Above Ground Level (AGL) in meters.
    - gimbal_pitch_deg: Camera pitch (-90 is nadir/straight down, 0 is horizontal).
    - drone_heading_deg: Heading/yaw relative to true North (0-360 deg).
    - u_norm: Horizontal offset of detection on camera sensor (-1.0 = left, 0.0 = center, +1.0 = right).
    - v_norm: Vertical offset of detection on camera sensor (-1.0 = top, 0.0 = center, +1.0 = bottom).
    - fov_h_deg, fov_v_deg: Horizontal and vertical Field of View of camera lens.
    
    Returns:
    (target_lat, target_lon, ground_distance_m)
    """
    # Angular offsets of target relative to camera optical axis
    angle_offset_h = (u_norm * fov_h_deg) / 2.0
    angle_offset_v = (v_norm * fov_v_deg) / 2.0
    
    # Effective pitch angle of the optical ray hitting the target
    effective_pitch_deg = gimbal_pitch_deg - angle_offset_v
    
    # Prevent parallel or upward rays (clamped to at least 5 degrees downward)
    clamped_pitch = max(-89.9, min(-5.0, effective_pitch_deg))
    pitch_rad = math.radians(abs(clamped_pitch))
    
    # Horizontal distance on the ground from drone to target
    ground_dist_m = drone_alt_agl_m / math.tan(pitch_rad)
    
    # Effective bearing from true north
    effective_bearing_deg = (drone_heading_deg + angle_offset_h) % 360.0
    bearing_rad = math.radians(effective_bearing_deg)
    
    # Earth displacement math (WGS-84 local approximation)
    R_earth = 6371000.0  # meters
    delta_lat = (ground_dist_m * math.cos(bearing_rad)) / R_earth
    delta_lon = (ground_dist_m * math.sin(bearing_rad)) / (R_earth * math.cos(math.radians(drone_lat)))
    
    target_lat = drone_lat + math.degrees(delta_lat)
    target_lon = drone_lon + math.degrees(delta_lon)
    
    return round(target_lat, 6), round(target_lon, 6), round(ground_dist_m, 1)
