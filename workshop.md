# 🏃‍♂️ Timesheet Agent Workshop

This runsheet includes the essential commands and steps required to run the timesheet agent locally.

---

## ✅ Prerequisites

- **Python 3.8+** (required to run the agent)
- **Git** (to clone the repository)
- **Google Cloud Authentication** (required for Vertex AI access)

**Note:** If you're using **Google Cloud Shell**, it comes with Python, Git, and gcloud CLI pre-installed and pre-authenticated.

---

## 🔐 Google Cloud Authentication Setup

<details>
<summary><strong>⚠️ IMPORTANT: Authentication Required</strong> - Click to expand authentication options</summary>

**By default this agent uses Vertex AI API and requires Google Cloud authentication. Choose ONE of the following methods:**

### Option 1: Google Cloud SDK (Recommended)

#### Installation:
```bash
# macOS with Homebrew:
brew install google-cloud-sdk

# Windows with Chocolatey:
choco install gcloudsdk

# Windows with Scoop:
scoop bucket add extras
scoop install gcloud

# Or download installer from: https://cloud.google.com/sdk/docs/install
```

#### Authentication:
```bash
# Authenticate with Google Cloud
gcloud auth application-default login

# Set your project (replace with your actual project ID)
gcloud config set project YOUR_PROJECT_ID
```

### Option 2: Service Account Key File
1. Create a service account in Google Cloud Console
2. Download the JSON key file
3. Set the environment variable:

**Linux/macOS:**
```bash
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/your/service-account-key.json"
```

**Windows (Command Prompt):**
```cmd
set GOOGLE_APPLICATION_CREDENTIALS=C:\path\to\your\service-account-key.json
```

**Windows (PowerShell):**
```powershell
$env:GOOGLE_APPLICATION_CREDENTIALS="C:\path\to\your\service-account-key.json"
```

### Option 3: Workload Identity Federation
For enterprise environments using external identity providers, follow the [Workload Identity Federation guide](https://cloud.google.com/iam/docs/workload-identity-federation).

</details>


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
Create a file at `timesheet_agent/.env` based on the template below. **Ensure you add your actual GOOGLE_CLOUD_PROJECT ID**:

```
GOOGLE_GENAI_USE_VERTEXAI=TRUE
GOOGLE_CLOUD_PROJECT={your-actual-project-id}
GOOGLE_CLOUD_LOCATION=us-central1
TIMESHEET_DB_PATH=timesheet_agent/database/timesheet.db
```

**🔍 How to find your Project ID:**
- Google Cloud Console: Look at the top of any GCP page
- Command line: `gcloud config get-value project`

## 🛠️ Initialize the SQLite Database
If you want to customize, update the `timesheet_schema.sql` file:
```sql
INSERT INTO employees (first_name, last_name, email) VALUES
('<your first name>', '<your last name>', '<your email>');  -- employee_id will be 1
```

### Initialize Database

```bash
# Initialize database schema and sample data
cd timesheet_agent/database
sqlite3 timesheet.db < sql/timesheet_schema.sql  # Creates tables and relationships
sqlite3 timesheet.db < sql/read_data.sql         # Inserts sample data for employees, projects, and assignments
```
📖 **Detailed schema:** See `timesheet_agent/database/sql/timesheet_schema.sql` for complete schema definitions, constraints, and sample data.

## 🚀 Run the Agent Locally
Navigate to the root directory (timesheet-agent-workshop) using `cd ../..` if you are still in the database folder.
```bash
adk web
```

## 🔧 Troubleshooting

### Authentication Errors
If you see errors like "DefaultCredentialsError" or "Your default credentials were not found":

1. **Verify authentication**: `gcloud auth list`
2. **Re-authenticate**: `gcloud auth application-default login`
3. **Check project setting**: `gcloud config get-value project`
4. **Verify environment variables**: Check your `.env` file has the correct project ID

### Common Issues
- **Missing project ID**: Ensure `GOOGLE_CLOUD_PROJECT` in `.env` matches your actual GCP project
- **Vertex AI not enabled**: Enable the Vertex AI API in your Google Cloud project
- **Billing not enabled**: Ensure billing is enabled for your Google Cloud project

---

**🎯 Ready to go!** Your timesheet agent should now be running at `http://localhost:8000`
