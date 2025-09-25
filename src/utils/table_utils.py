import uuid
from datetime import datetime

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
        # Convert due_date string to date object
        if isinstance(row['due_date'], str):
            row['due_date'] = datetime.strptime(row['due_date'], '%Y-%m-%d').date()

    metadata['loan_id'] = loan_id
    metadata['installment'] = data[0]['installment'] if data else 0
    metadata['payed'] = 0
    metadata['balance'] = metadata['amount']
    metadata['defaulted_payments'] = 0
    metadata['defaulted_amount'] = 0
    # Use the already converted date objects from data array
    if data:
        metadata['start_date'] = data[0]['due_date']
        metadata['end_date'] = data[-1]['due_date']
    else:
        metadata['start_date'] = None
        metadata['end_date'] = None

    return data, metadata