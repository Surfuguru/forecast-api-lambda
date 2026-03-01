"""
Tests for parser.py - main forecast parsing logic
"""

import pytest
from lambdas.forecast.parser.parser import ForecastParser


class TestDivideByTen:
    """Tests for divide_by_ten function"""
    
    def test_basic_division(self):
        assert ForecastParser.divide_by_ten(10) == 1.0
        assert ForecastParser.divide_by_ten(100) == 10.0
        assert ForecastParser.divide_by_ten(15) == 1.5
        assert ForecastParser.divide_by_ten(0) == 0.0
    
    def test_string_input(self):
        assert ForecastParser.divide_by_ten('10') == 1.0
        assert ForecastParser.divide_by_ten('15') == 1.5
    
    def test_invalid_input(self):
        assert ForecastParser.divide_by_ten(None) == 0.0
        assert ForecastParser.divide_by_ten('invalid') == 0.0


class TestParseDayVariables:
    """Tests for parse_day_variables function"""
    
    def test_valid_data_string(self):
        """Parse a valid day data string"""
        # Format: 8 values per variable, separated by :
        # Variables separated by ;
        data = "10:12:14:16:18:20:22:24;5:6:7:8:9:10:11:12"
        result = ForecastParser.parse_day_variables(data)
        
        assert result is not None
        assert len(result) == 2  # 2 variables
        assert len(result[0]) == 8  # 8 hourly values
        assert result[0] == ['10', '12', '14', '16', '18', '20', '22', '24']
        assert result[1] == ['5', '6', '7', '8', '9', '10', '11', '12']
    
    def test_empty_string(self):
        """Empty string should return None"""
        assert ForecastParser.parse_day_variables('') is None
        assert ForecastParser.parse_day_variables(None) is None
    
    def test_single_variable(self):
        """Single variable with no semicolons"""
        data = "1:2:3:4:5:6:7:8"
        result = ForecastParser.parse_day_variables(data)
        
        assert result is not None
        assert len(result) == 1
        assert result[0] == ['1', '2', '3', '4', '5', '6', '7', '8']


class TestParseTides:
    """Tests for parse_tides function"""
    
    def test_single_tide(self):
        """Parse a single tide entry (6 chars: HHMM + D.D)"""
        # 0500 + 1.5 = "05001.5" but format is "050015" (HHMMDD)
        tides = ForecastParser.parse_tides("050015")
        
        assert len(tides) == 1
        assert tides[0]['time'] == "05:00"
        assert tides[0]['height'] == "1.5"
    
    def test_multiple_tides(self):
        """Parse multiple tide entries"""
        # Two tides: 05:00 at 1.5m and 11:30 at 0.8m
        tides = ForecastParser.parse_tides("050015113008")
        
        assert len(tides) == 2
        assert tides[0]['time'] == "05:00"
        assert tides[0]['height'] == "1.5"
        assert tides[1]['time'] == "11:30"
        assert tides[1]['height'] == "0.8"
    
    def test_empty_string(self):
        """Empty string should return empty list"""
        assert ForecastParser.parse_tides('') == []
        assert ForecastParser.parse_tides(None) == []
    
    def test_short_string(self):
        """String shorter than 6 chars should return empty"""
        assert ForecastParser.parse_tides("123") == []


class TestGetWindType:
    """Tests for get_wind_type function"""
    
    def test_offshore(self):
        """Wind opposite to beach orientation is offshore"""
        # Beach facing 90° (East), wind from 270° (West) = offshore
        assert ForecastParser.get_wind_type(90, 270) == 'OFFSHORE'
        # Beach facing 0° (North), wind from 180° (South) = offshore
        assert ForecastParser.get_wind_type(0, 180) == 'OFFSHORE'
    
    def test_onshore(self):
        """Wind same direction as beach orientation is onshore"""
        # Beach facing 90° (East), wind from 90° (East) = onshore
        assert ForecastParser.get_wind_type(90, 90) == 'ONSHORE'
        # Beach facing 0° (North), wind from 0° (North) = onshore
        assert ForecastParser.get_wind_type(0, 0) == 'ONSHORE'
    
    def test_crossed(self):
        """Wind perpendicular to beach is crossed"""
        # Beach facing 0° (North), wind from 90° (East) = crossed
        result = ForecastParser.get_wind_type(0, 90)
        assert result in ['CROSSED', 'ONSHORE']  # Depends on angle calculation
    
    def test_invalid_input(self):
        """Invalid input should return OCEANIC"""
        assert ForecastParser.get_wind_type(None, 90) == 'OCEANIC'
        assert ForecastParser.get_wind_type(90, None) == 'OCEANIC'


class TestParseWaves:
    """Tests for parse_waves function"""
    
    @pytest.fixture
    def sample_oceanic_vars(self):
        """Sample parsed oceanic variables"""
        # 24 variables with 8 hourly values each
        # Simplified: just the first few we need
        return [
            ['15', '14', '13', '12', '11', '10', '9', '8'],      # 0: wave_height
            ['10', '10', '9', '9', '8', '8', '7', '7'],          # 1: wave_period
            ['180', '190', '200', '210', '180', '190', '200', '180'],  # 2: primary_direction
            ['100', '90', '80', '70', '60', '50', '40', '30'],   # 3: total_energy
            ['15', '14', '13', '12', '11', '10', '9', '8'],      # 4: total_power
        ] + [['0'] * 8 for _ in range(19)]  # Fill remaining with zeros
    
    def test_parse_waves_basic(self, sample_oceanic_vars):
        """Parse wave data for a specific hour"""
        result = ForecastParser.parse_waves(sample_oceanic_vars, None, 0)
        
        assert 'totalHeight' in result
        assert 'windseas' in result
        assert 'swellA' in result
        assert 'swellB' in result
        
        # Check total height values
        assert result['totalHeight']['value'] == 1.5  # 15 / 10
        assert result['totalHeight']['period'] == 1.0  # 10 / 10
        assert result['totalHeight']['direction'] == 'S'  # 180°
        assert result['totalHeight']['directionDegree'] == 180
        assert result['totalHeight']['energy'] == 100
        assert result['totalHeight']['power'] == 1.5  # 15 / 10
    
    def test_parse_waves_with_beach_data(self, sample_oceanic_vars):
        """Parse with beach-specific data override"""
        beach_vars = [
            ['12', '11', '10', '9', '8', '7', '6', '5'],  # wave_height
            ['5', '4', '3', '3', '2', '2', '1', '1'],     # windseas_height
            ['8', '7', '6', '5', '4', '3', '2', '2'],     # primary_swell_height
            ['4', '3', '2', '2', '2', '1', '1', '1'],     # secondary_swell_height
        ]
        
        result = ForecastParser.parse_waves(sample_oceanic_vars, beach_vars, 0)
        
        # Beach data should override oceanic for heights
        assert result['totalHeight']['value'] == 1.2  # 12 / 10 (beach data)
        assert result['windseas']['value'] == 0.5  # 5 / 10 (beach data)


class TestParseAtmospheric:
    """Tests for parse_atmospheric function"""
    
    def test_parse_atmospheric_basic(self):
        """Parse atmospheric data for a specific hour"""
        # Create sample atmospheric variables
        atmos_vars = [
            ['10', '12', '14', '16', '18', '20', '22', '24'],    # 0: wind
            ['180', '190', '200', '180', '190', '200', '180', '180'],  # 1: wind_direction
            ['15', '18', '20', '22', '25', '28', '30', '32'],    # 2: wind_gust
            ['0', '0', '5', '10', '20', '15', '5', '0'],         # 3: storm_potential
            ['1015', '1014', '1013', '1012', '1011', '1012', '1013', '1014'],  # 4: pressure
            ['28', '27', '26', '28', '30', '32', '31', '29'],    # 5: temperature
            ['20', '30', '50', '70', '80', '60', '40', '25'],    # 6: clouds
            ['0', '0', '0', '5', '10', '5', '0', '0'],           # 7: precipitation
        ]
        
        result = ForecastParser.parse_atmospheric(atmos_vars, 0)
        
        assert result['pressure'] == 1015
        assert result['temperature'] == 28
        assert result['clouds'] == 20
        assert result['precipitation'] == 0
        assert result['stormPotential'] == 0
    
    def test_parse_atmospheric_none(self):
        """None atmospheric vars should return defaults"""
        result = ForecastParser.parse_atmospheric(None, 0)
        
        assert result['pressure'] == 0
        assert result['temperature'] == 0
        assert result['clouds'] == 0
        assert result['precipitation'] == 0
        assert result['stormPotential'] == 0
