from utils.status_utils import calculate_status
from utils.date_utils import calculate_days

def safe_float(value):
    """Convert string to float, handling European decimal format"""
    if isinstance(value, str):
        return float(value.replace(',', '.'))
    return float(value or 0)


def calculate_default_fee(last_status, outstanding_from_prev, last_payment_date, payment, payment_date):
    elapsed_days = calculate_days(last_payment_date, payment_date)
    if last_status == 'late' and elapsed_days <= 30:
        return 0.0
    

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


def calculate_period(**kwargs):
    from datetime import datetime
    outstanding_from_prev = safe_float(kwargs.get("outstanding_from_prev"))
    last_status = kwargs.get("last_status")
    payment = kwargs.get("payment")
    payment_date = kwargs.get("payment_date")
    consecutive_defaulted = int(kwargs.get("consecutive_defaulted") or 0)
    current = kwargs.get("current")

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
    current['due_date'] = current['due_date'].isoformat()
    current['payment_date'] = payment_date.isoformat()
    return current
