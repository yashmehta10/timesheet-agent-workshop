-- Enable foreign key constraints
PRAGMA foreign_keys = ON;

-- Drop tables if they exist to allow re-running the script
-- Order matters: drop tables with foreign keys first
DROP TABLE IF EXISTS timesheets;
DROP TABLE IF EXISTS assignments;
DROP TABLE IF EXISTS projects;
DROP TABLE IF EXISTS employees;

-- ############################################################################
-- ## EMPLOYEES TABLE (Simplified)                                           ##
-- ############################################################################
CREATE TABLE employees (
    employee_id INTEGER PRIMARY KEY AUTOINCREMENT,
    first_name TEXT NOT NULL,
    last_name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL -- Email should be unique for each employee
);

-- ############################################################################
-- ## PROJECTS TABLE (Simplified)                                            ##
-- ############################################################################
CREATE TABLE projects (
    project_id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_name TEXT NOT NULL UNIQUE -- Project name should be unique
);

-- ############################################################################
-- ## ASSIGNMENTS TABLE (Simplified - Link between Employees and Projects)   ##
-- ############################################################################
CREATE TABLE assignments (
    assignment_id INTEGER PRIMARY KEY AUTOINCREMENT,
    employee_id INTEGER NOT NULL,
    project_id INTEGER NOT NULL,
    start_date DATE NOT NULL, -- Date the assignment begins
    end_date DATE,            -- Date the assignment ends (can be NULL if ongoing)
    FOREIGN KEY (employee_id) REFERENCES employees(employee_id) ON DELETE RESTRICT, -- Prevent deleting employee if assignments exist
    FOREIGN KEY (project_id) REFERENCES projects(project_id) ON DELETE RESTRICT,   -- Prevent deleting project if assignments exist
    UNIQUE (employee_id, project_id, start_date), -- Prevents duplicate assignments for the same employee to the same project starting on the same day.
    CONSTRAINT chk_assignment_dates CHECK (end_date IS NULL OR start_date <= end_date) -- End date must be after or same as start date
);

-- ############################################################################
-- ## TIMESHEETS TABLE (Simplified)                                          ##
-- ############################################################################
CREATE TABLE timesheets (
    timesheet_id INTEGER PRIMARY KEY AUTOINCREMENT,
    employee_id INTEGER NOT NULL,   -- Who worked
    project_id INTEGER NOT NULL,    -- On which project
    date_worked DATE NOT NULL,      -- When the work was done
    hours_worked REAL NOT NULL,     -- How many hours
    FOREIGN KEY (employee_id) REFERENCES employees(employee_id) ON DELETE RESTRICT, -- Prevent deleting employee if timesheets exist
    FOREIGN KEY (project_id) REFERENCES projects(project_id) ON DELETE RESTRICT,   -- Prevent deleting project if timesheets exist
    CONSTRAINT chk_hours_worked CHECK (hours_worked > 0 AND hours_worked <= 24), -- Basic check for hours
    UNIQUE (employee_id, project_id, date_worked) -- Prevents an employee from logging time for the same project on the same day multiple times.
);

-- ############################################################################
-- ## SAMPLE DATA (Optional - for testing the simplified schema)             ##
-- ############################################################################

-- Sample Employees
INSERT INTO employees (first_name, last_name, email) VALUES
('Yash', 'Mehta', 'yash.mehta@vivanti.com');  -- employee_id will be 1

-- Sample Projects
INSERT INTO projects (project_name) VALUES
('Timesheet Database design'), -- project_id will be 1
('Timesheet interaction scripts'),   -- project_id will be 2
('ADK Agent Setup'),   -- project_id will be 3
('ADK Timesheet Agent');   -- project_id will be 4

-- Sample Assignments
INSERT INTO assignments (employee_id, project_id, start_date, end_date) VALUES
(1, 1, '2025-06-01', '2025-06-10'), -- Design Database (assignment_id 1)
(1, 2, '2025-06-11', '2025-06-13'), -- Design interaction scripts for the database (assignment_id 2)
(1, 3, '2025-06-14', '2025-06-15'), -- Setup ADK locally (assignment_id 3)
(1, 4, '2025-06-16', '2025-06-18'); -- Setup ADK Timesheet Agent (assignment_id 4)

-- Sample Timesheet Entries
-- (employee_id 1) on Timesheet Database design (project_id 1)
INSERT INTO timesheets (employee_id, project_id, date_worked, hours_worked) VALUES
(1, 1, '2025-06-01', 7.6),
(1, 1, '2025-06-02', 7.6);

-- (employee_id 1) on Timesheet interaction scripts (project_id 2)
INSERT INTO timesheets (employee_id, project_id, date_worked, hours_worked) VALUES
(1, 2, '2025-06-03', 7.6);

-- (employee_id 1) on ADK Setup (project_id 3)
INSERT INTO timesheets (employee_id, project_id, date_worked, hours_worked) VALUES
(1, 3, '2025-06-01', 7.6);

-- (employee_id 1) on ADK Agent (project_id 4)
INSERT INTO timesheets (employee_id, project_id, date_worked, hours_worked) VALUES
(1, 4, '2025-06-02', 7.6);

SELECT 'Database schema created successfully. Foreign keys enabled. Sample data inserted.';
