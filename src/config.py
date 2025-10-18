import os
import requests
import logging

logger = logging.getLogger(__name__)

def get_doppler_secret(key, default=None):
    """Get secret from Doppler API"""
    token = os.environ.get('DOPPLER_TOKEN')
    if not token:
        return default
    
    try:
        response = requests.get(
            'https://api.doppler.com/v3/configs/config/secrets/download',
            headers={'Authorization': f'Bearer {token}'},
            params={'format': 'json'}
        )
        response.raise_for_status()
        secrets = response.json()
        return secrets.get(key, default)
    except Exception as e:
        logger.error(f"Error getting Doppler secret {key}: {e}")
        return default

class Config:
    @property
    def SQLALCHEMY_DATABASE_URI(self):
        # Use local MySQL for development
        if os.environ.get('ENVIRONMENT') == 'local':
            return 'mysql+pymysql://root:%40r00t$usR@localhost:3306/loan_tracker'
        
        # Use Supabase PostgreSQL for production
        return get_doppler_secret('DATABASE_URL', 
            'postgresql://postgres.khewnzogdzolwyflgazn:[YOUR-PASSWORD]@aws-0-us-east-1.pooler.supabase.com:6543/postgres?sslmode=require'
        )
    
    @property
    def SECRET_KEY(self):
        return get_doppler_secret('API_KEY', 'dev-secret-key')
    
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    @property
    def SQLALCHEMY_ENGINE_OPTIONS(self):
        # Local MySQL settings
        if os.environ.get('ENVIRONMENT') == 'local':
            return {
                'pool_pre_ping': True,
                'pool_recycle': 3600,
                'pool_size': 5,
                'max_overflow': 10
            }
        
        # AWS Lambda + Supabase optimized settings
        return {
            'pool_pre_ping': True,
            'pool_recycle': 300,  # 5min for Lambda lifecycle
            'pool_size': 1,       # Single connection for Lambda
            'max_overflow': 0,    # No overflow in serverless
            'connect_args': {
                'connect_timeout': 10,
                'application_name': 'score_handler_lambda',
                'sslmode': 'require'  # Force SSL connection
            }
        }
    