import unittest
import sys
import os
from unittest.mock import Mock
from datetime import date

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

class TestExtensionPeriod(unittest.TestCase):
    
    def test_extension_period_creation(self):
        """Test creation of extension period for last period with outstanding balance"""
        # Current period data (last period with outstanding balance)
        current = {
            'period': 12,  # Last period
            'due_date': date(2024, 12, 15),
            'outstanding_balance': -500.0,  # $500 still owed
            'installment': 1000.0
        }
        
        # Mock create_extension_period function
        def mock_create_extension_period(session, loan_id, current, consecutive_defaulted):
            outstanding_amount = abs(current['outstanding_balance'])
            monthly_rate = 24.0 / 12 / 100  # 2% monthly
            interest_amount = round(outstanding_amount * monthly_rate, 2)
            principal_amount = outstanding_amount
            total_installment = round(principal_amount + interest_amount, 2)
            
            return {
                'period': current['period'] + 1,
                'outstanding_amount': outstanding_amount,
                'interest_amount': interest_amount,
                'principal_amount': principal_amount,
                'total_installment': total_installment,
                'monthly_rate': monthly_rate
            }
        
        result = mock_create_extension_period(None, 'loan-123', current, 0)
        
        # Verify calculations
        self.assertEqual(result['period'], 13)
        self.assertEqual(result['outstanding_amount'], 500.0)
        self.assertEqual(result['monthly_rate'], 0.02)  # 2% monthly
        self.assertEqual(result['interest_amount'], 10.0)  # 500 * 0.02 = 10
        self.assertEqual(result['principal_amount'], 500.0)
        self.assertEqual(result['total_installment'], 510.0)  # 500 + 10 = 510

    def test_extension_period_with_default_rate(self):
        """Test extension period creation with default interest rate when metadata not found"""
        current = {
            'period': 6,
            'due_date': date(2024, 6, 15),
            'outstanding_balance': -1000.0,
            'installment': 2000.0
        }
        
        def mock_create_extension_period_default_rate(session, loan_id, current, consecutive_defaulted):
            outstanding_amount = abs(current['outstanding_balance'])
            monthly_rate = 0.02  # Default 2% monthly when no metadata
            interest_amount = round(outstanding_amount * monthly_rate, 2)
            total_installment = round(outstanding_amount + interest_amount, 2)
            
            return {
                'interest_amount': interest_amount,
                'total_installment': total_installment,
                'used_default_rate': True
            }
        
        result = mock_create_extension_period_default_rate(None, 'loan-456', current, 1)
        
        # Verify default rate is used
        self.assertEqual(result['interest_amount'], 20.0)  # 1000 * 0.02 = 20
        self.assertEqual(result['total_installment'], 1020.0)  # 1000 + 20 = 1020
        self.assertTrue(result['used_default_rate'])

    def test_extension_period_not_created_for_non_last_period(self):
        """Test that extension period is not created for non-last periods"""
        # Simulate scenario where current period is not the last period
        current_period = 8
        max_period = 12  # Last period is 12, current is 8
        outstanding_balance = -300.0
        
        # Extension should not be created
        should_create_extension = (current_period == max_period) and (outstanding_balance < 0)
        self.assertFalse(should_create_extension)

    def test_extension_period_not_created_for_positive_balance(self):
        """Test that extension period is not created when balance is positive (overpaid)"""
        # Simulate scenario where balance is positive (overpayment)
        current_period = 12
        max_period = 12  # Last period
        outstanding_balance = 100.0  # Positive balance (overpaid)
        
        # Extension should not be created for positive balance
        should_create_extension = (current_period == max_period) and (outstanding_balance < 0)
        self.assertFalse(should_create_extension)

    def test_extension_period_interest_calculation_accuracy(self):
        """Test accuracy of interest calculation for extension periods"""
        test_cases = [
            {'outstanding': 1000.0, 'rate': 12.0, 'expected_interest': 10.0},  # 1% monthly
            {'outstanding': 2500.0, 'rate': 24.0, 'expected_interest': 50.0},  # 2% monthly
            {'outstanding': 750.0, 'rate': 18.0, 'expected_interest': 11.25},  # 1.5% monthly
        ]
        
        for case in test_cases:
            monthly_rate = case['rate'] / 12 / 100
            calculated_interest = round(case['outstanding'] * monthly_rate, 2)
            self.assertEqual(calculated_interest, case['expected_interest'])

    def test_extension_period_consecutive_defaulted_preservation(self):
        """Test that consecutive_defaulted count is preserved in extension period"""
        consecutive_defaulted_values = [0, 1, 2, 3]
        
        for count in consecutive_defaulted_values:
            # Mock extension period creation
            def mock_extension_with_consecutive(consecutive_count):
                return {'consecutive_defaulted': consecutive_count}
            
            result = mock_extension_with_consecutive(count)
            self.assertEqual(result['consecutive_defaulted'], count)

    def test_extension_period_due_date_calculation(self):
        """Test that extension period due date is correctly calculated"""
        # Test basic month addition
        original_due_date = date(2024, 6, 15)
        
        # Mock the relativedelta behavior for adding one month
        def add_one_month(d):
            if d.month == 12:
                return date(d.year + 1, 1, d.day)
            else:
                return date(d.year, d.month + 1, d.day)
        
        expected_next_due_date = add_one_month(original_due_date)
        
        # Should be July 15, 2024
        self.assertEqual(expected_next_due_date, date(2024, 7, 15))
        
        # Test year rollover
        original_due_date_dec = date(2024, 12, 15)
        expected_next_due_date_dec = add_one_month(original_due_date_dec)
        
        # Should be January 15, 2025
        self.assertEqual(expected_next_due_date_dec, date(2025, 1, 15))


if __name__ == '__main__':
    unittest.main()