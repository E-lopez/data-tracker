import logging
import sys
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import insert
from models.loan_tables import LoanTables
from models.loan_metadata import LoanMetadata
from database import get_db_session, close_db_session, DatabaseSession
from utils.table_utils import prepare_data, serialize_dates

# Configure logging for Lambda
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stdout
)
logger = logging.getLogger(__name__)

def get_tables():
    session = get_db_session()
    try:

        user_table = session.query(LoanTables).all()
        if user_table:
            return serialize_dates([serialize_dates(row.to_dict()) for row in user_table])
        return None
    except SQLAlchemyError as e:
        logger.error(f"Error getting tables: {str(e)}")
        return None
    finally:
        close_db_session(session)

def get_table_by_id(user_id):
    session = get_db_session()
    try:
        user_table = session.query(LoanTables).filter_by(userId=user_id).first()
        if user_table:
            return user_table.to_dict()
        return None
    except SQLAlchemyError as e:
        logger.error(f"Error getting user table: {str(e)}")
        return None
    finally:
        close_db_session(session)

def get_metadata():
    session = get_db_session()
    try:
        metadata = session.query(LoanMetadata).all()
        if metadata:
            return [m.to_dict() for m in metadata]
        return []
    except SQLAlchemyError as e:
        logger.error(f"Error getting metadata: {str(e)}")
        return []
    finally:
        close_db_session(session)

def get_metadata_by_user_id(user_id):
    session = get_db_session()
    try:
        metadata = session.query(LoanMetadata).filter_by(userId=user_id).all()
        if metadata:
            return [m.to_dict() for m in metadata]
        return []
    except SQLAlchemyError as e:
        logger.error(f"Error getting metadata: {str(e)}")
        return []
    finally:
        close_db_session(session)

def get_loan_by_loan_id(loan_id):
    session = get_db_session()
    try:
        loan = session.query(LoanTables).filter_by(loanId=loan_id).first()
        if loan:
            return loan.to_dict()
        return None
    except SQLAlchemyError as e:
        logger.error(f"Error getting loan by loan_id: {str(e)}")
        return None
    finally:
        close_db_session(session)

def save_table(data):    
    table_data, table_metadata = prepare_data(data)
    logger.info(f"Prepared {len(table_data)} rows and metadata")
    
    try:
        with DatabaseSession() as session:
            session.execute(insert(LoanTables), table_data) # Bulk insert        
            session.execute(insert(LoanMetadata), table_metadata) # single insert        
            return {"status": "Table saved successfully"}
    except Exception as e:
        logger.error(f"Error saving table: {str(e)}")
        return {'error': str(e)}
