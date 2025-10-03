import unittest
import sys
import os
from datetime import date, timedelta

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from utils.amortization_utils import calculate_period
from utils.status_utils import calculate_status


class TestPaymentCalculations(unittest.TestCase):
    
    def setUp(self):
        """Set up test data"""
        self.base_current = {
            'installment': 1000.0,
            'payed_amount': 0.0,
            'due_date': '2024-01-15',
            'late_payment_fee': 0.0
        }
        self.payment_date_on_time = date(2024, 1, 15)
        self.payment_date_late = date(2024, 1, 20)

    def test_payment_not_late_outstanding_zero_or_positive_status_payed(self):
        """When payment is not late and outstanding >= 0, status should be payed"""
        result = calculate_period(
            current=self.base_current.copy(),
            payment=1000.0,
            payment_date=self.payment_date_on_time,
            outstanding_from_prev=0.0,
            last_status=None,
            consecutive_defaulted=0,
            is_first_period=True
        )
        self.assertEqual(result['status'], 'payed')
        self.assertEqual(result['outstanding_balance'], 0.0)

    def test_payment_late_outstanding_zero_or_positive_status_payed(self):
        """When payment is late and outstanding >= 0, status should be payed"""
        result = calculate_period(
            current=self.base_current.copy(),
            payment=1030.0,  # Payment covers installment + late fee (1000 + 30)
            payment_date=self.payment_date_late,
            outstanding_from_prev=0.0,
            last_status=None,
            consecutive_defaulted=0,
            is_first_period=True
        )
        self.assertGreaterEqual(result['outstanding_balance'], 0)
        self.assertEqual(result['status'], 'payed')

    def test_payment_late_outstanding_negative_status_late(self):
        """When payment is late and outstanding < 0, status should be late"""
        result = calculate_period(
            current=self.base_current.copy(),
            payment=500.0,
            payment_date=self.payment_date_late,
            outstanding_from_prev=0.0,
            last_status=None,
            consecutive_defaulted=0,
            is_first_period=True
        )
        self.assertEqual(result['status'], 'late')
        self.assertLess(result['outstanding_balance'], 0)

    def test_last_status_late_outstanding_negative_late_payment_status_default(self):
        """When last_status is late and outstanding < 0 and is_late, status should be default"""
        result = calculate_period(
            current=self.base_current.copy(),
            payment=500.0,
            payment_date=self.payment_date_late,
            outstanding_from_prev=-200.0,
            last_status='late',
            consecutive_defaulted=0,
            is_first_period=False
        )
        self.assertEqual(result['status'], 'default')

    def test_consecutive_defaulted_more_than_2_status_blocked(self):
        """When consecutive_defaulted > 2, status should be blocked"""
        result = calculate_period(
            current=self.base_current.copy(),
            payment=500.0,
            payment_date=self.payment_date_on_time,
            outstanding_from_prev=0.0,
            last_status=None,
            consecutive_defaulted=3,
            is_first_period=False
        )
        self.assertEqual(result['status'], 'blocked')

    def test_previous_status_blocked_status_blocked(self):
        """When previous status is blocked, status should be blocked"""
        result = calculate_period(
            current=self.base_current.copy(),
            payment=1000.0,
            payment_date=self.payment_date_on_time,
            outstanding_from_prev=0.0,
            last_status='blocked',
            consecutive_defaulted=0,
            is_first_period=False
        )
        self.assertEqual(result['status'], 'blocked')

    def test_outstanding_positive_calc_installment_subtracted(self):
        """When outstanding_from_prev > 0, calc_installment should have it subtracted"""
        result = calculate_period(
            current=self.base_current.copy(),
            payment=0.0,
            payment_date=self.payment_date_on_time,
            outstanding_from_prev=200.0,  # Overpayment from previous period
            last_status=None,
            consecutive_defaulted=0,
            is_first_period=False
        )
        # calc_installment should be 1000 - 200 = 800
        self.assertEqual(result['calc_installment'], 800.0)

    def test_outstanding_negative_calc_installment_added(self):
        """When outstanding_from_prev < 0, calc_installment should have it added"""
        result = calculate_period(
            current=self.base_current.copy(),
            payment=0.0,
            payment_date=self.payment_date_on_time,
            outstanding_from_prev=-200.0,  # Unpaid from previous period
            last_status=None,
            consecutive_defaulted=0,
            is_first_period=False
        )
        # calc_installment should be 1000 + 200 = 1200
        self.assertEqual(result['calc_installment'], 1200.0)

    def test_payment_less_than_calc_installment_not_late_status_pending(self):
        """When payment < calc_installment and not late, status should be pending"""
        result = calculate_period(
            current=self.base_current.copy(),
            payment=500.0,
            payment_date=self.payment_date_on_time,
            outstanding_from_prev=0.0,
            last_status=None,
            consecutive_defaulted=0,
            is_first_period=True
        )
        self.assertEqual(result['status'], 'pending')

    def test_payment_less_than_calc_installment_late_status_late(self):
        """When payment < calc_installment and is_late, status should be late"""
        result = calculate_period(
            current=self.base_current.copy(),
            payment=500.0,
            payment_date=self.payment_date_late,
            outstanding_from_prev=0.0,
            last_status=None,
            consecutive_defaulted=0,
            is_first_period=True
        )
        self.assertEqual(result['status'], 'late')

    def test_multiple_payments_same_period_payed_amount_accumulated(self):
        """When multiple payments for same period, payed_amount should be sum of payments"""
        # First payment
        current_with_payment = self.base_current.copy()
        current_with_payment['payed_amount'] = 300.0  # Previous payment
        
        result = calculate_period(
            current=current_with_payment,
            payment=700.0,  # Second payment
            payment_date=self.payment_date_on_time,
            outstanding_from_prev=0.0,
            last_status=None,
            consecutive_defaulted=0,
            is_first_period=True
        )
        # Total payed_amount should be 300 + 700 = 1000
        self.assertEqual(result['payed_amount'], 1000.0)

    def test_multiple_payments_outstanding_zero_or_positive_status_payed(self):
        """When multiple payments result in outstanding >= 0, status should be payed"""
        current_with_payment = self.base_current.copy()
        current_with_payment['payed_amount'] = 300.0
        
        result = calculate_period(
            current=current_with_payment,
            payment=700.0,
            payment_date=self.payment_date_on_time,
            outstanding_from_prev=0.0,
            last_status=None,
            consecutive_defaulted=0,
            is_first_period=True
        )
        self.assertEqual(result['status'], 'payed')
        self.assertEqual(result['outstanding_balance'], 0.0)

    def test_calculate_status_function_directly(self):
        """Test calculate_status function directly"""
        # Test payed status
        self.assertEqual(calculate_status(0, None, False, 0), 'payed')
        self.assertEqual(calculate_status(0, None, True, 100), 'payed')
        
        # Test late status
        self.assertEqual(calculate_status(0, None, True, -100), 'late')
        
        # Test default status
        self.assertEqual(calculate_status(0, 'late', True, -100), 'default')
        
        # Test blocked status
        self.assertEqual(calculate_status(3, None, False, -100), 'blocked')
        self.assertEqual(calculate_status(0, 'blocked', False, 0), 'blocked')
        
        # Test pending status
        self.assertEqual(calculate_status(0, None, False, -100), 'pending')

    def test_late_payment_fees_calculation(self):
        """Test that late payment fees are calculated correctly"""
        # Test blocked status fee (10%)
        result = calculate_period(
            current=self.base_current.copy(),
            payment=500.0,
            payment_date=self.payment_date_late,
            outstanding_from_prev=-200.0,
            last_status='blocked',
            consecutive_defaulted=3,
            is_first_period=False
        )
        expected_fee = (1000.0 + 200.0) * 0.1
        self.assertEqual(result['late_payment_fee'], expected_fee)

    def test_zero_payment_calculations(self):
        """Test calculations when payment is zero"""
        result = calculate_period(
            current=self.base_current.copy(),
            payment=0.0,
            payment_date=self.payment_date_late,
            outstanding_from_prev=0.0,
            last_status=None,
            consecutive_defaulted=0,
            is_first_period=True
        )
        self.assertEqual(result['payed_amount'], 0.0)
        # calc_installment should include late payment fee (3% of 1000 = 30)
        expected_calc_installment = 1000.0 + (1000.0 * 0.03)
        self.assertEqual(result['calc_installment'], expected_calc_installment)
        self.assertEqual(result['status'], 'late')

    def test_overpayment_scenario(self):
        """Test when payment exceeds calc_installment"""
        result = calculate_period(
            current=self.base_current.copy(),
            payment=1500.0,  # Overpayment
            payment_date=self.payment_date_on_time,
            outstanding_from_prev=0.0,
            last_status=None,
            consecutive_defaulted=0,
            is_first_period=True
        )
        self.assertEqual(result['outstanding_balance'], 500.0)  # Positive = overpaid
        self.assertEqual(result['status'], 'payed')
        self.assertEqual(result['calc_installment'], 0.0)  # Should be 0 when overpaid

    def test_european_number_format_safe_float(self):
        """Test safe_float handles European decimal format"""
        from utils.amortization_utils import safe_float
        self.assertEqual(safe_float('1000,50'), 1000.5)
        self.assertEqual(safe_float('2406072,29'), 2406072.29)
        self.assertEqual(safe_float(1000.5), 1000.5)
        self.assertEqual(safe_float(None), 0.0)

    def test_consecutive_defaulted_increment(self):
        """Test that consecutive_defaulted increments correctly"""
        result = calculate_period(
            current=self.base_current.copy(),
            payment=500.0,
            payment_date=self.payment_date_late,
            outstanding_from_prev=-200.0,
            last_status='late',
            consecutive_defaulted=1,
            is_first_period=False
        )
        self.assertEqual(result['consecutive_defaulted'], 2)
        self.assertEqual(result['status'], 'default')

    def test_late_days_calculation(self):
        """Test that late_days is calculated correctly"""
        result = calculate_period(
            current=self.base_current.copy(),
            payment=1000.0,
            payment_date=self.payment_date_late,  # 5 days late
            outstanding_from_prev=0.0,
            last_status=None,
            consecutive_defaulted=0,
            is_first_period=True
        )
        self.assertEqual(result['late_days'], 5)

    def test_payment_in_full_after_late_status(self):
        """Test payment in full after being late (should reset late fee)"""
        result = calculate_period(
            current=self.base_current.copy(),
            payment=1200.0,  # Full payment including outstanding
            payment_date=self.payment_date_on_time,
            outstanding_from_prev=-200.0,  # Was late previous period
            last_status='late',
            consecutive_defaulted=0,
            is_first_period=False
        )
        self.assertEqual(result['late_payment_fee'], 0.0)  # Should be reset
        self.assertEqual(result['status'], 'payed')

    def test_edge_case_exactly_calc_installment(self):
        """Test when payment exactly equals calc_installment"""
        result = calculate_period(
            current=self.base_current.copy(),
            payment=1000.0,
            payment_date=self.payment_date_on_time,
            outstanding_from_prev=0.0,
            last_status=None,
            consecutive_defaulted=0,
            is_first_period=True
        )
        self.assertEqual(result['outstanding_balance'], 0.0)
        self.assertEqual(result['calc_installment'], 0.0)
        self.assertEqual(result['status'], 'payed')


if __name__ == '__main__':
    unittest.main()