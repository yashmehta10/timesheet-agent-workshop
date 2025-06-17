# 🏃‍♂️ Timesheet Agent Workshop

This runsheet includes the essential commands and steps required to run the timesheet agent locally.

---

## ✅ Prerequisites

- Python 3.8+
- Google CLoud SDK
- Git
- ADK CLI installed (`pip install google-adk`)

OR

- Google Cloud Shell 
---

## 📥 Clone the Repository

```bash
git clone https://github.com/yashmehta10/timesheet-agent-workshop.git
cd timesheet-agent-workshop
```

## 🧪 Create and Activate a Virtual Environment
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

## 📦 Install Dependencies
```bash
pip install -r requirements.txt
```

## ⚙️ Set Environment Variables
Create a file at timesheet_agent/.env based on .env.local file:

```
GOOGLE_GENAI_USE_VERTEXAI=
GOOGLE_CLOUD_PROJECT=
GOOGLE_CLOUD_LOCATION=
TIMESHEET_DB_PATH=timesheet_agent/database/timesheet.db
```

## 🛠️ Initialize the SQLite Database
```bash
cd database
sqlite3 timesheet.db < sql/timesheet_schema.sql
sqlite3 timesheet.db < sql/read_data.sql
```

## 🚀 Run the Agent Locally
Navigate to the Agent  directory under timesheet-agent-workshop/timesheet_agent
```bash
adk web
```