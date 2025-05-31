import sqlite3
from typing import List, Dict, Optional, Any
import json
import os

# This path will be defined either via .env from ADK or Agent Engine or Cloud Run
DATABASE_FILE_PATH = os.environ.get('TIMESHEET_DB_PATH')
print(f"DEBUG: Attempting to use database at: {os.path.abspath(DATABASE_FILE_PATH)}")

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

    print("BEFORE INSERTION")
    print(get_timesheet_summary_by_employee_and_date_range(target_employee_id, "2025-05-31", "2025-05-31"))

    entries = [
        {"employee_id": 1, "project_id": 1, "date_worked": "2025-05-30", "hours_worked": 3.8}, # Assumes employee 1 and project 1 exist
        {"employee_id": 1, "project_id": 2, "date_worked": "2025-05-30", "hours_worked": 3.8}  # Assumes employee 1 and project 2 exist
    ]
    print("\n--- Inserting timesheet entries ---")
    insertion_result = insert_timesheet_entries(entries)
    print(insertion_result)

    print("AFTER INSERTION")
    print(get_timesheet_summary_by_employee_and_date_range(target_employee_id, "2025-05-31", "2025-05-31"))