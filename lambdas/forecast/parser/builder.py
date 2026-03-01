"""
Forecast response builder
Assembles the final SurfForecastResponse format
"""

import logging
from datetime import datetime
from typing import Any, Dict, Optional

from .parser import ForecastParser
from .variables import OCEAN_VARIABLES, DIVISOR_FACTOR

logger = logging.getLogger(__name__)


class ForecastBuilder:
    """
    Build forecast response in SurfForecastResponse format
    """
    
    @staticmethod
    def get_max_value(data: Dict, var_key: str, var_type: str = 'v', should_divide: bool = False) -> float:
        """
        Extract maximum value across all days for a variable
        
        Args:
            data: Raw data dict with v0-v14 or s0-s14 keys
            var_key: Key in OCEAN_VARIABLES
            var_type: 'v' for oceanic, 's' for beach
            should_divide: Whether to divide by 10
            
        Returns:
            Maximum value
        """
        if not data:
            return 0.0
        
        max_val = 0
        var_index = OCEAN_VARIABLES.get(var_key)
        
        if var_index is None:
            return 0.0
        
        for day_idx in range(15):
            key = f'{var_type}{day_idx}'
            day_string = data.get(key, '')
            
            if not day_string:
                continue
            
            try:
                variables = day_string.split(';')
                if var_index < len(variables):
                    values = variables[var_index].split(':')
                    for val in values:
                        try:
                            num_val = int(val)
                            if num_val > max_val:
                                max_val = num_val
                        except ValueError:
                            pass
            except Exception as e:
                logger.warning(f"Error extracting max value: {e}")
        
        return max_val / DIVISOR_FACTOR if should_divide else max_val
    
    @staticmethod
    def get_max_height(data: Dict, var_type: str = 'v') -> float:
        """Get maximum wave height across all days"""
        return ForecastBuilder.get_max_value(data, 'wave_height', var_type, should_divide=True)
    
    @staticmethod
    def get_max_wind(atmospheric_data: Dict) -> int:
        """Get maximum wind speed across all days"""
        if not atmospheric_data:
            return 0
        
        max_wind = 0
        
        for day_idx in range(15):
            key = f'v{day_idx}'
            day_string = atmospheric_data.get(key, '')
            
            if not day_string:
                continue
            
            try:
                variables = day_string.split(';')
                # Wind is at index 0
                if len(variables) > 0:
                    values = variables[0].split(':')
                    for val in values:
                        try:
                            num_val = int(val)
                            if num_val > max_wind:
                                max_wind = num_val
                        except ValueError:
                            pass
            except Exception as e:
                logger.warning(f"Error extracting max wind: {e}")
        
        return max_wind
    
    @classmethod
    def build_forecast(cls, beach_data: Dict, forecast_type: str, 
                       atmospheric_data: Dict, oceanic_data: Dict) -> Dict:
        """
        Build complete forecast response
        
        Args:
            beach_data: Beach metadata from database (id, nome, orientacao, etc.)
            forecast_type: 'SURF' or 'OCEANIC'
            atmospheric_data: Raw atmospheric data from S3
            oceanic_data: Raw oceanic/beach data from S3
            
        Returns:
            Complete forecast response matching SurfForecastResponse
        """
        ocean_dados = oceanic_data.get('dados', {}) if oceanic_data else {}
        
        # Get date string
        try:
            date_str = f"{ocean_dados.get('ano', datetime.now().year)}-{ocean_dados.get('mes', datetime.now().month)}-{ocean_dados.get('dia', datetime.now().day)}"
        except:
            date_str = datetime.now().strftime('%Y-%m-%d')
        
        # Get beach orientation
        orientation = beach_data.get('orientacao')
        beach_orientation = int(orientation) if orientation else None
        
        # Parse days
        days = ForecastParser.parse_days(
            atmospheric_data, 
            oceanic_data, 
            beach_orientation, 
            forecast_type
        )
        
        # Calculate max values
        max_height = cls.get_max_height(ocean_dados, 'v')
        max_energy = cls.get_max_value(ocean_dados, 'total_energy', 'v', should_divide=False)
        max_power = cls.get_max_value(ocean_dados, 'total_power', 'v', should_divide=True)
        
        atmos_dados = atmospheric_data.get('dados', {}) if atmospheric_data else {}
        max_wind = cls.get_max_wind(atmos_dados)
        
        # Build forecast object
        forecast_obj = {
            'maxHeight': max_height,
            'maxEnergy': max_energy,
            'maxPower': max_power,
            'maxWind': max_wind,
            'days': days,
        }
        
        # Add map URL if available
        map_name = beach_data.get('nome_do_mapa')
        if map_name:
            map_date = beach_data.get('dt_mapa_atualizado', '')
            forecast_obj['forecastMapUrl'] = f"https://surfguru.space/mapas/{map_name}{map_date}.png"
        
        # Build complete response
        response = {
            'id': str(beach_data.get('praia_id', beach_data.get('id', ''))),
            'date': date_str,
            'type': forecast_type,
            'name': beach_data.get('nome', beach_data.get('nome_2', '')),
            'orientation': beach_orientation or 0,
            'forecast': forecast_obj,
        }
        
        return response
