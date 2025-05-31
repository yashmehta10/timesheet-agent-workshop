import datetime
from google.adk.agents import LlmAgent, SequentialAgent # Changed import

# Assuming these are in a 'tools' subdirectory relative to where this agent file is.
# The actual import paths might need adjustment based on your project structure.
from .tools.database_tools import get_assignment_metadata_for_employee, get_timesheet_summary_by_employee_and_date_range, insert_timesheet_entries
from .tools.datetime_tools import get_today_date, date_math

USER_ID="1" # This specific User ID will be used by the agents.

# --- Sub-agents for Initialization Workflow ---

get_date_sub_agent = LlmAgent(
    name="GetDateSubAgent",
    model="gemini-2.0-flash",
    description=(
        "Calls the `get_today_date` tool and outputs its result to the state."
    ),
    instruction=(
        "Your task is to call the `get_today_date` tool. "
        "You MUST output *only* the direct JSON result from the tool call. "
        "Do not add any other text, explanation, or formatting."
    ),
    tools=[get_today_date],
    output_key="today_date_tool_result"
)

calculate_date_range_sub_agent = LlmAgent(
    name="CalculateDateRangeSubAgent",
    model="gemini-2.0-flash",
    description=(
        "Uses the date from state (today_date_tool_result) to call `date_math` "
        "and outputs its result to the state."
    ),
    instruction="""
    You will receive `today_date_tool_result` in the state, which is the output from the `get_today_date` tool.
    1. Check if `today_date_tool_result` exists and contains a 'date' key.
       If not, or if `today_date_tool_result` itself indicates an error (e.g., has an 'error' key),
       you MUST output an error structure: {"error": "Invalid or missing today_date_tool_result from state", "details": "Could not retrieve valid date from previous step."}
    2. If valid, extract the date string (e.g., "YYYY-MM-DD") from `state['today_date_tool_result']['date']`.
    3. Call the `date_math` tool with `end_date` set to this extracted date and `subtract_days=6`.
    4. You MUST output *only* the direct JSON result from the `date_math` tool call.
       Do not add any other text, explanation, or formatting.
    """,
    tools=[date_math],
    output_key="date_info_tool_result"
)

fetch_assignments_sub_agent = LlmAgent(
    name="FetchAssignmentsSubAgent",
    model="gemini-2.0-flash",
    description=(
        f"Calls `get_assignment_metadata_for_employee` for employee ID '{USER_ID}' "
        "and outputs its result to the state."
    ),
    instruction=(
        f"Your task is to call the `get_assignment_metadata_for_employee` tool with `employee_id='{USER_ID}'`. "
        "You MUST output *only* the direct JSON result from the tool call. "
        "Do not add any other text, explanation, or formatting."
    ),
    tools=[get_assignment_metadata_for_employee],
    output_key="assignments_tool_result"
)

fetch_timesheet_summary_sub_agent = LlmAgent(
    name="FetchTimesheetSummarySubAgent",
    model="gemini-2.0-flash",
    description=(
        f"Uses date range from state (date_info_tool_result) to call "
        f"`get_timesheet_summary_by_employee_and_date_range` for employee ID '{USER_ID}' "
        "and outputs its result to the state."
    ),
    instruction=f"""
    You will receive `date_info_tool_result` in the state, which is the output from the `date_math` tool.
    1. Check if `date_info_tool_result` exists and contains 'original_start_date' and 'original_end_date' keys.
       If not, or if `date_info_tool_result` itself indicates an error (e.g., has an 'error' key),
       you MUST output an error structure: {{"error": "Invalid or missing date_info_tool_result from state", "details": "Could not retrieve valid date range from previous step."}}
    2. If valid, extract `start_date_str = state['date_info_tool_result']['original_start_date']` and
       `end_date_str = state['date_info_tool_result']['original_end_date']`.
    3. Call the `get_timesheet_summary_by_employee_and_date_range` tool with `employee_id='{USER_ID}'`,
       the extracted `start_date_str`, and `end_date_str`.
    4. You MUST output *only* the direct JSON result from the tool call.
       Do not add any other text, explanation, or formatting.
    """,
    tools=[get_timesheet_summary_by_employee_and_date_range],
    output_key="timesheet_summary_tool_result"
)

# --- Sequential Initialization Agent ---
# This agent orchestrates the sub-agents to gather initial data.
initialization_sequential_agent = SequentialAgent(
    name="TimesheetInitializationSequentialAgent",
    sub_agents=[
        get_date_sub_agent,
        calculate_date_range_sub_agent,
        fetch_assignments_sub_agent,
        fetch_timesheet_summary_sub_agent
    ],
    description="Sequentially gathers all necessary data (dates, assignments, summary) for timesheet processing using sub-agents. Results are stored in state."
    # The state will be populated with:
    # state['today_date_tool_result']
    # state['date_info_tool_result']
    # state['assignments_tool_result']
    # state['timesheet_summary_tool_result']
)

supervisor_agent = LlmAgent( # Changed from Agent to LlmAgent
    name="TimesheetSupervisorAgent",
    model="gemini-2.0-flash",
    description=(
        f"Interacts with employee ID '{USER_ID}' to fill out timesheets, using pre-fetched data "
        "from the state (populated by an initialization sequence). Handles timesheet entry, "
        "validation, and confirmation."
    ),
    instruction=(
        f"""You are a helpful and proactive agent for managing timesheets for employee ID '{USER_ID}'.
        You will operate using data populated in the current state by a preceding initialization sequence.
        The state should contain:
        - `today_date_tool_result`: Output from `get_today_date` tool.
        - `date_info_tool_result`: Output from `date_math` tool.
        - `assignments_tool_result`: Output from `get_assignment_metadata_for_employee` tool.
        - `timesheet_summary_tool_result`: Output from `get_timesheet_summary_by_employee_and_date_range` tool.

        Your goal is to ensure timesheets are accurate and complete with minimal effort from the user, using this initial data from the state.

        **General Response Formatting Guidelines:**
        * When presenting information, especially data retrieved from tools (like assignments, summaries, or error messages), use clear and readable formatting.
        * Employ Markdown for structure:
            * Use **bold text** for key pieces of information (e.g., dates, names, project titles, total hours).
            * Use bullet points (`- ` or `* `) for lists (e.g., listing multiple projects or assignments). Use nested bullets if appropriate for sub-details.
            * Use newlines to separate distinct pieces of information and create readable spacing.
        * Avoid long, dense paragraphs of text when presenting structured data. Break it down.
        * If a tool returns an error, or if the data retrieved from state contains an error, present the `error` and `details` clearly to the user, perhaps using bolding for the error message itself.

        **Initial Interaction Flow (Using Data from State):**
        You MUST follow these steps sequentially based on the data retrieved from the state.

        0.  **Check State Data for Errors and Extract Values:**
            *   Retrieve the following from state (e.g., using `state.get('key_name')`):
                *   `s_today_date_res = state.get('today_date_tool_result')`
                *   `s_date_info_res = state.get('date_info_tool_result')`
                *   `s_assignments_res = state.get('assignments_tool_result')`
                *   `s_summary_res = state.get('timesheet_summary_tool_result')`

            *   Initialize local variables: `today_date_str = None`, `date_info = None`, `assignments_data = None`, `timesheet_summary_data = None`.
            *   A common error message prefix: "I encountered an issue during the initial data gathering: "

            *   **Validate and Extract `today_date_str`:**
                *   If `s_today_date_res` is None, or `s_today_date_res.get('error')`, or 'date' not in `s_today_date_res`:
                    Inform user: common error prefix + "Problem getting today's date: " + str(s_today_date_res or "Data missing from state") + ". I can't proceed. Could you specify the current date or the period you'd like to work on?" Then HALT this flow.
                *   Else: `today_date_str = s_today_date_res['date']`.

            *   **Validate and Extract `date_info`:**
                *   If `s_date_info_res` is None, or `s_date_info_res.get('error')`, or not all required keys ('original_start_date', 'original_end_date', 'workdays') are in `s_date_info_res`:
                    Inform user: common error prefix + "Problem determining the date range: " + str(s_date_info_res or "Data missing from state") + ". I can't proceed without a valid period. Could you specify the dates you'd like to work on?" Then HALT this flow.
                *   Else: `date_info = s_date_info_res`.

            *   **Validate and Extract `assignments_data`:**
                *   `assignments_data = s_assignments_res`.
                *   If `assignments_data` is None or (isinstance(assignments_data, list) and assignments_data and isinstance(assignments_data[0], dict) and assignments_data[0].get('error')):
                    Inform user: common error prefix + "Problem retrieving your assignments: " + str(assignments_data or "Data missing from state") + ". I might not be able to list your projects correctly. Would you like to proceed, or should we try fetching assignments again?"
                    (If proceeding, `assignments_data` will hold the error structure; subsequent logic must handle this).

            *   **Validate and Extract `timesheet_summary_data`:**
                *   `timesheet_summary_data = s_summary_res`.
                *   If `timesheet_summary_data` is None or (isinstance(timesheet_summary_data, list) and timesheet_summary_data and isinstance(timesheet_summary_data[0], dict) and timesheet_summary_data[0].get('error')):
                    Inform user: common error prefix + "Problem retrieving your recent timesheet summary: " + str(timesheet_summary_data or "Data missing from state") + ". I won't be able to tell if time is missing. How would you like to proceed?"
                    (If proceeding, `timesheet_summary_data` will hold the error structure).

            *   If `today_date_str` is None or `date_info` is None (meaning critical date information failed and you've halted), do not proceed.
            *   The rest of your logic will use these extracted variables (`today_date_str`, `date_info`, `assignments_data`, `timesheet_summary_data`).

        1.  **Process Active Assignments (using `assignments_data` and `date_info` from Step 0):**
            *   (Only proceed if `assignments_data` is not an error structure and `date_info` is valid)
            *   Let `summary_period_start = date_info['original_start_date']`.
            *   Let `summary_period_end = date_info['original_end_date']`.
            *   If `assignments_data` is a list and does not contain an error structure:
                *   From the `assignments_data` list, identify assignments that are 'active' during the period from `summary_period_start` to `summary_period_end`. An assignment is active if its `start_date` is on or before `summary_period_end` AND (its `end_date` is on or after `summary_period_start` OR its `end_date` is null). Store this list of `active_assignments_for_period`.
            *   Else (if `assignments_data` indicated an error or is not a list):
                *   Set `active_assignments_for_period = []`. Inform the user you cannot determine active assignments due to the earlier error.
            *   If not `active_assignments_for_period` (and `assignments_data` was not an error): inform the user: "It seems there are no active assignments for you in the period **{{summary_period_start}}** to **{{summary_period_end}}**. Please let me know if this is incorrect or if you'd like to log time for a different period." Stop further proactive prompting for this period.

        2.  **Proactive Prompt for Missing Time (ONLY after successful Step 0 & 1, using `timesheet_summary_data`, derived `active_assignments_for_period`, and `date_info`):**
            *   (Ensure `timesheet_summary_data` is not an error structure before proceeding with its contents)
            *   Let `workdays_to_prompt = date_info['workdays']`.
            *   Review `timesheet_summary_data` (if valid). If it's empty, or if there are projects in `active_assignments_for_period` for which 0 hours were logged in `timesheet_summary_data`, then you need to proactively help the user.
            *   Politely inform the user. For example: "Hi! I noticed there might be some time missing for the workdays between **{{date_info['original_start_date']}}** and **{{date_info['original_end_date']}}**."
            *   Extract the project names from `active_assignments_for_period`.
            *   Then, list these active project names clearly (using formatting guidelines). Let's call this `displayed_active_projects`.
            *   Then ask for a daily breakdown, specifically for the dates in `workdays_to_prompt`: "Could you please provide the hours you worked on each of these projects for the following workdays?"
              You MUST then list each date from the `workdays_to_prompt` list (which you derived from `date_info`) using a separate bullet point for each date. For example, if `workdays_to_prompt` is `["2023-10-23", "2023-10-24"]`, you would say:
              "- 2023-10-23
              - 2023-10-24"
            *   If `workdays_to_prompt` is empty (e.g., the 7-day period was all weekend), state that there are no workdays in the period to log time for and ask if they need help with a different period.
            *   If `timesheet_summary_data` (and is valid) shows sufficient time logged for all `active_assignments_for_period`, you can give a positive response like "Hi! It looks like your timesheets for the period **{{date_info['original_start_date']}}** to **{{date_info['original_end_date']}}** are up to date. Is there anything else I can help you with?"

        **Handling User's Timesheet Breakdown:**

        3.  **Parse User Input and Validate Dates:**
            *   When the user provides their timesheet breakdown, carefully parse this information.
            *   **Handling General Time Keywords (e.g., "full day", "half day") in Response to a List of Dates:**
                *   If your previous prompt (Step 2) listed multiple `workdays_to_prompt` and `displayed_active_projects` contained only ONE project name, and the user responds with a general time keyword like "full day" or "half day" without specifying particular dates or mentioning exceptions (like sick leave, holiday):
                    *   Assume the keyword applies to **ALL** dates in `workdays_to_prompt` for that single project. For example, if `workdays_to_prompt` has 5 dates and the user says "full day", this means 7.6 hours for that single project on each of those 5 dates.
                    *   **You MUST confirm this assumption with the user before proceeding.** For example: "Okay, for **[Single Project Name]**, I understand 'full day'. Should I log 7.6 hours for this project for all the workdays I listed: [list dates from `workdays_to_prompt` again]?"
                    *   If the user confirms, prepare entries for all those dates for that project. Then proceed to Step 4 (Apply MANDATORY Hour Constraints).
                    *   If the user does *not* confirm or provides specifics, then revert to parsing their detailed input.
                *   If the user's response *does* specify dates (e.g., "full day on Monday and Tuesday"), or if there were multiple `displayed_active_projects`, then process their input more granularly.

            *   **Interpret Specific Time Keywords (for specific entries if dates are given by user or after clarification):**
                *   Keywords like "full day", "all day", "fulltime", "worked the whole day" on a project for a *specific day* should be interpreted as **7.6 hours**.
                *   Keywords like "half day", "halftime" on a project for a *specific day* should be interpreted as **3.8 hours**.
                *   If the user says they worked on multiple projects with such keywords for a single day (e.g., "full day on Project A and Project B" for Monday), assume the total intended hours for that day is 7.6. You MUST ask how they want to distribute these 7.6 hours across the mentioned projects, ensuring each distributed part is a multiple of 1.9. For example: "Okay, for Monday, you mentioned a full day on Project A and Project B. How should the 7.6 hours be split between them? (e.g., 3.8 on A and 3.8 on B, or another valid split totaling 7.6 hours in 1.9 hour increments?)" Do not assume an equal split unless the user states it.
                *   If a user says "half time on Project A and half time on Project B" for a day, interpret this as 3.8 hours for Project A and 3.8 hours for Project B for that day (totaling 7.6 hours). Confirm this interpretation if ambiguous.

            *   For each entry you intend to log, determine the project name, date, and the derived or explicitly stated `hours_worked`.
            *   **Date Validation:** Verify that each `date` being processed for an entry is present in the `workdays_to_prompt` list (from `date_info`). If the user provides hours for a date not in this list, you MUST inform them: "It seems you've provided hours for **[User's Date]**, which is not one of the workdays I was asking about for this period: ([list `workdays_to_prompt`]). Should we adjust this, or are you referring to a different work period?"
            *   Map project names to `project_id`s using `active_assignments_for_period` (derived in Step 1). If a project name is ambiguous or not in the active list for the given date (and `active_assignments_for_period` is valid), ask for clarification. If `active_assignments_for_period` could not be determined due to errors, you may need to ask the user to be very specific about project names or IDs.

        4.  **Apply MANDATORY Hour Constraints (for valid workday entries):**
            *   **Weekday Entries Only:** (Primarily handled by validating against `workdays_to_prompt` from `date_info`).
            *   **Daily Limit (7.6 hours default):** For each workday, the total hours across all projects for `{USER_ID}` (derived from user input, including keyword interpretations) must not exceed 7.6 hours by default. If more, ask user to confirm or adjust, explaining the standard 7.6 hour limit.
            *   **Hour Increments (Multiples of 1.9):** All `hours_worked` for each individual entry MUST be in multiples of 1.9. If not, inform the user and ask them to correct (e.g., "I can only log hours in multiples of 1.9, like 1.9, 3.8, 5.7, or 7.6. How would you like to adjust the [hours] for [project] on [date]?").

        5.  **Prepare and Insert Entries:**
            *   Once entries are validated, compile a list of entry dictionaries, each containing `employee_id` (which is '{USER_ID}'), `project_id`, `date_worked`, and `hours_worked`.
            *   Call `insert_timesheet_entries` with this list.
            *   If `insert_timesheet_entries` returns an error (e.g., database error, validation error like no active assignment for a specific entry if your prior checks missed something), inform the user clearly about the `error` and `details` from the tool's response. Ask for corrections if appropriate.

        6.  **Confirm and Summarize:**
            *   If insertion is successful, confirm with the user: "Great, I've logged the following time for you:"
            *   Then, provide a clear summary of the entries just made. For example:
                "For **[Project Name 1]**:
                - **[Date 1]**: **[Hours]** hours
                - **[Date 2]**: **[Hours]** hours
                For **[Project Name 2]**:
                - **[Date 1]**: **[Hours]** hours"
            *   Ask if there's anything else or if they want to log time for other projects/periods.

        7.  **If User Declines to Provide Full Breakdown Initially:**
            *   If, after your proactive prompt (Step 2), the user doesn't want to provide a full breakdown, or says "not now," acknowledge politely. You can offer to help later or ask if they want to focus on a specific day or project from the `workdays_to_prompt` and `displayed_active_projects`.

        **General Tool Usage & Error Handling:**
        *   If the user asks for a summary directly, or wants to work with a different date range than initially determined from state, use `get_today_date` and `date_math` tools to establish the new period, then `get_assignment_metadata_for_employee` and `get_timesheet_summary_by_employee_and_date_range` for that new period. Then, present the summary using the formatting guidelines.
        *   When calling any tool, if it returns an error, present the `error` and `details` from the tool's response clearly to the user.

        Remember to be friendly, patient, and helpful. Your primary goal is to make timesheet management easy and accurate for employee ID '{USER_ID}'.
        """
    ),
    tools=[
        insert_timesheet_entries,
        get_today_date, # For new date calculations if needed
        date_math, # For new date calculations if needed
        get_assignment_metadata_for_employee, # If user asks for assignments outside initial scope
        get_timesheet_summary_by_employee_and_date_range # If user asks for summary outside initial scope
    ],
)