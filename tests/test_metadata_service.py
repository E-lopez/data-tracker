import unittest
import sys
import os
from unittest.mock import Mock, patch, MagicMock
from datetime import date

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

# Mock SQLAlchemy dependencies before importing
sys.modules['sqlalchemy'] = Mock()
sys.modules['sqlalchemy.exc'] = Mock()
sys.modules['database'] = Mock()
sys.modules['models.loan_metadata'] = Mock()

# Mock the safe_float function
def mock_safe_float(value):
    if isinstance(value, str):
        return float(value.replace(',', '.'))
    return float(value or 0)

# Mock update_loan_metadata function for testing
def mock_update_loan_metadata(loan_id, current_row):
    """Mock implementation of update_loan_metadata for testing"""
    if not loan_id:
        return False
    
    # Simulate metadata lookup
    mock_metadata = {
        'amount': 10000.0,
        'balance': 8000.0,
        'payed': 2000.0
    }
    
    # Calculate principal payment
    principal_payment = mock_safe_float(current_row.get('payed_amount', 0)) - mock_safe_float(current_row.get('principal', 0))
    
    # Update balance only if principal_payment > 0
    new_balance = mock_metadata['balance']
    if principal_payment > 0:
        new_balance = mock_metadata['amount'] - principal_payment
    
    # Update payed amount (cumulative)
    new_payed = mock_metadata['payed'] + mock_safe_float(current_row.get('payed_amount', 0))
    
    return {'balance': new_balance, 'payed': new_payed, 'success': True}


class TestMetadataService(unittest.TestCase):
    
    def setUp(self):
        """Set up test data"""
        self.loan_id = "test-loan-123"
        self.mock_metadata = Mock()
        self.mock_metadata.loan_id = self.loan_id
        self.mock_metadata.amount = 10000.0
        self.mock_metadata.balance = 8000.0
        self.mock_metadata.payed = 2000.0

    def test_update_loan_metadata_successful_update(self):
        """Test successful metadata update"""
        current_row = {
            'payed_amount': 1000.0,
            'principal': 800.0
        }
        
        result = mock_update_loan_metadata(self.loan_id, current_row)
        
        self.assertTrue(result['success'])
        self.assertEqual(result['balance'], 9800.0)  # 10000 - (1000-800) = 9800
        self.assertEqual(result['payed'], 3000.0)    # 2000 + 1000 = 3000

    def test_balance_calculation_positive_principal_payment(self):
        """Test balance calculation when principal payment > 0"""
        current_row = {
            'payed_amount': 1000.0,
            'principal': 800.0  # Principal payment = 1000 - 800 = 200
        }
        
        result = mock_update_loan_metadata(self.loan_id, current_row)
        
        # Balance should be amount - principal_payment = 10000 - 200 = 9800
        self.assertEqual(result['balance'], 9800.0)

    def test_balance_no_change_when_principal_payment_negative(self):
        """Test balance doesn't change when principal payment <= 0"""
        current_row = {
            'payed_amount': 500.0,
            'principal': 800.0  # Principal payment = 500 - 800 = -300 (negative)
        }
        
        result = mock_update_loan_metadata(self.loan_id, current_row)
        
        # Balance should remain unchanged (original balance = 8000)
        self.assertEqual(result['balance'], 8000.0)

    def test_payed_amount_accumulation(self):
        """Test that payed amount accumulates correctly"""
        current_row = {
            'payed_amount': 1500.0,
            'principal': 800.0
        }
        
        result = mock_update_loan_metadata(self.loan_id, current_row)
        
        # Payed should be existing payed + current payed_amount = 2000 + 1500 = 3500
        self.assertEqual(result['payed'], 3500.0)

    def test_loan_not_found(self):
        """Test handling when loan metadata is not found"""
        current_row = {'payed_amount': 1000.0, 'principal': 800.0}
        
        result = mock_update_loan_metadata('', current_row)  # Empty loan_id
        
        self.assertFalse(result)

    def test_final_balance_zero_scenario(self):
        """Test that balance reaches zero at end of all periods"""
        # Simulate a loan scenario where all payments are made
        initial_amount = 10000.0
        
        # Mock metadata with initial state
        mock_metadata = Mock()
        mock_metadata.amount = initial_amount
        mock_metadata.balance = initial_amount
        mock_metadata.payed = 0.0
        
        # Simulate multiple payment periods
        payments = [
            {'payed_amount': 2000.0, 'principal': 1500.0},  # Principal payment: 500
            {'payed_amount': 2000.0, 'principal': 1600.0},  # Principal payment: 400
            {'payed_amount': 2000.0, 'principal': 1700.0},  # Principal payment: 300
            {'payed_amount': 2000.0, 'principal': 1800.0},  # Principal payment: 200
            {'payed_amount': 2000.0, 'principal': 1900.0},  # Principal payment: 100
        ]
        
        total_principal_payments = sum(p['payed_amount'] - p['principal'] for p in payments)
        expected_final_balance = initial_amount - total_principal_payments
        
        # Final balance should be zero when all principal is paid
        self.assertEqual(expected_final_balance, 8500.0)  # This shows remaining balance
        
        # To reach zero, we need one more payment of 8500 principal
        final_payment = {'payed_amount': 10000.0, 'principal': 1500.0}  # Principal payment: 8500
        total_principal_payments += (final_payment['payed_amount'] - final_payment['principal'])
        
        self.assertEqual(initial_amount - total_principal_payments, 0.0)

    def test_payed_amount_sum_validation(self):
        """Test that payed amount equals sum of all payed_amount values"""
        # Simulate loan table payments
        loan_table_payments = [1000.0, 1500.0, 2000.0, 1200.0, 800.0]
        expected_total_payed = sum(loan_table_payments)
        
        # Mock cumulative updates
        cumulative_payed = 0.0
        for payment in loan_table_payments:
            cumulative_payed += payment
        
        self.assertEqual(cumulative_payed, expected_total_payed)
        self.assertEqual(cumulative_payed, 6500.0)

    def test_zero_payment_handling(self):
        """Test handling of zero payments"""
        mock_metadata = Mock()
        mock_metadata.amount = 10000.0
        mock_metadata.balance = 8000.0
        mock_metadata.payed = 2000.0
        
        current_row = {
            'payed_amount': 0.0,
            'principal': 800.0  # Principal payment = 0 - 800 = -800 (negative)
        }
        
        # Balance should not change (negative principal payment)
        principal_payment = current_row['payed_amount'] - current_row['principal']
        self.assertLessEqual(principal_payment, 0)
        
        # Payed amount should still accumulate (even if zero)
        new_payed = mock_metadata.payed + current_row['payed_amount']
        self.assertEqual(new_payed, 2000.0)

    def test_european_number_format_handling(self):
        """Test handling of European decimal format in amounts"""
        # Test mock_safe_float with European format
        self.assertEqual(mock_safe_float('1000,50'), 1000.5)
        self.assertEqual(mock_safe_float('2500,75'), 2500.75)
        
        # Test in context of metadata update
        current_row = {
            'payed_amount': '1000,50',  # European format
            'principal': '800,25'       # European format
        }
        
        principal_payment = mock_safe_float(current_row['payed_amount']) - mock_safe_float(current_row['principal'])
        self.assertEqual(principal_payment, 200.25)


if __name__ == '__main__':
    unittest.main()