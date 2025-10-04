from models.loan_tables import LoanTables
from models.loan_metadata import LoanMetadata
from utils.status_utils import calculate_status
from utils.date_utils import calculate_days
from datetime import datetime
from dateutil.relativedelta import relativedelta

def safe_float(value):
    """Convert string to float, handling European decimal format"""
    if isinstance(value, str):
        return float(value.replace(',', '.'))
    return float(value or 0)


def _update_status_and_fees(current, outstanding_from_prev, last_status, consecutive_defaulted, payment_in_full, is_late, is_first_period):
    if consecutive_defaulted >= 2 or last_status == 'blocked':
        current['late_payment_fee'] = round((safe_float(current['installment']) + abs(outstanding_from_prev)) * 0.1, 2)
    elif outstanding_from_prev < 0 and (last_status == 'late' or last_status == 'default') and is_late:
        current['late_payment_fee'] = round((safe_float(current['installment']) + abs(outstanding_from_prev)) * 0.05, 2)
        current['consecutive_defaulted'] = int(consecutive_defaulted or 0) + 1
    elif outstanding_from_prev < 0 and last_status == 'late' and not is_late:
        if payment_in_full:
            current['late_payment_fee'] = 0.0
        else:
            current['late_payment_fee'] = round(abs(outstanding_from_prev) * 0.03, 2)
    elif (outstanding_from_prev >= 0 or is_first_period) and is_late:
        current['status'] = 'late'
        current['late_payment_fee'] = round((safe_float(current['installment']) + abs(outstanding_from_prev)) * 0.03, 2)
    return current

def create_extension_period(session, loan_id, current, consecutive_defaulted):
    """Create extension period for loans with outstanding balance at final period"""
    
    # Get loan metadata to calculate interest rate
    metadata = session.query(LoanMetadata).filter_by(loan_id=loan_id).first()
    
    # Create additional period for remaining balance
    next_period = current['period'] + 1
    next_due_date = current['due_date'] + relativedelta(months=1)
    
    outstanding_amount = abs(current['outstanding_balance'])
    # Calculate interest on outstanding balance (monthly rate)
    monthly_rate = safe_float(metadata.rate) / 12 / 100 if metadata else 0.02  # Default 2% monthly
    interest_amount = round(outstanding_amount * monthly_rate, 2)
    principal_amount = outstanding_amount
    total_installment = round(principal_amount + interest_amount, 2)
    
    new_row = LoanTables(
        loan_id=loan_id,
        period=next_period,
        due_date=next_due_date,
        installment=total_installment,
        principal=principal_amount,
        interest=interest_amount,
        service_fee=0.0,
        insurance_fee=0.0,
        late_payment_fee=0.0,
        payed_amount=0.0,
        outstanding_balance=-total_installment,
        status='pending',
        late_days=0,
        payment_date=None,
        consecutive_defaulted=consecutive_defaulted
    )
    session.add(new_row)


def calculate_period(**kwargs):
    outstanding_from_prev = safe_float(kwargs.get("outstanding_from_prev"))
    last_status = kwargs.get("last_status")
    payment = kwargs.get("payment")
    payment_date = kwargs.get("payment_date")
    consecutive_defaulted = int(kwargs.get("consecutive_defaulted") or 0)
    current = kwargs.get("current")
    session = kwargs.get("session")
    loan_id = kwargs.get("loan_id")

    print(f"incoming V2: {current}")

    is_first_period = kwargs.get('is_first_period')
    
    # Ensure due_date is a date object
    if isinstance(current['due_date'], str):
        current['due_date'] = datetime.strptime(current['due_date'], '%Y-%m-%d').date()
    
    is_late = payment_date > current['due_date']
    payment_in_full = abs(outstanding_from_prev or 0) < (safe_float(current['payed_amount']) + safe_float(payment))

    current = _update_status_and_fees(
        current, outstanding_from_prev, last_status, consecutive_defaulted, payment_in_full, is_late, is_first_period)

    total_due = round(safe_float(current['installment']) + (outstanding_from_prev * -1) + (current.get('late_payment_fee') or 0.0), 2)
    current['payed_amount'] = safe_float(current['payed_amount']) + safe_float(payment)
    current['calc_installment'] = round(total_due - safe_float(current['payed_amount']), 2) if current['payed_amount'] < total_due else 0
    current['outstanding_balance'] = round(current['payed_amount'] - total_due, 2)

    current['status'] = calculate_status(consecutive_defaulted, last_status, is_late, current['outstanding_balance'])

    current['late_days'] = calculate_days(current['due_date'], payment_date) if is_late else 0
    
    # Handle edge case: last period with outstanding balance
    if session and loan_id and current['outstanding_balance'] < 0:
        # Check if this is the last period
        from models.loan_tables import LoanTables
        max_period = session.query(LoanTables.period).filter_by(loan_id=loan_id).order_by(LoanTables.period.desc()).first()
        
        if max_period and current['period'] == max_period[0]:
            create_extension_period(session, loan_id, current, consecutive_defaulted)
    
    current['due_date'] = current['due_date'].isoformat()
    current['payment_date'] = payment_date.isoformat()
    return current
