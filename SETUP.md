# Setup Instructions

## Required GitHub Secrets

You need to add these secrets to your GitHub repository:

1. Go to: https://github.com/Surfuguru/forecast-api-lambda/settings/secrets/actions

2. Add these secrets:

**AWS Credentials:**
- `AWS_ACCESS_KEY_ID` - Your AWS access key
- `AWS_SECRET_ACCESS_KEY` - Your AWS secret key

**Database Credentials:**
- `FORECAST_API_MYSQL_HOST` - surf8.cioli53lpczj.us-east-1.rds.amazonaws.com
- `FORECAST_API_MYSQL_USER` - goforit
- `FORECAST_API_MYSQL_PASSWORD` - m-8Oq1Y$splZ?DE5i_r7
- `FORECAST_API_MYSQL_DATABASE` - surf10

## How to Add Secrets

1. Click "New repository secret"
2. Name: (e.g., `AWS_ACCESS_KEY_ID`)
3. Value: (paste the value)
4. Click "Add secret"

## Quick Add Commands

```bash
# From your local machine with AWS CLI configured
gh secret set AWS_ACCESS_KEY_ID --body "$(aws configure get aws_access_key_id)" --repo Surfuguru/forecast-api-lambda
gh secret set AWS_SECRET_ACCESS_KEY --body "$(aws configure get aws_secret_access_key)" --repo Surfuguru/forecast-api-lambda

# Database secrets
gh secret set FORECAST_API_MYSQL_HOST --body "surf8.cioli53lpczj.us-east-1.rds.amazonaws.com" --repo Surfuguru/forecast-api-lambda
gh secret set FORECAST_API_MYSQL_USER --body "goforit" --repo Surfuguru/forecast-api-lambda
gh secret set FORECAST_API_MYSQL_PASSWORD --body "m-8Oq1Y\$splZ?DE5i_r7" --repo Surfuguru/forecast-api-lambda
gh secret set FORECAST_API_MYSQL_DATABASE --body "surf10" --repo Surfuguru/forecast-api-lambda
```

After adding all secrets, push a commit to trigger the deployment!

## Manual Deployment (if needed)

```bash
# Build Lambda layer
mkdir -p layer/pymysql/python
pip install -r layer/pymysql/requirements.txt -t layer/pymysql/python

# Build and deploy
cd infrastructure
sam build
sam deploy --guided
```
