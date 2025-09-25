# Manual Deployment Guide

## Prerequisites

1. AWS CLI configured with appropriate permissions
2. Supabase PostgreSQL database setup
3. Database tables created (see README.md)

## Step-by-Step Deployment

### 1. Setup S3 Deployment Bucket
```bash
./setup-s3.sh data-tracker-deployment-bucket us-east-1
```

### 2. Set Doppler Secrets

Set your secrets in Doppler:

```bash
doppler secrets set DATABASE_URL="postgresql://postgres.khewnzogdzolwyflgazn:[YOUR-PASSWORD]@aws-0-us-east-1.pooler.supabase.com:6543/postgres"
doppler secrets set API_KEY="your-api-key"
```

### 3. Deploy Lambda Function
```bash
./deploy.sh dev data-tracker-deployment-bucket YOUR_DOPPLER_TOKEN
```

### 4. Test Deployment

Test the health endpoint:
```bash
curl https://YOUR_API_GATEWAY_URL/health
```

Expected response:
```json
{
  "status": "healthy",
  "service": "data-tracker"
}
```

## Security Best Practices

### Database Password Security
- ✅ **DO**: Use Doppler for secret management
- ✅ **DO**: Rotate passwords regularly
- ❌ **DON'T**: Hardcode passwords in code
- ❌ **DON'T**: Put passwords in environment variables

### SSL Configuration
- ✅ **DO**: Always use `sslmode=require`
- ✅ **DO**: Use Supabase's pooler (port 6543)
- ✅ **DO**: Verify SSL certificates

### Connection String Format
```
postgresql://postgres.khewnzogdzolwyflgazn:[YOUR-PASSWORD]@aws-0-us-east-1.pooler.supabase.com:6543/postgres?sslmode=require
```

## Troubleshooting

### Common Issues

1. **Doppler token invalid**
   - Verify token is correct: `doppler secrets --token YOUR_TOKEN`
   - Check project and config are correct

2. **Database connection failed**
   - Verify Supabase connection string
   - Check SSL configuration
   - Ensure tables exist

3. **Lambda timeout**
   - Check CloudWatch logs
   - Verify database connectivity
   - Consider increasing timeout

### Logs
View Lambda logs:
```bash
aws logs tail /aws/lambda/data-tracker-dev --follow
```

## Environment Variables

The Lambda function uses these environment variables (set via CloudFormation):

- `DATABASE_URL`: Retrieved from Doppler
- `SECRET_KEY`: Retrieved from Doppler
- `DOPPLER_TOKEN`: Doppler service token  
- `ENVIRONMENT`: Deployment environment (dev/staging/prod)

## API Testing
