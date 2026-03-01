"""
Index constants for parsing raw forecast data strings

Raw data format: "value1:value2:...:value8;var1:var2:...:var23"
- Split by ";" to get individual variables (24 total)
- Split by ":" to get 8 hourly values per variable (00:00, 03:00, 06:00, 09:00, 12:00, 15:00, 18:00, 21:00)
"""

# Oceanic variables (from oceanos/oceano{id}.json or used as fallback)
OCEAN_VARIABLES = {
    'wave_height': 0,           # Altura total das ondas (dividir por 10)
    'wave_period': 1,           # Período (dividir por 10)
    'primary_direction': 2,     # Direção primária em graus
    'total_energy': 3,          # Energia total
    'total_power': 4,           # Potência total (dividir por 10)
    'windseas_height': 5,       # Altura do vento marítimo (dividir por 10)
    'windseas_period': 6,       # Período do vento marítimo (dividir por 10)
    'windseas_direction': 7,    # Direção do vento marítimo
    'windseas_energy': 8,       # Energia do vento marítimo
    'windseas_power': 9,        # Potência do vento marítimo (dividir por 10)
    'swell_a_height': 10,       # Altura swell A (dividir por 10)
    'swell_a_period': 11,       # Período swell A (dividir por 10)
    'swell_a_direction': 12,    # Direção swell A
    'swell_a_energy': 13,       # Energia swell A
    'swell_a_power': 14,        # Potência swell A (dividir por 10)
    'swell_b_height': 15,       # Altura swell B (dividir por 10)
    'swell_b_period': 16,       # Período swell B (dividir por 10)
    'swell_b_direction': 17,    # Direção swell B
    'swell_b_energy': 18,       # Energia swell B
    'swell_b_power': 19,        # Potência swell B (dividir por 10)
    'sea_wind': 20,             # Vento marítimo
    'sea_wind_direction': 21,   # Direção do vento marítimo
    # Index 22 is unused
    'tides': 23,                # Dados de maré
}

# Beach-specific variables (from oceanos/praia{id}.json, prefixed with 's' instead of 'v')
BEACH_VARIABLES = {
    'wave_height': 0,           # Altura total
    'windseas_height': 1,       # Altura vagas
    'primary_swell_height': 2,  # Altura swell primário
    'secondary_swell_height': 3, # Altura swell secundário
}

# Atmospheric variables (from atmos/atmos{id}pro.json)
ATMOSPHERIC_VARIABLES = {
    'storm_potential': 3,       # Potencial de tempestade
    'pressure': 4,              # Pressão atmosférica
    'temperature': 5,           # Temperatura
    'clouds': 6,                # Nebulosidade
    'precipitation': 7,         # Precipitação
}

# Wind variables (subset of atmospheric, used for wind parsing)
WIND_VARIABLES = {
    'wind': 0,                  # Velocidade do vento
    'wind_direction': 1,        # Direção do vento em graus
    'wind_gust': 2,             # Rajadas de vento
    'pressure': 4,              # Pressão (duplicado para conveniência)
}

# Time hours for forecast (8 data points per day)
TIME_HOURS = [0, 3, 6, 9, 12, 15, 18, 21]

# Divisor for values that need to be divided by 10
DIVISOR_FACTOR = 10
