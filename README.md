# Score Handler Lambda

AWS Lambda function for handling user scoring and amortization calculations with Supabase PostgreSQL database.

## Features

- User survey registration and scoring
- Risk assessment calculations
- Amortization plan generation
- Repayment plan calculations
- Secure database connection with SSL

## Architecture

- **Runtime**: Python 3.11
- **Database**: Supabase PostgreSQL (with SSL)
- **Security**: Doppler for secrets management
- **Deployment**: CloudFormation + S3

## API Endpoints

- `GET /health` - Health check
- `POST /survey` - Register user survey and calculate scores
- `POST /repayment-plan` - Generate repayment plan
- `GET /repayment-plan/{user_id}` - Get user's amortization data

## Security Strategy

### Database Password Security
**Recommended approach**: Use Doppler

1. **Set secrets in Doppler**:
```bash
doppler secrets set DATABASE_URL="postgresql://postgres.khewnzogdzolwyflgazn:[YOUR-PASSWORD]@aws-0-us-east-1.pooler.supabase.com:6543/postgres"
doppler secrets set API_KEY="your-api-key"
```

2. **Lambda retrieves secrets at runtime** from Doppler API
3. **No hardcoded credentials** in code or environment variables

### SSL Connection
- **Always use SSL**: `sslmode=require` in connection string
- **Supabase enforces SSL** by default on pooler connections
- **Connection string format**: 
  ```
  postgresql://postgres.khewnzogdzolwyflgazn:[YOUR-PASSWORD]@aws-0-us-east-1.pooler.supabase.com:6543/postgres?sslmode=require
  ```

## Deployment

### 1. Setup S3 Bucket
```bash
./setup-s3.sh score-handler-deployment-bucket us-east-1
```

### 2. Set Doppler Secrets
```bash
doppler secrets set DATABASE_URL="postgresql://postgres.khewnzogdzolwyflgazn:[YOUR-PASSWORD]@aws-0-us-east-1.pooler.supabase.com:6543/postgres"
doppler secrets set API_KEY="your-api-key"
```

### 3. Deploy Lambda
```bash
./deploy.sh dev score-handler-deployment-bucket YOUR_DOPPLER_TOKEN
```

## Database Tables

The Lambda expects these PostgreSQL tables in Supabase:

```sql
-- User scoring data
CREATE TABLE user_score (
    nrow SERIAL PRIMARY KEY,
    "userId" VARCHAR(150) NOT NULL UNIQUE,
    demographics DECIMAL(10,6),
    "financialResponsibility" DECIMAL(10,6),
    "riskAversion" DECIMAL(10,6),
    impulsivity DECIMAL(10,6),
    "futureOrientation" DECIMAL(10,6),
    "financialKnowledge" DECIMAL(10,6),
    "locusOfControl" DECIMAL(10,6),
    "socialInfluence" DECIMAL(10,6),
    resilience DECIMAL(10,6),
    familismo DECIMAL(10,6),
    respect DECIMAL(10,6),
    risk_level DECIMAL(10,6)
);

-- User amortization data
CREATE TABLE user_amortization_data (
    nrow SERIAL PRIMARY KEY,
    "userId" VARCHAR(150) NOT NULL UNIQUE,
    "userRisk" DECIMAL(10,6),
    instalment DECIMAL(10,6),
    period DECIMAL(10,6),
    amount DECIMAL(10,6)
);
```

## Environment Variables

- `DATABASE_URL`: PostgreSQL connection string (retrieved from Doppler)
- `SECRET_KEY`: Application secret key (retrieved from Doppler)
- `DOPPLER_TOKEN`: Doppler service token
- `ENVIRONMENT`: Deployment environment (dev/staging/prod)

## Cost Optimization

- **Single connection pool**: Optimized for Lambda lifecycle
- **Connection recycling**: 5-minute timeout
- **Minimal memory**: 512MB allocation
- **Fast startup**: No heavy frameworks

## Monitoring

- CloudWatch logs for debugging
- Lambda metrics for performance
- Database connection monitoring via Supabase dashboard