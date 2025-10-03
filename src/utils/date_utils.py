from datetime import date
import calendar


def calculate_days(initial_date, final_date):
    if not initial_date or not final_date:
        return 0
    delta = (final_date - initial_date).days
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
    