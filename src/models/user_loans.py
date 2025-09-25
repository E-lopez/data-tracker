from sqlalchemy import Column, Integer, String, Numeric
from database import Base

class UserLoans(Base):
    __tablename__ = 'user_loans'

    nrow = Column(Integer, unique=True, autoincrement=True, primary_key=True)
    user_id = Column(String(150), nullable=False)
    loan_id = Column(String(150), nullable=False)
    status = Column(String(50), nullable=False)

    def to_dict(self):
        return {
            'user_id': self.user_id,
            'loan_id': self.loan_id,
            'status': self.status
        }