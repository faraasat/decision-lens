import math
import numpy as np
from typing import Any

def clean_json_data(obj: Any) -> Any:
    """
    Recursively convert objects to JSON-serializable formats.
    Handles NaN, Infinity, and Numpy types.
    """
    if isinstance(obj, float):
        if math.isnan(obj) or math.isinf(obj):
            return 0
        return float(obj)
    if isinstance(obj, (np.integer, int)):
        return int(obj)
    if isinstance(obj, (np.floating, np.float32, np.float64, float)):
        if math.isnan(obj) or math.isinf(obj):
            return 0
        return float(obj)
    if isinstance(obj, np.ndarray):
        return clean_json_data(obj.tolist())
    if isinstance(obj, dict):
        return {str(k): clean_json_data(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [clean_json_data(x) for x in obj]
    return obj
