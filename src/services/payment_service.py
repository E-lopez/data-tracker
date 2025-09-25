from datetime import date
from dateutil.relativedelta import relativedelta

import logging
import sys
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import extract, func
from models.loan_tables import LoanTables
from models.loan_metadata import LoanMetadata
from database import get_db_session, close_db_session
from utils.amortization_utils import calculate_late_fee
from utils.date_utils import calculate_late_days, get_last_date_of_month

# Configure logging for Lambda
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stdout
)
logger = logging.getLogger(__name__)

def get_current_period():
    session = get_db_session()
    try:
        current_period = session.query(LoanMetadata).order_by(LoanMetadata.current_period.desc()).first()
        if current_period:
            return current_period.current_period
        return 0
    except SQLAlchemyError as e:
        logging.error(f"Error getting current period: {str(e)}")
        return 0
    finally:
        close_db_session(session)


def get_table_by_loan_id(loan_id):
    session = get_db_session()
    try:
        user_table = session.query(LoanTables).filter_by(loanId=loan_id).first()
        if user_table:
            return user_table.to_dict()
        return None
    except SQLAlchemyError as e:
        logger.error(f"Error getting user table: {str(e)}")
        return None
    finally:
        close_db_session(session)


def calculate_period(**kwargs):
    current = kwargs.get("current")
    print(f"Current Rows: {len(current)}")


def calculate_first_period(**kwargs):
    loan_metadata = kwargs.get("session").query(LoanMetadata).filter_by(loan_id=kwargs.get("loan_id")).first()
    current_balance = loan_metadata.balance if loan_metadata and loan_metadata.balance else 0

    print(f"Current Balance: {kwargs.get('current')['due_date']}, {current_balance}")

    current = kwargs.get("current")
    current['late_days'] = calculate_late_days(current['due_date'], kwargs.get("payment_date"))
    current['late_payment_fee'] = calculate_late_fee(current['late_days'], current_balance)
    current['calc_installment'] = current['late_payment_fee'] + current['interest'] + current['principal'] + current['service_fee'] + current['insurance_fee']
    current['outstanding_balance'] = float(kwargs.get("payment")) - current['calc_installment']
    
    current['status'] = 'default' if current['outstanding_balance'] <= 0 else 'payed'
    current['due_date'] = current['due_date'].isoformat()
    current['payment_date'] = kwargs.get("payment_date").isoformat()
    current['payed_amount'] = kwargs.get("payment")
    current['receipt_id'] = f"R-{kwargs.get('loan_id')}-{current['period']}"
    return current

def get_current_row(data):
    session = get_db_session()
    loan_id = data.get("loan_id")
    payment = data.get("installment", 0)
    payment_date = date.today()
    end_date = get_last_date_of_month(payment_date)
    start_date = end_date - relativedelta(months=2)


    print(f"Data: {data}")

    current = session.query(LoanTables).filter(
        LoanTables.loan_id == loan_id,
        LoanTables.due_date >= start_date,
        LoanTables.due_date <= end_date,
    ).order_by(LoanTables.due_date.asc()).limit(2).all()
    
    # Convert to dictionaries
    current = [row.to_dict() for row in current]

    is_first_period = True if len(current) == 1 else False

    if(is_first_period):
        return calculate_first_period(session=session, loan_id=loan_id, current=current[0], payment=payment, payment_date=payment_date)
    else:
        return calculate_period(session=session, loan_id=loan_id, current=current, payment=payment, payment_date=payment_date)


    # Convert SQLAlchemy objects to dictionaries
    result = []
    for curr in current:
        if curr:
            curr_dict = curr.to_dict()
            # Convert date to string for JSON serialization
            if curr_dict.get('due_date'):
                curr_dict['due_date'] = curr.due_date.isoformat()
            result.append(curr_dict)
    
    close_db_session(session)
    return result


def record_payment(data):
    # Placeholder for future implementation
    try:
        current_rows = get_current_row(data)
        print(f"Current Rows: {current_rows}")
        return current_rows if current_rows else {'message': 'No current row found'}
    except Exception as e:
        logger.error(f"Error recording payment: {str(e)}")
        return {'message': 'Error recording payment'}


# current_row.status = 'paid'
# current_row.payed_amount = data.get('payed_amount', current_row.payed_amount)
# current_row.payment_date = data.get('payment_date', current_row.payment_date)
# current_row.outstanding_balance = current_row.outstanding_balance - current_row.payed_amount
# current_row.late_days = data.get('late_days', 0)
# current_row.late_payment_fee = data.get('late_payment_fee', 0)
# current_row.receipt_id = data.get('receipt_id', current_row.receipt_id)

# session = get_db_session()
# session.add(current_row)
# session.commit()
# session.refresh(current_row)
# close_db_session(session)
# logger.info(f"Current row after update: {current_row.to_dict()}")
