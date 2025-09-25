from datetime import date
import calendar


def calculate_late_days(due_date, payment_date):
    if not due_date or not payment_date:
        return 0
    delta = (payment_date - due_date).days
    return max(0, delta)


def get_last_date_of_month(current_date=None):
    # Get the current date
    if current_date is None:
        current_date = date.today()

    # Get the year and month from the current date
    year = current_date.year
    month = current_date.month

    # Use calendar.monthrange to get the number of days in the month
    # monthrange returns a tuple: (weekday of first day, number of days in month)
    _, num_days = calendar.monthrange(year, month)

    # Create a date object for the last day of the month
    return date(year, month, num_days)