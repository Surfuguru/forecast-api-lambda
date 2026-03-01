"""
Convert wind/wave direction degrees to compass direction strings
"""

# 16-point compass directions (matching the original TypeScript implementation)
DIRECTION_RANGES = [
    'N',
    'NNE',
    'NE',
    'ENE',
    'E',
    'ESE',
    'SE',
    'SSE',
    'S',
    'SSO',
    'SSO',  # Note: duplicate in original
    'OSO',
    'O',
    'ONO',
    'NO',
    'NNO',
]


def normalize_degrees(degrees_value):
    """Normalize degrees to 0-360 range"""
    try:
        degrees = float(degrees_value)
    except (TypeError, ValueError):
        return 0
    
    if degrees < 0:
        return degrees + 360
    elif degrees > 360:
        return degrees - 360
    return degrees


def get_direction(degrees_value):
    """
    Convert degrees to compass direction string
    
    Args:
        degrees_value: Direction in degrees (0-360)
        
    Returns:
        Compass direction string (e.g., 'N', 'NNE', 'NE', etc.)
    """
    degrees = normalize_degrees(degrees_value)
    quadrant_in_32 = (degrees / 11.25) % 32 + 1
    quadrant = int(quadrant_in_32 / 2)
    quadrant_number = quadrant - 16 if quadrant >= 16 else quadrant
    return DIRECTION_RANGES[quadrant_number]
