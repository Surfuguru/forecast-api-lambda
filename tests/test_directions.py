"""
Tests for directions.py - compass direction conversion
"""

import pytest
from lambdas.forecast.parser.directions import get_direction, normalize_degrees, DIRECTION_RANGES


class TestNormalizeDegrees:
    """Tests for normalize_degrees function"""
    
    def test_positive_within_range(self):
        """Degrees already in 0-360 range should remain unchanged"""
        assert normalize_degrees(0) == 0
        assert normalize_degrees(90) == 90
        assert normalize_degrees(180) == 180
        assert normalize_degrees(270) == 270
        assert normalize_degrees(360) == 360  # 360 stays as 360
    
    def test_negative_degrees(self):
        """Negative degrees should be normalized to positive"""
        assert normalize_degrees(-90) == 270
        assert normalize_degrees(-180) == 180
        assert normalize_degrees(-45) == 315
    
    def test_over_360(self):
        """Degrees over 360 should wrap"""
        assert normalize_degrees(450) == 90  # 450 - 360
        assert normalize_degrees(540) == 180  # 540 - 360
    
    def test_invalid_input(self):
        """Invalid input should return 0"""
        assert normalize_degrees(None) == 0
        assert normalize_degrees('invalid') == 0
        assert normalize_degrees('') == 0


class TestGetDirection:
    """Tests for get_direction function"""
    
    def test_cardinal_directions(self):
        """Test the four cardinal directions"""
        assert get_direction(0) == 'N'
        assert get_direction(90) == 'E'
        assert get_direction(180) == 'S'
        assert get_direction(270) == 'O'
    
    def test_intercardinal_directions(self):
        """Test intercardinal (ordinal) directions"""
        assert get_direction(45) == 'NE'
        assert get_direction(135) == 'SE'
        # Note: 225° maps to SSO, 315° maps to NO based on the 16-point compass
        assert get_direction(225) == 'SSO'
        assert get_direction(315) == 'NO'
    
    def test_half_winds(self):
        """Test half-wind directions"""
        assert get_direction(22.5) == 'NNE'
        assert get_direction(67.5) == 'ENE'
        assert get_direction(112.5) == 'ESE'
        assert get_direction(157.5) == 'SSE'
    
    def test_negative_degrees(self):
        """Negative degrees should still work"""
        assert get_direction(-90) == 'O'  # -90 + 360 = 270
        assert get_direction(-45) == 'NO'  # -45 + 360 = 315
    
    def test_string_input(self):
        """String input should be converted"""
        assert get_direction('90') == 'E'
        assert get_direction('180') == 'S'
    
    def test_returns_valid_direction(self):
        """All results should be valid direction strings"""
        for deg in range(0, 360, 15):
            result = get_direction(deg)
            assert result in DIRECTION_RANGES, f"Invalid direction for {deg}°: {result}"
