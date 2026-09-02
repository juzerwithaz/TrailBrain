import time
import random
from typing import Dict, Any, List

class SARDetector:
    """
    Search and Rescue Computer Vision Inference Pipeline.
    Simulates dual-band RGB + FLIR Thermal human detection.
    """
    def __init__(self, confidence_threshold: float = 0.85):
        self.confidence_threshold = confidence_threshold

    def process_frame(self, frame_metadata: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Processes an aerial frame metadata dict and detects human targets.
        """
        detections = []
        # Check if target is in field of view
        has_target = frame_metadata.get("target_in_view", True)
        if has_target:
            confidence = random.uniform(0.91, 0.98)
            if confidence >= self.confidence_threshold:
                detections.append({
                    "class_name": "person",
                    "confidence": round(confidence, 3),
                    "bbox_norm": {
                        "u": frame_metadata.get("u_norm", 0.05),
                        "v": frame_metadata.get("v_norm", -0.10),
                        "width": 0.08,
                        "height": 0.12
                    },
                    "thermal_signature": {
                        "is_thermal": True,
                        "apparent_temp_c": round(random.uniform(34.5, 37.0), 1),
                        "ambient_temp_c": 12.0
                    },
                    "timestamp": time.time()
                })
        return detections
