"""
Tests for builder.py - forecast response building
"""

import pytest
from lambdas.forecast.parser.builder import ForecastBuilder


class TestGetMaxValue:
    """Tests for get_max_value function"""
    
    @pytest.fixture
    def sample_data(self):
        """Sample raw data with multiple days"""
        return {
            'v0': '10:12:14:16:18:20:22:24;100:90:80:70:60:50:40:30',
            'v1': '8:9:10:11:12:13:14:15;80:85:90:95:100:95:90:85',
            'v2': '5:6:7:8:9:10:11:12;50:55:60:65:70:75:80:85',
        }
    
    def test_get_max_wave_height(self, sample_data):
        """Get maximum wave height (index 0)"""
        result = ForecastBuilder.get_max_value(sample_data, 'wave_height', 'v', False)
        assert result == 24  # Max from v0's first variable
    
    def test_get_max_with_division(self, sample_data):
        """Get max value with division by 10"""
        result = ForecastBuilder.get_max_value(sample_data, 'wave_height', 'v', True)
        assert result == 2.4  # 24 / 10
    
    def test_get_max_empty_data(self):
        """Empty data should return 0"""
        result = ForecastBuilder.get_max_value({}, 'wave_height', 'v', False)
        assert result == 0
    
    def test_get_max_invalid_variable(self, sample_data):
        """Invalid variable key should return 0"""
        result = ForecastBuilder.get_max_value(sample_data, 'invalid_key', 'v', False)
        assert result == 0


class TestGetMaxHeight:
    """Tests for get_max_height function"""
    
    def test_get_max_height(self):
        """Get maximum wave height across all days"""
        data = {
            'v0': '10:12:14:16:18:20:22:24',
            'v1': '15:17:19:21:23:25:27:29',  # Higher values
            'v2': '5:6:7:8:9:10:11:12',
        }
        
        result = ForecastBuilder.get_max_height(data, 'v')
        assert result == 2.9  # 29 / 10
    
    def test_get_max_height_beach_type(self):
        """Get max height using beach (s) prefix"""
        data = {
            's0': '10:15:20:25:30:35:40:45',
            's1': '5:6:7:8:9:10:11:12',
        }
        
        result = ForecastBuilder.get_max_height(data, 's')
        assert result == 4.5  # 45 / 10


class TestGetMaxWind:
    """Tests for get_max_wind function"""
    
    def test_get_max_wind(self):
        """Get maximum wind speed across all days"""
        atmospheric_data = {
            'v0': '10:12:14:16:18:20:22:24;180:180:180:180:180:180:180:180',
            'v1': '15:18:21:25:28:30:32:35;180:180:180:180:180:180:180:180',
        }
        
        result = ForecastBuilder.get_max_wind(atmospheric_data)
        assert result == 35  # Max wind from v1
    
    def test_get_max_wind_empty(self):
        """Empty data should return 0"""
        result = ForecastBuilder.get_max_wind({})
        assert result == 0


class TestBuildForecast:
    """Tests for build_forecast function"""
    
    @pytest.fixture
    def sample_beach_data(self):
        """Sample beach metadata from database"""
        return {
            'praia_id': 1,
            'id': 1,
            'nome': 'Maracaípe',
            'nome_2': 'Maracaípe',
            'orientacao': 92,
        }
    
    @pytest.fixture
    def sample_atmospheric_data(self):
        """Sample atmospheric data from S3"""
        return {
            'dados': {
                'ano': '2026',
                'mes': '03',
                'dia': '01',
                'v0': '10:12:14:16:18:20:22:24;180:190:200:180:190:200:180:180;15:18:20:22:25:28:30:32;0:0:0:0:0:0:0:0;1015:1014:1013:1012:1011:1012:1013:1014;28:27:26:28:30:32:31:29;20:30:50:70:80:60:40:25;0:0:0:5:10:5:0:0',
            }
        }
    
    @pytest.fixture
    def sample_oceanic_data(self):
        """Sample oceanic data from S3"""
        return {
            'dados': {
                'ano': '2026',
                'mes': '03',
                'dia': '01',
                'v0': '15:14:13:12:11:10:9:8;10:10:9:9:8:8:7:7;180:190:200:210:180:190:200:180;100:90:80:70:60:50:40:30;15:14:13:12:11:10:9:8;5:4:3:3:2:2:1:1;6:6:5:5:4:4:3:3;190:200:210:220:190:200:210:190;50:45:40:35:30:25:20:15;5:4:4:3:3:2:2:1;8:7:6:5:4:3:2:2;7:7:6:6:5:5:4:4;200:210:220:230:200:210:220:200;60:55:50:45:40:35:30:25;6:5:5:4:4:3:3:2;4:3:2:2:2:1:1:1;5:5:4:4:3:3:2:2;220:230:240:250:220:230:240:220;40:35:30:25:20:15:10:5;4:3:3:2:2:1:1:0;10:11:12:13:14:15:16:17;220:225:230:235:240:245:250:255;0:0:0:0:0:0:0:0;06001.5',
            }
        }
    
    def test_build_forecast_basic(self, sample_beach_data, sample_atmospheric_data, sample_oceanic_data):
        """Build a complete forecast response"""
        result = ForecastBuilder.build_forecast(
            beach_data=sample_beach_data,
            forecast_type='SURF',
            atmospheric_data=sample_atmospheric_data,
            oceanic_data=sample_oceanic_data
        )
        
        # Check top-level structure
        assert 'id' in result
        assert 'date' in result
        assert 'type' in result
        assert 'name' in result
        assert 'orientation' in result
        assert 'forecast' in result
        
        # Check values
        assert result['id'] == '1'
        assert result['type'] == 'SURF'
        assert result['name'] == 'Maracaípe'
        assert result['orientation'] == 92
        
        # Check forecast structure
        forecast = result['forecast']
        assert 'maxHeight' in forecast
        assert 'maxEnergy' in forecast
        assert 'maxPower' in forecast
        assert 'maxWind' in forecast
        assert 'days' in forecast
        
        # Check days array
        assert isinstance(forecast['days'], list)
        assert len(forecast['days']) == 15  # 15 days of forecast
    
    def test_build_forecast_day_structure(self, sample_beach_data, sample_atmospheric_data, sample_oceanic_data):
        """Check structure of individual days"""
        result = ForecastBuilder.build_forecast(
            beach_data=sample_beach_data,
            forecast_type='SURF',
            atmospheric_data=sample_atmospheric_data,
            oceanic_data=sample_oceanic_data
        )
        
        first_day = result['forecast']['days'][0]
        
        assert 'day' in first_day
        assert 'hours' in first_day
        assert 'tides' in first_day
        
        # Check first hour structure
        if first_day['hours']:
            first_hour = first_day['hours'][0]
            assert 'hour' in first_hour
            assert 'waves' in first_hour
            assert 'winds' in first_hour
            assert 'atmospheric' in first_hour
            
            # Check waves structure
            waves = first_hour['waves']
            assert 'totalHeight' in waves
            assert 'windseas' in waves
            assert 'swellA' in waves
            assert 'swellB' in waves
    
    def test_build_forecast_missing_atmospheric(self, sample_beach_data, sample_oceanic_data):
        """Build forecast with missing atmospheric data"""
        result = ForecastBuilder.build_forecast(
            beach_data=sample_beach_data,
            forecast_type='SURF',
            atmospheric_data=None,
            oceanic_data=sample_oceanic_data
        )
        
        # Should still build successfully
        assert result['type'] == 'SURF'
        assert len(result['forecast']['days']) == 15
