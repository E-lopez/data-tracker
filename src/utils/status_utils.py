def calculate_status(consecutive_defaulted, last_status, is_late, current_outstanding):
    if consecutive_defaulted >= 2 or last_status == 'blocked':
        return 'blocked'
    elif is_late and current_outstanding < 0 and (last_status == 'default' or last_status == 'late'):
        return 'default'
    elif is_late and current_outstanding < 0:
        return 'late'
    elif current_outstanding >= 0:
        return 'payed'
    else:
        return 'pending'