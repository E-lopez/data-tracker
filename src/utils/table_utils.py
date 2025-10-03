import uuid
from datetime import datetime, date

def safe_float(value):
    """Convert string to float, handling European decimal format"""
    if isinstance(value, str):
        return float(value.replace(',', '.'))
    return float(value or 0)

def prepare_data(data):   
    metadata = data['metadata']
    data = data['data'] 
    loan_id = uuid.uuid4().hex   
    for row in data:
        row.pop('balance', None)
        row['user_id'] = metadata["user_id"]
        row['late_payment_fee'] = 0
        row['payment_date'] = None
        row['late_days'] = 0
        row['loan_id'] = loan_id
        row['receipt_id'] = ''
        row['payed_amount'] = 0
        row['outstanding_balance'] = 0
        row['status'] = 'pending'
        # Convert numeric fields to proper format
        for field in ['service_fee', 'insurance_fee', 'interest', 'principal', 'installment', 'period']:
            if field in row:
                row[field] = safe_float(row[field])
        # Convert due_date string to date object
        if isinstance(row['due_date'], str):
            row['due_date'] = datetime.strptime(row['due_date'], '%Y-%m-%d').date()

    metadata['loan_id'] = loan_id
    metadata['installment'] = safe_float(data[0]['installment']) if data else 0
    metadata['payed'] = 0
    metadata['balance'] = safe_float(metadata['amount'])
    metadata['defaulted_payments'] = 0
    metadata['defaulted_amount'] = 0
    # Convert other numeric fields
    for field in ['amount', 'term', 'rate', 'risk_distance', 'risk_score', 'user_risk']:
        if field in metadata:
            metadata[field] = safe_float(metadata[field])
    # Use the already converted date objects from data array
    if data:
        metadata['start_date'] = data[0]['due_date']
        metadata['end_date'] = data[-1]['due_date']
    else:
        metadata['start_date'] = None
        metadata['end_date'] = None

    return data, metadata

def serialize_dates(obj):
    """Convert date objects to ISO format strings for JSON serialization"""
    if isinstance(obj, dict):
        return {key: serialize_dates(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [serialize_dates(item) for item in obj]
    elif isinstance(obj, date):
        return obj.isoformat()
    return obj