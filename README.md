# Forecast API - AWS Lambda

Serverless forecast API deployed to AWS Lambda with API Gateway.

## Architecture

- **Runtime:** Python 3.13
- **Framework:** AWS SAM (Serverless Application Model)
- **API:** API Gateway REST API
- **Database:** RDS MySQL (via VPC)
- **CI/CD:** GitHub Actions

## Endpoints

- `GET /health` - Health check
- `GET /locations` - Get all locations (hierarchical)
- `GET /geolocation/nearest-spots?lat=-22.9&long=-43.2&range=50` - Get beaches by geo
- `GET /geolocation/search?name=saquarema` - Search beaches by name
- `GET /forecast/mock` - Mock forecast data

## Local Development

```bash
# Install SAM CLI
brew install aws-sam-cli

# Install dependencies
pip install -r lambdas/requirements.txt

# Build
sam build

# Test locally
sam local start-api

# Invoke single function
sam local invoke HealthFunction
```

## Deployment

### Manual Deploy

```bash
# Deploy to production
sam deploy --guided

# Or use the deploy script
./deploy.sh production
```

### Automatic Deploy

Push to `main` branch - GitHub Actions will auto-deploy.

## Required Secrets

Add these to GitHub repository secrets:

- `AWS_ACCESS_KEY_ID`
- `AWS_SECRET_ACCESS_KEY`
- `FORECAST_API_MYSQL_HOST`
- `FORECAST_API_MYSQL_USER`
- `FORECAST_API_MYSQL_PASSWORD`
- `FORECAST_API_MYSQL_DATABASE`

## Infrastructure

See `infrastructure/template.yaml` for SAM template.

## Testing

```bash
# Run tests
pytest tests/ -v

# Lint CloudFormation
cfn-lint infrastructure/template.yaml
```

## Monitoring

- **CloudWatch Logs:** `/aws/lambda/forecast-api-*`
- **CloudWatch Metrics:** Lambda metrics in us-east-1

## Costs

Estimated $5-10/month for typical usage.

## License

MIT
