import datetime
from typing import Dict, List, Optional, Union

def get_today_date() -> Dict[str, str]:
    """Returns the current date in YYYY-MM-DD format."""
    return {"date": datetime.date.today().isoformat()}

def date_math(
    end_date: Optional[str] = None,
    subtract_days: Optional[int] = None,
    start_date: Optional[str] = None,
    add_days: Optional[int] = None
) -> Dict[str, Union[str, List[str], None]]:
    """
    Calculates a date period and returns the original start and end dates
    of that period, along with a list of all workdays (Monday-Friday) within it.

    Exactly one of (end_date AND subtract_days) OR (start_date AND add_days)
    must be provided to define the period.

    Args:
        end_date: The end date of the period (YYYY-MM-DD). Used with subtract_days.
        subtract_days: Number of days to subtract from end_date to find the start.
        start_date: The start date of the period (YYYY-MM-DD). Used with add_days.
        add_days: Number of days to add to start_date to find the end.

    Returns:
        A dictionary containing:
        - "original_start_date": The calculated start date of the full period.
        - "original_end_date": The calculated end date of the full period.
        - "workdays": A list of date strings (YYYY-MM-DD) for workdays (M-F)
                      within the original_start_date and original_end_date, inclusive.
        Returns an error dictionary if inputs are invalid.
    """
    base_date_obj: Optional[datetime.date] = None
    period_start_date: Optional[datetime.date] = None
    period_end_date: Optional[datetime.date] = None

    try:
        if end_date is not None and subtract_days is not None:
            if start_date is not None or add_days is not None:
                return {"error": "Provide either (end_date and subtract_days) OR (start_date and add_days), not both."}
            base_date_obj = datetime.date.fromisoformat(end_date)
            period_end_date = base_date_obj
            period_start_date = base_date_obj - datetime.timedelta(days=subtract_days)
        elif start_date is not None and add_days is not None:
            base_date_obj = datetime.date.fromisoformat(start_date)
            period_start_date = base_date_obj
            period_end_date = base_date_obj + datetime.timedelta(days=add_days)
        else:
            return {"error": "Invalid parameters. Provide (end_date and subtract_days) OR (start_date and add_days)."}

        if period_start_date > period_end_date:
             # Swap if subtract_days was negative or add_days was negative leading to inverted range
            period_start_date, period_end_date = period_end_date, period_start_date

        workdays_list: List[str] = []
        current_date = period_start_date
        while current_date <= period_end_date:
            if current_date.weekday() < 5: # Monday is 0, Friday is 4
                workdays_list.append(current_date.isoformat())
            current_date += datetime.timedelta(days=1)

        return {
            "original_start_date": period_start_date.isoformat(),
            "original_end_date": period_end_date.isoformat(),
            "workdays": workdays_list
        }
    except ValueError as e: # Handles invalid date format
        return {"error": f"Invalid date format provided: {e}"}
    except TypeError as e: # Handles issues with None for days if logic is flawed
        return {"error": f"Type error in date calculation, check parameters: {e}"}

if __name__ == '__main__':
    print("--- Testing datetime_tools.py ---")
    today = get_today_date()["date"]
    print(f"Today's Date: {today}")

    # Test case 1: Last 6 days ending today (to get a 7-day period)
    print("\nTest Case 1: 7-day period ending today (subtract 6 days)")
    result1 = date_math(end_date=today, subtract_days=6)
    print(result1['workdays'])