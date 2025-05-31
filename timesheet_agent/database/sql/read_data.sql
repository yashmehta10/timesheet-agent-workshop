.headers on
.mode table

-- ############################################################################
-- ## READ DATA FROM EMPLOYEES TABLE                                         ##
-- ############################################################################
SELECT
    employee_id,
    first_name,
    last_name,
    email
FROM
    employees;


-- ############################################################################
-- ## READ DATA FROM PROJECTS TABLE                                          ##
-- ############################################################################
SELECT
    project_id,
    project_name
FROM
    projects;


-- ############################################################################
-- ## READ DATA FROM ASSIGNMENTS TABLE                                       ##
-- ############################################################################
SELECT
    assignment_id,
    employee_id,
    project_id,
    start_date,
    end_date
FROM
    assignments;


-- ############################################################################
-- ## READ DATA FROM TIMESHEETS TABLE                                        ##
-- ############################################################################
SELECT
    timesheet_id,
    employee_id,
    project_id,
    date_worked,
    hours_worked
FROM
    timesheets;


-- Example of a more detailed query joining tables to get meaningful timesheet information
/*
SELECT '--- Reading combined timesheet report (JOINED DATA) ---' AS Report_Information;
SELECT
    t.timesheet_id,
    e.first_name || ' ' || e.last_name AS employee_name,
    p.project_name,
    t.date_worked,
    t.hours_worked
FROM
    timesheets t
JOIN
    employees e ON t.employee_id = e.employee_id
JOIN
    projects p ON t.project_id = p.project_id
ORDER BY
    e.last_name, e.first_name, p.project_name, t.date_worked;
*/