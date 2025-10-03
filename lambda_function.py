import json
import logging
import os
import sys
from typing import Dict, Any


print("[MODULE] lambda_function.py loading...")
sys.stdout.flush()

from config import Config
from database import init_db
from services.table_service import get_table_by_id, get_tables, save_table, get_metadata, get_metadata_by_user_id, get_loan_by_loan_id
from services.payment_service import record_payment, get_payment, end_of_month_update

# Configure logging for Lambda
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stdout,
    force=True
)
logger = logging.getLogger(__name__)

# Initialize database connection
db = init_db()

def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    AWS Lambda handler for data-tracker service
    """
    
    try:
        http_method = event.get('httpMethod') or event.get('requestContext', {}).get('http', {}).get('method', 'GET')
        path = event.get('path') or event.get('rawPath', '/')
        body = event.get('body')
        path_parameters = event.get('pathParameters') or {}
        headers = event.get('headers') or {}
        origin = headers.get('origin') or headers.get('Origin')

        request_data = {}
        if body:
            try:
                request_data = json.loads(body)
            except json.JSONDecodeError:
                return create_response(400, {'error': 'Invalid JSON in request body'}, origin)

        if http_method == 'OPTIONS':
            return create_response(200, {}, origin)

        return handle_route(http_method, path, path_parameters, request_data, origin)
    except Exception as e:
        return create_response(500, {'error': 'Internal server error'}, None)

def handle_route(http_method: str, path: str, path_parameters: Dict[str, Any], request_data: Dict[str, Any], origin: str) -> Dict[str, Any]:
    """Handles routing logic for lambda_handler"""
    if path in ['/health', '/']:
        return handle_health(origin)
    if path == '/get-tables' and http_method == 'GET':
        return handle_get_tables(origin)
    if path.startswith('/get-table-by-id') and http_method == 'GET':
        return handle_get_table_by_id(path, path_parameters, origin)
    if path == '/save-table' and http_method == 'POST':
        return handle_save_table(request_data, origin)
    if path == '/get-metadata' and http_method == 'GET':
        return handle_get_metadata(origin)
    if path.startswith('/get-metadata-by-id/') and http_method == 'GET':
        return handle_get_metadata_by_id(path, path_parameters, origin)
    if path.startswith('/get-loan-by-loan-id/') and http_method == 'GET':
        return handle_get_loan_by_loan_id(path, path_parameters, origin)
    if path == '/record-payment' and http_method == 'POST':
        return handle_record_payment(request_data, origin)
    if path.startswith('/get-payment') and http_method == 'GET':
        return handle_get_payment(path, path_parameters, origin)
    if path == '/end-of-month-update' and http_method == 'POST':
        return handle_end_of_month_update(origin)

    # Uncomment and implement these routes as needed
    # if path == '/save-metadata' and http_method == 'POST':
    #     result = save_metadata(request_data)
    #     return create_response(200, result, origin)

    # if path == '/record-payment' and http_method == 'POST':
    #     result = record_payment(request_data)
    #     return create_response(200, result, origin)

    logger.warning(f"No route found for {http_method} {path}")
    return create_response(404, {'error': f'Endpoint not found: {http_method} {path}'}, origin)

def handle_health(origin: str) -> Dict[str, Any]:
    return create_response(200, {'status': 'healthy', 'service': 'data-tracker'}, origin)

def handle_get_tables(origin: str) -> Dict[str, Any]:
    try:
        result = get_tables()
        return create_response(200, result, origin)
    except Exception as e:
        logger.error(f"Error logging tables: {str(e)}")
        return create_response(500, {'error': 'Internal server error'}, origin)

def handle_get_table_by_id(path: str, path_parameters: Dict[str, Any], origin: str) -> Dict[str, Any]:
    user_id = path_parameters.get('user_id') or path.split('/')[-1]
    result = get_table_by_id(user_id)
    if result is None:
        return create_response(404, {'error': f'Table not found for user_id: {user_id}'}, origin)
    return create_response(200, result, origin)

def handle_save_table(request_data: Dict[str, Any], origin: str) -> Dict[str, Any]:
    logger.info(f"Saving table with data: {request_data}")
    result = save_table(request_data)
    return create_response(200, result, origin)

def handle_get_metadata(origin: str) -> Dict[str, Any]:
    result = get_metadata()
    return create_response(200, result, origin)

def handle_get_metadata_by_id(path: str, path_parameters: Dict[str, Any], origin: str) -> Dict[str, Any]:
    user_id = path_parameters.get('user_id') or path.split('/')[-1]
    result, status_code = get_metadata_by_user_id(user_id)
    return create_response(status_code, result, origin)

def handle_get_loan_by_loan_id(path: str, path_parameters: Dict[str, Any], origin: str) -> Dict[str, Any]:
    loan_id = path_parameters.get('loan_id') or path.split('/')[-1]
    result, status_code = get_loan_by_loan_id(loan_id)
    return create_response(status_code, result, origin)

def handle_record_payment(request_data: Dict[str, Any], origin: str) -> Dict[str, Any]:
    result = record_payment(request_data)
    try:
        test = json.dumps(result)
        logger.info(f"Current row: {test}")
    except Exception as e:
        logger.error(f"Error logging current row: {str(e)}")
    return create_response(200, result, origin)

def handle_get_payment(path, path_parameters: Dict[str, Any], origin: str) -> Dict[str, Any]:
    loan_id = path_parameters.get('loan_id') or path.split('/')[-2]
    month_offset = path_parameters.get('month_offset') or path.split('/')[-1]
    print(f"Data: {path}, {loan_id}, {month_offset}")
    try:
        month_offset = int(month_offset) if month_offset.isdigit() else 0
        result = get_payment(loan_id, month_offset)
    except Exception as e:
        logger.error(f"Error processing payment request: {str(e)}")
        return create_response(500, {'error': 'Internal server error'}, origin)
    return create_response(200, result, origin)

def handle_end_of_month_update(origin: str) -> Dict[str, Any]:
    try:
        result = end_of_month_update()
        return create_response(200, result, origin)
    except Exception as e:
        logger.error(f"Error in end of month update: {str(e)}")
        return create_response(500, {'error': 'Internal server error'}, origin)

def create_response(status_code: int, body: Dict[str, Any], origin: str = None) -> Dict[str, Any]:
    """Create a properly formatted API Gateway response"""
    headers = {
        'Content-Type': 'application/json',
        'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
        'Access-Control-Allow-Headers': 'Content-Type, Authorization, Origin'
    }
    
    # Set CORS origin based on request origin
    if origin and origin in ['http://localhost:3000', 'http://localhost:5173', 'https://loan-client.onrender.com']:
        headers['Access-Control-Allow-Origin'] = origin
        headers['Access-Control-Allow-Credentials'] = 'true'
    
    return {
        'statusCode': status_code,
        'headers': headers,
        'body': json.dumps(body)
    }
    