"""
Main forecast parser
Converts raw S3 data strings into structured forecast format matching SurfForecastResponse
"""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from .variables import (
    OCEAN_VARIABLES, BEACH_VARIABLES, ATMOSPHERIC_VARIABLES, 
    WIND_VARIABLES, TIME_HOURS, DIVISOR_FACTOR
)
from .directions import get_direction

logger = logging.getLogger(__name__)


class ForecastParser:
    """
    Parse raw forecast data from S3 into structured format
    
    Input: Raw data strings like "8:6:6:6:9:10:8:8;20:6:20:32:66:64:52:44;..."
    Output: Structured days/hours with waves, winds, atmospheric data
    """
    
    @staticmethod
    def divide_by_ten(value) -> float:
        """Divide a value by 10 (for heights, periods, etc.)"""
        try:
            return int(value) / DIVISOR_FACTOR
        except (TypeError, ValueError):
            return 0.0
    
    @staticmethod
    def parse_day_variables(data_string: str) -> Optional[List[List[str]]]:
        """
        Parse a day's data string into a 2D array of variables and hourly values
        
        Args:
            data_string: Raw string like "8:6:6:6:9:10:8:8;20:6:20:32:66:64:52:44;..."
            
        Returns:
            List of variables, each containing 8 hourly values
            e.g., [['8', '6', '6', '6', '9', '10', '8', '8'], ...]
        """
        if not data_string:
            return None
        
        try:
            variables = data_string.split(';')
            return [v.split(':') for v in variables]
        except Exception as e:
            logger.warning(f"Failed to parse day variables: {e}")
            return None
    
    @staticmethod
    def parse_tides(tides_string: str) -> List[Dict[str, str]]:
        """
        Parse tide data string into structured format
        
        Args:
            tides_string: String like "05001.50912.2" 
                          (time HHMM + height D.D format, repeated)
                          
        Returns:
            List of {time, height} dicts
        """
        if not tides_string or len(tides_string) < 6:
            return []
        
        tides = []
        try:
            # Each tide entry is 6 characters: HHMM + D.D
            tides_size = len(tides_string) // 6
            for i in range(tides_size):
                index = i * 6
                if index + 6 <= len(tides_string):
                    time_str = f"{tides_string[index]}{tides_string[index+1]}:{tides_string[index+2]}{tides_string[index+3]}"
                    height_str = f"{tides_string[index+4]}.{tides_string[index+5]}"
                    tides.append({
                        'time': time_str,
                        'height': height_str
                    })
        except Exception as e:
            logger.warning(f"Failed to parse tides: {e}")
        
        return tides
    
    @staticmethod
    def get_wind_type(beach_orientation: int, wind_direction: int) -> str:
        """
        Determine wind type based on beach orientation and wind direction
        
        Args:
            beach_orientation: Beach facing direction in degrees
            wind_direction: Wind coming from direction in degrees
            
        Returns:
            'OFFSHORE', 'ONSHORE', or 'CROSSED'
        """
        try:
            angle = beach_orientation - int(wind_direction)
            
            # Normalize angle to -180 to 180
            if angle > 180 or angle < -180:
                if beach_orientation < wind_direction:
                    angle = beach_orientation + 360 - wind_direction
                else:
                    angle = beach_orientation - (wind_direction + 360)
            
            angle = abs(angle)
            
            if angle > 125:
                return 'OFFSHORE'
            elif angle > 65:
                return 'CROSSED'
            return 'ONSHORE'
        except (TypeError, ValueError):
            return 'OCEANIC'
    
    @classmethod
    def parse_waves(cls, oceanic_vars: List[List[str]], beach_vars: Optional[List[List[str]]], index: int) -> Dict:
        """
        Parse wave data for a specific hour
        
        Args:
            oceanic_vars: Parsed oceanic variables
            beach_vars: Parsed beach-specific variables (optional)
            index: Hour index (0-7)
            
        Returns:
            Structured wave data with totalHeight, windseas, swellA, swellB
        """
        def safe_get(vars_list: List[List[str]], var_index: int, hour_index: int, default: str = '0') -> str:
            try:
                return vars_list[var_index][hour_index]
            except (IndexError, TypeError):
                return default
        
        # Helper to get value - prefer beach data if available
        def get_wave_value(oceanic_key: str, beach_key: str, hour_idx: int, divide: bool = True):
            if beach_vars:
                val = safe_get(beach_vars, BEACH_VARIABLES[beach_key], hour_idx)
            else:
                val = safe_get(oceanic_vars, OCEAN_VARIABLES[oceanic_key], hour_idx)
            
            return cls.divide_by_ten(val) if divide else int(val)
        
        return {
            'totalHeight': {
                'value': get_wave_value('wave_height', 'wave_height', index),
                'period': cls.divide_by_ten(safe_get(oceanic_vars, OCEAN_VARIABLES['wave_period'], index)),
                'direction': get_direction(safe_get(oceanic_vars, OCEAN_VARIABLES['primary_direction'], index)),
                'directionDegree': int(safe_get(oceanic_vars, OCEAN_VARIABLES['primary_direction'], index, '0')),
                'power': cls.divide_by_ten(safe_get(oceanic_vars, OCEAN_VARIABLES['total_power'], index)),
                'energy': int(safe_get(oceanic_vars, OCEAN_VARIABLES['total_energy'], index, '0')),
            },
            'windseas': {
                'value': get_wave_value('windseas_height', 'windseas_height', index),
                'period': cls.divide_by_ten(safe_get(oceanic_vars, OCEAN_VARIABLES['windseas_period'], index)),
                'direction': get_direction(safe_get(oceanic_vars, OCEAN_VARIABLES['windseas_direction'], index)),
                'directionDegree': int(safe_get(oceanic_vars, OCEAN_VARIABLES['windseas_direction'], index, '0')),
                'power': cls.divide_by_ten(safe_get(oceanic_vars, OCEAN_VARIABLES['windseas_power'], index)),
                'energy': int(safe_get(oceanic_vars, OCEAN_VARIABLES['windseas_energy'], index, '0')),
            },
            'swellA': {
                'value': get_wave_value('swell_a_height', 'primary_swell_height', index),
                'period': cls.divide_by_ten(safe_get(oceanic_vars, OCEAN_VARIABLES['swell_a_period'], index)),
                'direction': get_direction(safe_get(oceanic_vars, OCEAN_VARIABLES['swell_a_direction'], index)),
                'directionDegree': int(safe_get(oceanic_vars, OCEAN_VARIABLES['swell_a_direction'], index, '0')),
                'power': cls.divide_by_ten(safe_get(oceanic_vars, OCEAN_VARIABLES['swell_a_power'], index)),
                'energy': int(safe_get(oceanic_vars, OCEAN_VARIABLES['swell_a_energy'], index, '0')),
            },
            'swellB': {
                'value': get_wave_value('swell_b_height', 'secondary_swell_height', index),
                'period': cls.divide_by_ten(safe_get(oceanic_vars, OCEAN_VARIABLES['swell_b_period'], index)),
                'direction': get_direction(safe_get(oceanic_vars, OCEAN_VARIABLES['swell_b_direction'], index)),
                'directionDegree': int(safe_get(oceanic_vars, OCEAN_VARIABLES['swell_b_direction'], index, '0')),
                'power': cls.divide_by_ten(safe_get(oceanic_vars, OCEAN_VARIABLES['swell_b_power'], index)),
                'energy': int(safe_get(oceanic_vars, OCEAN_VARIABLES['swell_b_energy'], index, '0')),
            },
        }
    
    @classmethod
    def parse_winds(cls, beach_orientation: Optional[int], atmospheric_vars: Optional[List[List[str]]], 
                    oceanic_vars: List[List[str]], forecast_type: str, index: int) -> Dict:
        """
        Parse wind data for a specific hour
        
        Args:
            beach_orientation: Beach facing direction (for wind type calculation)
            atmospheric_vars: Parsed atmospheric variables
            oceanic_vars: Parsed oceanic variables
            forecast_type: 'SURF' or 'OCEANIC'
            index: Hour index (0-7)
            
        Returns:
            Structured wind data with coast and sea wind info
        """
        def safe_get(vars_list: Optional[List[List[str]]], var_index: int, hour_index: int, default: str = '0') -> str:
            if not vars_list:
                return default
            try:
                return vars_list[var_index][hour_index]
            except (IndexError, TypeError):
                return default
        
        wind_direction = safe_get(atmospheric_vars, WIND_VARIABLES['wind_direction'], index)
        wind_type = 'OCEANIC'
        
        if forecast_type == 'SURF' and beach_orientation is not None:
            wind_type = cls.get_wind_type(beach_orientation, wind_direction)
        
        return {
            'coast': {
                'directionDegree': int(safe_get(atmospheric_vars, WIND_VARIABLES['wind_direction'], index, '0')),
                'wind': int(safe_get(atmospheric_vars, WIND_VARIABLES['wind'], index, '0')),
                'windGust': int(safe_get(atmospheric_vars, WIND_VARIABLES['wind_gust'], index, '0')),
                'pressure': safe_get(atmospheric_vars, ATMOSPHERIC_VARIABLES['pressure'], index, '0'),
                'type': wind_type,
                'direction': get_direction(wind_direction),
            },
            'sea': {
                'direction': int(safe_get(oceanic_vars, OCEAN_VARIABLES['sea_wind_direction'], 0, '0')),
                'wind': int(safe_get(oceanic_vars, OCEAN_VARIABLES['sea_wind'], 0, '0')),
            },
        }
    
    @classmethod
    def parse_atmospheric(cls, atmospheric_vars: Optional[List[List[str]]], index: int) -> Dict:
        """
        Parse atmospheric data for a specific hour
        
        Args:
            atmospheric_vars: Parsed atmospheric variables
            index: Hour index (0-7)
            
        Returns:
            Structured atmospheric data
        """
        def safe_get(vars_list: Optional[List[List[str]]], var_index: int, hour_index: int, default: int = 0) -> int:
            if not vars_list:
                return default
            try:
                return int(vars_list[var_index][hour_index])
            except (IndexError, TypeError, ValueError):
                return default
        
        return {
            'pressure': safe_get(atmospheric_vars, ATMOSPHERIC_VARIABLES['pressure'], index),
            'temperature': safe_get(atmospheric_vars, ATMOSPHERIC_VARIABLES['temperature'], index),
            'clouds': safe_get(atmospheric_vars, ATMOSPHERIC_VARIABLES['clouds'], index),
            'precipitation': safe_get(atmospheric_vars, ATMOSPHERIC_VARIABLES['precipitation'], index),
            'stormPotential': safe_get(atmospheric_vars, ATMOSPHERIC_VARIABLES['storm_potential'], index),
        }
    
    @classmethod
    def parse_wave_hours(cls, beach_orientation: Optional[int], oceanic_vars: List[List[str]], 
                         beach_vars: Optional[List[List[str]]], atmospheric_vars: Optional[List[List[str]]], 
                         forecast_type: str) -> List[Dict]:
        """
        Parse all 8 hours of wave data for a day
        
        Returns:
            List of hourly data dicts
        """
        hours = []
        for idx, hour in enumerate(TIME_HOURS):
            hours.append({
                'hour': f"{str(hour).zfill(2)}:00",
                'waves': cls.parse_waves(oceanic_vars, beach_vars, idx),
                'winds': cls.parse_winds(beach_orientation, atmospheric_vars, oceanic_vars, forecast_type, idx),
                'atmospheric': cls.parse_atmospheric(atmospheric_vars, idx),
            })
        return hours
    
    @classmethod
    def parse_days(cls, atmospheric_data: Dict, oceanic_data: Dict, 
                   beach_orientation: Optional[int], forecast_type: str) -> List[Dict]:
        """
        Parse 15 days of forecast data
        
        Args:
            atmospheric_data: Raw atmospheric data from S3 (has 'dados' with v0-v14 keys)
            oceanic_data: Raw oceanic/beach data from S3 (has 'dados' with v0-v14 and/or s0-s14 keys)
            beach_orientation: Beach facing direction in degrees
            forecast_type: 'SURF' or 'OCEANIC'
            
        Returns:
            List of day dicts with date, hours, and tides
        """
        atmos_dados = atmospheric_data.get('dados', {}) if atmospheric_data else {}
        ocean_dados = oceanic_data.get('dados', {}) if oceanic_data else {}
        
        # Get date from oceanic data (first day)
        try:
            date_string = f"{ocean_dados.get('ano', datetime.now().year)}-{ocean_dados.get('mes', datetime.now().month)}-{ocean_dados.get('dia', datetime.now().day)}"
            base_date = datetime.strptime(date_string, '%Y-%m-%d')
        except (ValueError, TypeError):
            base_date = datetime.now()
        
        days = []
        for day_idx in range(15):
            current_date = base_date + timedelta(days=day_idx)
            date_str = current_date.strftime('%Y-%m-%d')
            
            # Parse variables for this day
            # v0-v14 for oceanic/atmospheric, s0-s14 for beach-specific
            oceanic_key = f'v{day_idx}'
            beach_key = f's{day_idx}'
            
            oceanic_vars = cls.parse_day_variables(ocean_dados.get(oceanic_key, ''))
            beach_vars = cls.parse_day_variables(ocean_dados.get(beach_key, ''))
            atmospheric_vars = cls.parse_day_variables(atmos_dados.get(oceanic_key, ''))
            
            # If no oceanic data, skip this day
            if not oceanic_vars:
                days.append({
                    'day': date_str,
                    'hours': [],
                    'tides': [],
                })
                continue
            
            # Parse hours
            hours = cls.parse_wave_hours(
                beach_orientation, 
                oceanic_vars, 
                beach_vars, 
                atmospheric_vars, 
                forecast_type
            )
            
            # Parse tides (only on first day, from oceanic vars)
            tides = []
            if day_idx == 0 and len(oceanic_vars) > OCEAN_VARIABLES['tides']:
                tides_str = oceanic_vars[OCEAN_VARIABLES['tides']][0] if oceanic_vars[OCEAN_VARIABLES['tides']] else ''
                tides = cls.parse_tides(tides_str)
            
            days.append({
                'day': date_str,
                'hours': hours,
                'tides': tides,
            })
        
        return days
