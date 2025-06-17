import sqlite3
from typing import List, Dict, Optional, Any
import json
import os

# This path will be defined either via .env from ADK or Agent Engine or Cloud Run
DATABASE_FILE_PATH = os.environ.get('TIMESHEET_DB_PATH', '../database/timesheet.db')

def get_assignment_metadata_for_employee(employee_id: int) -> List[Dict[str, Any]]:
    """
    Reads assignment metadata from the SQLite database for a specific employee.
    (Function definition as previously established)
    """
    assignments_metadata: List[Dict[str, Any]] = []
    conn: Optional[sqlite3.Connection] = None
    db_path = DATABASE_FILE_PATH

    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        query = """
            SELECT
                a.assignment_id,
                e.first_name || ' ' || e.last_name AS employee_name,
                p.project_name,
                a.start_date,
                a.end_date
            FROM
                assignments a
            JOIN
                employees e ON a.employee_id = e.employee_id
            JOIN
                projects p ON a.project_id = p.project_id
            WHERE
                a.employee_id = ?
            ORDER BY
                a.start_date, p.project_name;
        """
        cursor.execute(query, (employee_id,))
        rows = cursor.fetchall()
        for row in rows:
            assignments_metadata.append(dict(row))
    except sqlite3.Error as e:
        error_message = f"A database error occurred: {e}"
        print(error_message)
        return [{
            "error": error_message,
            "details": "Failed to retrieve assignment metadata from the database."
        }]
    finally:
        if conn:
            conn.close()
    return assignments_metadata

def get_timesheet_summary_by_employee_and_date_range(employee_id: int, start_date_str: str, end_date_str: str) -> List[Dict[str, Any]]:
    """
    Retrieves a summary of hours worked by a specific employee on each project
    within a given date range.
    (Function definition as previously established)
    """
    summary_data: List[Dict[str, Any]] = []
    conn: Optional[sqlite3.Connection] = None
    db_path = DATABASE_FILE_PATH

    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        query = """
            SELECT
                e.first_name || ' ' || e.last_name AS employee_name,
                p.project_name,
                SUM(t.hours_worked) AS total_hours
            FROM
                timesheets t
            JOIN
                employees e ON t.employee_id = e.employee_id
            JOIN
                projects p ON t.project_id = p.project_id
            WHERE
                t.employee_id = ? AND
                t.date_worked BETWEEN ? AND ?
            GROUP BY
                p.project_id, p.project_name
            ORDER BY
                project_name;
        """
        cursor.execute(query, (employee_id, start_date_str, end_date_str))
        rows = cursor.fetchall()
        for row in rows:
            summary_data.append(dict(row))
    except sqlite3.Error as e:
        error_message = f"A database error occurred: {e}"
        print(error_message)
        return [{
            "error": error_message,
            "details": "Failed to retrieve timesheet summary for the employee from the database."
        }]
    finally:
        if conn:
            conn.close()
    return summary_data

def get_under_logged_workdays(employee_id: int, start_date_str: str, end_date_str: str, workdays_in_period: List[str], expected_hours_per_day: float = 7.6) -> Dict[str, Any]:
    """
    Identifies workdays within a given period where the total logged hours
    for an employee are less than expected_hours_per_day.

    Args:
        employee_id: The ID of the employee.
        start_date_str: The start date of the period (YYYY-MM-DD).
        end_date_str: The end date of the period (YYYY-MM-DD).
        workdays_in_period: A list of date strings (YYYY-MM-DD) representing
                            the actual workdays to check within the period.
        expected_hours_per_day: The minimum hours expected to be logged per workday.

    Returns:
        A dictionary containing:
        - "under_logged_dates": A list of date strings (YYYY-MM-DD) for workdays
                                with insufficient hours.
        - "checked_workdays_count": Number of workdays checked.
        - "status_message": A descriptive message.
    """
    daily_hours_map: Dict[str, float] = {}
    conn: Optional[sqlite3.Connection] = None
    db_path = DATABASE_FILE_PATH

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        query = """
            SELECT
                date_worked,
                SUM(hours_worked) AS total_hours_for_day
            FROM
                timesheets
            WHERE
                employee_id = ? AND
                date_worked BETWEEN ? AND ?
            GROUP BY
                date_worked;
        """
        cursor.execute(query, (employee_id, start_date_str, end_date_str))
        rows = cursor.fetchall()
        for row in rows:
            daily_hours_map[row[0]] = float(row[1])

    except sqlite3.Error as e:
        error_message = f"A database error occurred while checking daily logs: {e}"
        print(error_message)
        return {"error": error_message, "details": "Failed to retrieve daily timesheet data."}
    finally:
        if conn:
            conn.close()

    under_logged_dates = [
        day for day in workdays_in_period if daily_hours_map.get(day, 0.0) < expected_hours_per_day
    ]
    return {
        "under_logged_dates": under_logged_dates,
        "checked_workdays_count": len(workdays_in_period),
        "status_message": f"Checked {len(workdays_in_period)} workdays. Found {len(under_logged_dates)} under-logged."
    }

def _is_valid_assignment_for_date(cursor: sqlite3.Cursor, employee_id: int, project_id: int, date_worked: str) -> bool:
    """Helper function to check if a valid assignment exists for the given date."""
    query = """
        SELECT 1
        FROM assignments
        WHERE employee_id = ?
          AND project_id = ?
          AND start_date <= ?
          AND (end_date IS NULL OR end_date >= ?);
    """
    cursor.execute(query, (employee_id, project_id, date_worked, date_worked))
    return cursor.fetchone() is not None

def insert_timesheet_entries(entries: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Inserts one or more timesheet entries into the timesheets table.
    Validates that each entry's 'date_worked' falls within a valid assignment
    period for the employee and project.

    Args:
        entries: A list of dictionaries, where each dictionary represents a
                 timesheet entry and must contain the keys:
                 'employee_id' (int), 'project_id' (int),
                 'date_worked' (str, YYYY-MM-DD), and 'hours_worked' (float/int).

    Returns:
        A dictionary indicating the outcome.
        If any entry fails validation against assignment periods, the entire batch is rejected.
    """
    if not entries:
        return {
            "status": "no_action",
            "message": "No entries provided to insert.",
            "records_inserted": 0
        }

    conn: Optional[sqlite3.Connection] = None
    db_path = DATABASE_FILE_PATH
    
    # Prepare data for executemany and initial key validation
    data_to_insert = []
    required_keys = ['employee_id', 'project_id', 'date_worked', 'hours_worked']
    for i, entry in enumerate(entries):
        for key in required_keys:
            if key not in entry:
                return {
                    "status": "error",
                    "message": f"Missing key '{key}' in entry data at index {i}. Each entry must have 'employee_id', 'project_id', 'date_worked', 'hours_worked'.",
                    "records_inserted": 0
                }
        # Values will be extracted later if all validations pass
        
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("PRAGMA foreign_keys = ON;")

        # --- Assignment Validation Step ---
        for i, entry in enumerate(entries):
            if not _is_valid_assignment_for_date(cursor, entry['employee_id'], entry['project_id'], entry['date_worked']):
                return {
                    "status": "validation_error",
                    "message": f"Entry at index {i} (EmpID: {entry['employee_id']}, ProjID: {entry['project_id']}, Date: {entry['date_worked']}) "
                               f"is invalid: No active assignment found for this date or employee/project combination.",
                    "records_inserted": 0
                }
        
        # If all entries are validated against assignments, prepare for insertion
        for entry in entries:
             data_to_insert.append((
                entry['employee_id'],
                entry['project_id'],
                entry['date_worked'],
                entry['hours_worked']
            ))

        # --- Insertion Step ---
        sql = """
            INSERT INTO timesheets (employee_id, project_id, date_worked, hours_worked)
            VALUES (?, ?, ?, ?);
        """
        cursor.executemany(sql, data_to_insert)
        conn.commit()
        
        return {
            "status": "success",
            "records_inserted": len(data_to_insert),
            "message": f"Successfully inserted {len(data_to_insert)} timesheet entries."
        }

    except sqlite3.IntegrityError as e: # Handles FK violations, UNIQUE constraint, NOT NULL, CHECK
        if conn:
            conn.rollback() 
        error_message = f"Database integrity error during insert: {e}. This could be due to a non-existent employee/project ID, duplicate entry for the same day, or invalid hours."
        print(error_message)
        return {
            "status": "error",
            "message": error_message,
            "records_inserted": 0
        }
    except sqlite3.Error as e:
        if conn:
            conn.rollback()
        error_message = f"A general database error occurred: {e}"
        print(error_message)
        return {
            "status": "error",
            "message": error_message,
            "records_inserted": 0
        }
    finally:
        if conn:
            conn.close()

if __name__ == '__main__':
    target_employee_id = 1 # For Yash Mehta
    test_start_date = "2025-06-14"
    test_end_date = "2025-06-18"
    # Example workdays list, in a real scenario this comes from date_math
    test_workdays = ["2025-05-16", "2025-05-17", "2025-05-18"]

    print("Under-logged check:", get_under_logged_workdays(target_employee_id, test_start_date, test_end_date, test_workdays))