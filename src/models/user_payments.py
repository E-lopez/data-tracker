from sqlite3 import Date
from sqlalchemy import Column, Integer, String, Numeric
from database import Base

class UserPayments(Base):
    __tablename__ = 'user_loans'

    nrow = Column(Integer, unique=True, autoincrement=True, primary_key=True)
    user_id = Column(String(150), nullable=False)
    loan_id = Column(String(150), nullable=False)
    document_id = Column(String(150), nullable=False)
    payment_date = Column(Date, nullable=False)
    payed_amount = Column(Numeric, nullable=False)

    def to_dict(self):
        return {
            'user_id': self.user_id,
            'loan_id': self.loan_id,
            'document_id': self.document_id,
            'payment_date': self.payment_date,
            'payed_amount': float(self.payed_amount)
        }