from sqlalchemy import Column, Integer, String, Numeric, Date
from database import Base

class LoanMetadata(Base):
    __tablename__ = 'loan_metadata'

    nrow = Column(Integer, unique=True, autoincrement=True, primary_key=True)
    user_id = Column(String(150), nullable=False)
    loan_id = Column(String(150), nullable=False)
    amount = Column(Numeric, nullable=False)
    term = Column(Numeric, nullable=False)
    rate = Column(Numeric, nullable=False)
    installment = Column(Numeric, nullable=False)
    payed = Column(Numeric, nullable=False)
    balance = Column(Numeric, nullable=False)
    defaulted_payments = Column(Numeric, nullable=True)
    defaulted_amount = Column(Numeric, nullable=True)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    risk_distance = Column(Numeric, nullable=False)
    risk_score = Column(Numeric, nullable=False)
    risk_category = Column(String(50), nullable=False)
    closest_cluster = Column(Integer, nullable=False)
    user_risk = Column(Numeric, nullable=False)

    def to_dict(self):
        return {
            'user_id': self.user_id,
            'loan_id': self.loan_id,
            'amount': float(self.amount),
            'term': float(self.term),
            'rate': float(self.rate),
            'installment': float(self.instalment),
            'payed': float(self.payed),
            'balance': float(self.balance),
            'defaulted_payments': float(self.defaulted_payments) if self.defaulted_payments is not None else None,
            'defaulted_amount': float(self.defaulted_amount) if self.defaulted_amount is not None else None,
            'start_date': self.start_date,
            'end_date': self.end_date,
            'risk_distance': float(self.risk_distance),
            'risk_score': float(self.risk_score),
            'risk_category': self.risk_category,
            'closest_cluster': int(self.closest_cluster),
            'user_risk': float(self.user_risk)
        }