#!/bin/bash

set -e

# Configuration
ENVIRONMENT=${1:-dev}
S3_BUCKET=${2:-data-tracker-deployment-bucket}
STACK_NAME="data-tracker-${ENVIRONMENT}"
AWS_REGION="us-east-1"
DOPPLER_TOKEN=${3:-""}

echo "Deploying Data Tracker Lambda for environment: $ENVIRONMENT"
echo "S3 Bucket: $S3_BUCKET"
echo "Stack Name: $STACK_NAME"
echo "Region: $AWS_REGION"

# Create deployment package
echo "Creating deployment package..."
rm -rf package/
mkdir -p package/

# Install dependencies with proper wheels for Lambda
echo "Installing dependencies..."

# Install all dependencies with compatible wheels for arm64 Lambda
python3 -m pip install \
--platform manylinux2014_aarch64 \
--target=package \
--implementation cp \
--python-version 3.13 \
--only-binary=:all: --upgrade \
numpy pandas numpy-financial psycopg2-binary sqlalchemy requests

# Copy source code
echo "Copying source code..."
cp -r src/ package/
cp lambda_function.py package/

# Create ZIP file
echo "Creating ZIP file..."
cd package
zip -r ../function.zip . -x "*.pyc" "*__pycache__*"
cd ..

# Upload to S3
echo "Uploading to S3..."
aws s3 cp function.zip s3://${S3_BUCKET}/data-tracker/function.zip

# Deploy CloudFormation stack
echo "Deploying CloudFormation stack..."
aws cloudformation deploy \
    --template-file cloudformation-template.yaml \
    --stack-name ${STACK_NAME} \
    --parameter-overrides \
        Environment=${ENVIRONMENT} \
        S3Bucket=${S3_BUCKET} \
        S3Key=data-tracker/function.zip \
        DopplerToken=${DOPPLER_TOKEN} \
    --capabilities CAPABILITY_IAM \
    --region ${AWS_REGION}

# Get stack outputs
echo "Getting stack outputs..."
API_URL=$(aws cloudformation describe-stacks \
    --stack-name ${STACK_NAME} \
    --query 'Stacks[0].Outputs[?OutputKey==`ApiUrl`].OutputValue' \
    --output text \
    --region ${AWS_REGION})

FUNCTION_ARN=$(aws cloudformation describe-stacks \
    --stack-name ${STACK_NAME} \
    --query 'Stacks[0].Outputs[?OutputKey==`DataTrackerFunctionArn`].OutputValue' \
    --output text \
    --region ${AWS_REGION})

echo ""
echo "Deployment completed successfully!"
echo "Environment: $ENVIRONMENT"
echo "Function ARN: $FUNCTION_ARN"
echo ""
echo "API Endpoints:"
echo "  Health Check:        GET  ${API_URL}health" 
echo "  Save Table Data:     POST ${API_URL}table"
echo "  Get Table Data:      GET  ${API_URL}table/{userId}"
echo "  Delete Table Data:   DELETE ${API_URL}table/{userId}"
echo "  Generate Amortization Schedule: POST ${API_URL}amortization"
echo ""
echo "Clean up..."
rm -rf package/
rm function.zip