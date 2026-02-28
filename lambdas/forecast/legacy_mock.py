"""
Mock legacy forecast endpoint
GET /forecast/mock
"""

import json
from common.responses import success

def lambda_handler(event, context):
    """
    Return mock forecast data
    """
    return success({
        "id": "id_da_praia",
        "date": "data da previsão gerada",
        "name": "Point de Itaúna",
        "forecast": {
            "wavesHeight": {
                "maxHeight": 3.5,
                "periods": [{"label": "1s", "color": "#FFFFFF"}],
                "totalHeight": [{
                    "day": "05/04/2022",
                    "label": "Ter 5",
                    "hours": [
                        {"hour": "00:00", "height": 1.5, "primaryDirection": "SSE", "degrees": 289, "period": 10},
                        {"hour": "03:00", "height": 1.4, "primaryDirection": "SSE", "degrees": 289, "period": 10},
                        {"hour": "06:00", "height": 1.2, "primaryDirection": "SSE", "degrees": 289, "period": 10},
                        {"hour": "09:00", "height": 1.1, "primaryDirection": "SSE", "degrees": 289, "period": 10}
                    ]
                }],
                "windseas": [],
                "swellA": [],
                "swellB": []
            }
        }
    })
