import logging
import sys
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import update
from models.loan_metadata import LoanMetadata
from database import get_db_session, close_db_session
from utils.amortization_utils import safe_float

# Configure logging for Lambda
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stdout
)
logger = logging.getLogger(__name__)

def update_loan_metadata(loan_id, current_row, session=None):
    """Update loan metadata with current period balance and payed amount"""
    should_close_session = session is None
    if session is None:
        session = get_db_session()
    try:
        # Get current metadata
        metadata = session.query(LoanMetadata).filter_by(loan_id=loan_id).first()
        if not metadata:
            logger.error(f"No metadata found for loan_id: {loan_id}")
            return False
        
        # Get principal payment from current row
        principal_payment = safe_float(current_row.get('principal', 0))
        
        # Update balance by reducing it by the principal payment
        new_balance = round(safe_float(metadata.balance) - principal_payment, 2)
        
        # Update payed amount (cumulative)
        new_payed = safe_float(metadata.payed) + safe_float(current_row.get('payed_amount', 0))
        
        # Update metadata
        stmt = update(LoanMetadata).where(LoanMetadata.loan_id == loan_id).values(
            balance=new_balance,
            payed=new_payed
        )
        session.execute(stmt)
        session.commit()
        
        logger.info(f"Updated metadata for loan {loan_id}: balance={new_balance}, payed={new_payed}")
        return True
        
    except SQLAlchemyError as e:
        session.rollback()
        logger.error(f"Error updating loan metadata: {str(e)}")
        return False
    finally:
        if should_close_session:
            close_db_session(session)