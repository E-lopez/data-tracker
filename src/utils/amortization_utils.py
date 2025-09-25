def calculate_late_fee(late_days, balance, fee_rate = 0.015):
    if late_days <= 0 or balance <= 0:
        return 0
    return round((fee_rate / 100) * float(balance) * late_days, 2)