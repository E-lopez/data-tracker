from datetime import date
from dateutil.relativedelta import relativedelta

import logging
import sys
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import update
from models.loan_tables import LoanTables
from models.loan_metadata import LoanMetadata
from models.user_payments import UserPayments
from database import get_db_session, close_db_session
from utils.amortization_utils import calculate_period, safe_float
from utils.date_utils import get_last_date_of_month
from services.metadata_service import update_loan_metadata

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


def calculate_current_row(session, data):
    loan_id = data.get("loan_id")
    payment = safe_float(data.get("installment", 0))
    payment_date = date.today() + relativedelta(months=data.get("month_offset") or 0, days=20)
    end_date = get_last_date_of_month(payment_date)
    start_date = end_date - relativedelta(months=2)



    current = session.query(LoanTables).filter(
        LoanTables.loan_id == loan_id,
        LoanTables.due_date >= start_date,
        LoanTables.due_date <= end_date,
    ).order_by(LoanTables.due_date.asc()).limit(2).all()
    
    # Convert to dictionaries
    current_editable = [row.to_dict() for row in current]

    # Check if current list is empty
    if not current_editable:
        close_db_session(session)
        return {'message': 'No current row found'}

    is_first_period = True if len(current_editable) == 1 else False
    outstanding_from_prev = 0.0 if is_first_period else safe_float(current_editable[0]['outstanding_balance'])
    last_status = None if is_first_period else current_editable[0]['status']
    consecutive_defaulted = 0 if is_first_period else current_editable[0].get('consecutive_defaulted', 0)
    # Select the appropriate current row
    current_row = current_editable[0] if is_first_period else current_editable[1]

    res = calculate_period(
        session=session, 
        loan_id=loan_id,
        current=current_row, 
        payment=payment, 
        payment_date=payment_date, 
        outstanding_from_prev=outstanding_from_prev, 
        last_status=last_status,
        consecutive_defaulted=consecutive_defaulted,
        is_first_period=is_first_period
    )

    # Update loan metadata
    update_loan_metadata(loan_id, res, session)

    return {'row': res, 'period': current_row['period']}


def record_payment(data):
    try:
        session = get_db_session()
        loan_id = data.get("loan_id")
        current_row = calculate_current_row(session, data)
        
        # Update loan tables
        stmt = update(LoanTables).where(LoanTables.loan_id == loan_id).where(LoanTables.period == current_row['period']).values(**current_row['row'])
        session.execute(stmt)
        
        # Register payment in user_payments table
        user_payment = UserPayments(
            user_id=data.get('user_id', ''),
            loan_id=loan_id,
            document_id=data.get('document_id', ''),
            payment_date=current_row['row']['payment_date'],
            payed_amount=safe_float(data.get('installment', 0))
        )
        session.add(user_payment)
        
        session.commit()
        close_db_session(session)
        return current_row['row'] if current_row else {'message': 'No current row found'}
    except Exception as e:
        logger.error(f"Error recording payment: {str(e)}")
        return {'message': 'Error recording payment'}


def end_of_month_update():
    from datetime import date
    import calendar
    
    # Check if today is the last day of the month
    today = date.today()
    last_day = calendar.monthrange(today.year, today.month)[1]
    if today.day != last_day:
        return {'message': 'Not the last day of the month', 'updated_loans': 0}
    
    session = get_db_session()
    try:
        # Get all loan metadata
        loan_metadata = session.query(LoanMetadata).all()
        updated_count = 0
        
        for metadata in loan_metadata:
            try:
                # Send 0 payment for each loan
                data = {'loan_id': metadata.loan_id, 'installment': 0, 'month_offset': 0}
                calculate_current_row(session, data)
                updated_count += 1
            except Exception as e:
                logger.error(f"Error updating loan {metadata.loan_id}: {str(e)}")
                continue
        
        session.commit()
        return {'message': 'End of month update completed', 'updated_loans': updated_count}
    except Exception as e:
        session.rollback()
        logger.error(f"Error in end_of_month_update: {str(e)}")
        return {'message': 'Error in end of month update', 'updated_loans': 0}
    finally:
        close_db_session(session)

## The following functions are placeholders for future implementation
def get_payment(loan_id, month_offset):
    session = get_db_session()
    data = {'loan_id': loan_id, 'month_offset': month_offset or 0}
    current_row = calculate_current_row(session, data)
    close_db_session(session)
    return current_row if current_row else {'message': 'No current row found'}
 