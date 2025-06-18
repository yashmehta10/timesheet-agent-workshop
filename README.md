# timesheet-agent-workshop

This repository contains the code for a timesheet management agent built using Google's Agent Development Kit (ADK). The agent is designed to interact with a user to record, retrieve, and manage their timesheet entries in a SQLite database.

## Overview

The primary goal of this project is to provide a conversational interface for employees to manage their timesheets. The agent proactively checks for missing entries, guides the user through logging time, and ensures data consistency according to predefined business rules (e.g., daily hour limits, valid hour increments).

## Features

*   **Conversational Timesheet Logging:** Users can describe their work, and the agent parses this information to create timesheet entries.
*   **Proactive Prompts:** The agent checks for recent workdays with potentially missing timesheet entries and prompts the user.
*   **Date Range Calculation:** Automatically determines relevant date ranges for timesheet summaries and prompts (e.g., the last 7 days).
*   **Active Assignment Checking:** Verifies that time is logged against active project assignments for the user.
*   **Timesheet Summaries:** Provides summaries of logged hours for specified periods.
*   **Input Validation:**
    *   Ensures hours are logged in valid increments (e.g., multiples of 1.9 hours).
    *   Enforces daily hour limits (e.g., 7.6 hours per day).
    *   Validates dates against workdays and active assignments.
*   **Keyword Interpretation:** Understands terms like "full day" (7.6 hours) and "half day" (3.8 hours).
*   **Database Interaction:** Uses SQLite to store and retrieve employee, project, assignment, and timesheet data.

## Technology Stack

*   **Python 3.x**
*   **Google Agent Development Kit (ADK):** For building the conversational agent (`google-adk`).
*   **SQLite:** As the backend database for storing timesheet information.
*   **Gemini AI Model:** (Specified as `gemini-2.0-flash` in the agent configuration) for powering the agent's conversational abilities.

## Project Structure

```
timesheet-agent-workshop/
├── .git/                     # Git repository files
├── .gitignore                # Specifies intentionally untracked files that Git should ignore
├── timesheet_agent/          # Main package for the timesheet agent
│   ├── __init__.py
│   ├── agent.py              # Core agent logic, instructions, and tool registration
│   ├── .env.local            # Local environment variables (template, ensure it's in .gitignore)
│   ├── database/             # Database related files
│   │   ├── timesheet.db      # SQLite database file (path configured via TIMESHEET_DB_PATH)
│   │   └── sql/              # SQL scripts
│   │       ├── timesheet_schema.sql # Database schema definition and sample data
│   │       └── read_data.sql      # Sample SQL queries for reading data
│   └── tools/                # Agent tools
│       ├── __init__.py
│       ├── database_tools.py # Tools for interacting with the timesheet database
│       └── datetime_tools.py # Tools for date and time operations
├── requirements.txt          # Python package dependencies
├── workshop.md               # Step-by-step setup guide
└── README.md                 # This file
```

## 🚀 Quick Start

For detailed setup and installation instructions, see the **[Workshop Guide](workshop.md)**.

The workshop includes:
- ✅ Prerequisites and authentication setup  
- ✅ Step-by-step installation for all platforms
- ✅ Environment configuration
- ✅ Database initialization
- ✅ Troubleshooting guide

### Quick Overview:
1. **Prerequisites:** Python 3.8+, Git, Google Cloud authentication
2. **Install:** Clone repo → Create venv → Install dependencies → Configure environment
3. **Run:** `adk web` → Access at `http://localhost:8000`

**👉 [Start with the Workshop Guide →](workshop.md)**

## Agent Functionality

The agent (`root_agent` in `agent.py`) is configured with detailed instructions to manage timesheets for a specific employee (ID "1"). Key aspects of its functionality include:

*   **Initial Interaction:**
    1.  Determines the current date and calculates a 7-day lookback period (identifying workdays).
    2.  Fetches active project assignments for the employee within this period.
    3.  Retrieves a summary of recently logged timesheet entries.
*   **Proactive Prompting:** If missing time is detected for active projects within the identified workdays, the agent proactively prompts the user to provide a breakdown of their hours.
*   **User Input Handling:**
    *   Parses user's description of hours worked on projects for specific dates.
    *   Interprets keywords like "full day" (7.6 hours) and "half day" (3.8 hours).
    *   Validates that provided dates fall within the prompted workdays.
    *   Maps project names to project IDs.
*   **Hour Constraints:**
    *   Ensures total daily hours do not exceed 7.6 hours (by default).
    *   Requires individual time entries to be in multiples of 1.9 hours.
*   **Confirmation:** Confirms logged entries with the user and provides a summary.
*   **Error Handling:** Clearly communicates tool errors or validation issues to the user.

## Agent Tools

The agent utilizes the following custom tools (defined in `timesheet_agent/tools/`):

*   **`get_today_date()` (from `datetime_tools.py`):**
    *   Returns the current date in YYYY-MM-DD format.
*   **`date_math(end_date, subtract_days, start_date, add_days)` (from `datetime_tools.py`):**
    *   Calculates a date period and returns the start date, end date, and a list of workdays (Mon-Fri) within that period.
*   **`get_assignment_metadata_for_employee(employee_id)` (from `database_tools.py`):**
    *   Retrieves assignment details (project name, start/end dates) for a given employee.
*   **`get_timesheet_summary_by_employee_and_date_range(employee_id, start_date_str, end_date_str)` (from `database_tools.py`):**
    *   Summarizes hours worked by an employee on each project within a date range.
*   **`insert_timesheet_entries(entries: List[Dict])` (from `database_tools.py`):**
    *   Inserts one or more timesheet entries into the database.
    *   Validates entries against active assignments for the given date.

## Database Schema

The SQLite database (`timesheet.db`) consists of the following main tables:

*   **`employees`**: Stores employee information.
    *   `employee_id` (PK), `first_name`, `last_name`, `email`
*   **`projects`**: Stores project information.
    *   `project_id` (PK), `project_name`
*   **`assignments`**: Links employees to projects with start and end dates for their assignment.
    *   `assignment_id` (PK), `employee_id` (FK), `project_id` (FK), `start_date`, `end_date`
*   **`timesheets`**: Stores the actual timesheet entries.
    *   `timesheet_id` (PK), `employee_id` (FK), `project_id` (FK), `date_worked`, `hours_worked`

Refer to `timesheet_agent/database/sql/timesheet_schema.sql` for detailed schema definitions, constraints, and sample data.

## Contributing

Contributions are welcome! Please feel free to submit pull requests or open issues for bugs, feature requests, or improvements.

When contributing, please ensure:
*   Code is well-formatted and includes comments where necessary.
*   New features or changes are covered by tests (if applicable).
*   The README is updated if changes affect setup, functionality, or dependencies.

---

## 📖 Documentation

- **[Workshop Guide](workshop.md)** - Complete setup and installation instructions