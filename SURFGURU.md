# SURFGURU API Documentation

## API Endpoints

### Base URL
**Always use:** `https://api.surfguru.pro`

**Do NOT use the raw AWS URL** (`https://xxx.execute-api.us-east-1.amazonaws.com/production`) - always use the CloudFront/custom domain.

## Endpoints

### Locations
- `GET /locations` - Get all locations in hierarchical tree structure
- `GET /geolocation/nearest-spots?lat={lat}&lon={lon}&range={km}` - Find nearest surf spots
- `GET /geolocation/search?q={query}` - Search locations by name

### Forecast
- `GET /forecast?praia_id={id}` - Get parsed forecast for a surf spot (SurfForecastResponse format)
- `GET /forecast/mock` - Get mock forecast data for testing

## Response Format (SurfForecastResponse)

```json
{
  "id": "1",
  "date": "2026-03-01",
  "type": "SURF",
  "name": "Maracaípe",
  "orientation": 92,
  "forecast": {
    "maxHeight": 1.5,
    "maxEnergy": 120,
    "maxPower": 15.8,
    "maxWind": 25,
    "days": [
      {
        "day": "2026-03-01",
        "hours": [
          {
            "hour": "00:00",
            "waves": {
              "totalHeight": { "value": 1.5, "period": 10, "direction": "SSE", ... },
              "windseas": { ... },
              "swellA": { ... },
              "swellB": { ... }
            },
            "winds": { "coast": { ... }, "sea": { ... } },
            "atmospheric": { "pressure": 1015, "temperature": 28, ... }
          }
        ],
        "tides": [...]
      }
    ]
  }
}
```

## Architecture

```
CloudFront (api.surfguru.pro)
    ↓
API Gateway
    ↓
Lambda Functions (Python 3.13)
    ├── RDS MySQL (location data)
    └── S3 (forecast data: atmospheric + oceanic)
```

## Deployment

- **CI:** Runs on every push/PR (lint, test, build)
- **CD:** Runs on push to master/main (SAM deploy to AWS)
- **Stack:** `forecast-api-live`
- **Region:** `us-east-1`

## Related Projects

- **Frontend:** `~/Documents/Code/surfguru` (Next.js)
- **Legacy API:** `~/Documents/Code/forecast-api` (Node.js - for reference)
