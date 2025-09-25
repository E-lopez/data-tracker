from sqlalchemy import Column, Integer, String, Numeric, Date
from database import Base

class LoanTables(Base):
    __tablename__ = 'loan_tables'
    
    nrow = Column(Integer, unique=True, autoincrement=True, primary_key=True)
    loan_id = Column(String(150), nullable=False)
    late_payment_fee = Column(Numeric, nullable=True)
    service_fee = Column(Numeric, nullable=False)
    insurance_fee = Column(Numeric, nullable=False)
    interest = Column(Numeric, nullable=False)
    principal = Column(Numeric, nullable=False)
    installment = Column(Numeric, nullable=False)
    calc_installment = Column(Numeric, nullable=True)
    period = Column(Numeric, nullable=False)
    due_date = Column(Date, nullable=False)
    payment_date = Column(Date, nullable=True)
    late_days = Column(Numeric, nullable=True)
    payed_amount = Column(Numeric, nullable=True)
    outstanding_balance = Column(Numeric, nullable=True)
    receipt_id = Column(String(150), nullable=True)
    status = Column(String(50), nullable=True)	

    def to_dict(self):
        return {
            'loan_id': self.loan_id,
            'late_payment_fee': float(self.late_payment_fee) if self.late_payment_fee is not None else None,
            'service_fee': float(self.service_fee),
            'insurance_fee': float(self.insurance_fee),
            'interest': float(self.interest),
            'principal': float(self.principal),
            'installment': float(self.installment),
            'calc_installment': float(self.calc_installment) if self.calc_installment is not None else None,
            'period': float(self.period),
            'due_date': self.due_date,
            'payment_date': self.payment_date,
            'late_days': float(self.late_days) if self.late_days is not None else None,
            'payed_amount': float(self.payed_amount) if self.payed_amount is not None else None,
            'outstanding_balance': float(self.outstanding_balance) if self.outstanding_balance is not None else None,
            'receipt_id': self.receipt_id,
            'status': self.status
        }
    