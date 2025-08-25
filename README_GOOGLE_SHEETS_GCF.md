### Google Sheets Integration Playbook (Google Cloud Functions)

This README is a starting point for building and migrating Google Sheets integrations backed by Google Cloud Functions. It distills the working patterns from this repo so you can reuse them without re‑inventing auth, I/O, and error handling.

Use this as a template in a new repository.


### Scope
- **Write to Google Sheets**: Export data (e.g., from BigQuery) and write into a Sheet/tab and range
- **Read from Google Sheets**: Fetch rows from a Sheet/tab and load to BigQuery
- **Cloud Functions**: HTTP-triggered functions, Python runtime


### Prerequisites
- **Google Cloud Project** with the following APIs enabled:
  - **Google Sheets API**
  - **BigQuery API** (and optionally BigQuery Storage API)
  - **Cloud Functions API** (or Cloud Run if deploying as 2nd gen)
- **Service Account** with roles:
  - For reading/writing Sheets: share the target spreadsheet with the service account email
  - For BigQuery: `BigQuery Data Viewer` (read), `BigQuery Data Editor` or `BigQuery Job User` (write/load)
- **Credentials**: Either
  - Use the Cloud Function/Cloud Run default service account (preferred for production), or
  - Provide a service account JSON key (e.g., `gbq_creds.json`) and use explicit credentials


### Configuration and Environment
You will typically provide these via URL query parameters to the HTTP function, or via environment variables if that fits your deployment better.

- **Authentication**
  - `SERVICE_ACCOUNT_FILE` (optional if not using ADC): path to JSON key (e.g., `gbq_creds.json`)
  - `GOOGLE_CLOUD_PROJECT`: inferred automatically if running in GCP; set explicitly for local/dev
  - Alternatively set `GOOGLE_APPLICATION_CREDENTIALS` to point to the JSON key (local/dev)

- **Sheets parameters (HTTP query or env)**
  - `spreadsheet_id`: the Spreadsheet ID (from its URL)
  - `sheet_name`: the tab name
  - `range`: optional A1 notation for reads (e.g., `A1:Z1000`)
  - `starting_cell`: for writes (e.g., `A3`)

- **BigQuery parameters (HTTP query or env)**
  - `journey`: dynamic dataset suffix (pattern used in this repo)
  - `table_name`: source table for exports to Sheets
  - `destination_table`: destination table for imports from Sheets
  - `BIGQUERY_PROJECT_ID`: defaults to your project (e.g., `qalearn`)
  - `BIGQUERY_DATASET`: often computed like `by_journey_{journey}`

- **Query customization (optional, used in this repo)**
  - `columns_ordered_from_left_to_right`: comma-separated list, supports aliasing via `original:new`
  - `columns_to_hide`: comma-separated list of columns to exclude
  - `where_clause`: optional SQL filter appended to the query


### Libraries
Add these to your `requirements.txt` as needed:
```
functions-framework
google-cloud-bigquery
google-api-python-client
google-auth
pandas
pyarrow
gspread
```
Notes:
- Use `googleapiclient.discovery.build` + Sheets v4 for low-level control of Sheets operations
- Use `gspread` for ergonomic read access to Sheets


### Core Patterns and Code Snippets

- **Authenticate (Sheets via explicit key file + scopes)**
```python
from google.oauth2 import service_account
from googleapiclient.discovery import build

scopes = ["https://www.googleapis.com/auth/spreadsheets"]
creds = service_account.Credentials.from_service_account_file(
    "gbq_creds.json", scopes=scopes
)
sheets_api = build("sheets", "v4", credentials=creds)
```

- **Write values to a Sheet (clear range + update)**
```python
# Clear a block then write values starting from a cell
clear_range = f"{sheet_name}!{starting_cell}:Z100000"
sheets_api.spreadsheets().values().clear(
    spreadsheetId=spreadsheet_id,
    range=clear_range,
    body={}
).execute()

body = {"values": rows}  # rows is a 2D list, first row often headers
sheets_api.spreadsheets().values().update(
    spreadsheetId=spreadsheet_id,
    range=f"{sheet_name}!{starting_cell}",
    valueInputOption="RAW",  # or "USER_ENTERED"
    body=body
).execute()
```

- **Read values from a Sheet using gspread**
```python
import gspread
from google.oauth2.service_account import Credentials

creds = Credentials.from_service_account_file(
    "gbq_creds.json",
    scopes=["https://www.googleapis.com/auth/spreadsheets"],
)
client = gspread.authorize(creds)
sheet = client.open_by_key(spreadsheet_id).worksheet(sheet_name)

# Either read a range, or whole sheet
values = sheet.get("A1:Z1000")
# values = sheet.get_all_values()

headers = values[0]
records = values[1:]
```

- **Query BigQuery and transform results for Sheets**
```python
from google.cloud import bigquery

bq_client = bigquery.Client()
query = f"""
SELECT *
FROM `{project_id}.by_journey_{journey}.{table_name}`
{f"WHERE {where_clause}" if where_clause else ""}
"""
rows_iter = bq_client.query(query).result()
headers = [schema_field.name for schema_field in rows_iter.schema]
rows = [headers]
for row in rows_iter:
    rows.append([row.get(h) if row.get(h) is not None else "" for h in headers])
```

- **Load a DataFrame to BigQuery**
```python
from google.cloud import bigquery
import pandas

bq_client = bigquery.Client()
job_config = bigquery.LoadJobConfig(
    autodetect=True,
    write_disposition="WRITE_TRUNCATE",
)
load_job = bq_client.load_table_from_dataframe(
    dataframe, f"{project_id}.{dataset}.{table}", job_config=job_config
)
load_job.result()
```

- **Normalize column names for BigQuery compatibility**
```python
import re

dataframe.columns = [
    re.sub(r"[^a-zA-Z0-9_]", "_", name).lower() for name in dataframe.columns
]
```


### Function Interfaces (as used in this repo)

- **Export BigQuery → Google Sheet** (HTTP GET)
  - Required: `spreadsheet_id`, `journey`
  - Optional: `sheet_name` (default `candidates`), `starting_cell` (default `A3`), `table_name` (default `candidates_all_fields_flat`)
  - Optional query customization: `columns_ordered_from_left_to_right`, `columns_to_hide`, `where_clause` (fetched from settings table in BigQuery in this repo)

- **Import Google Sheet → BigQuery** (HTTP GET)
  - Required: `spreadsheet_id`, `sheet_name`, `journey`, `destination_table`
  - Optional: `range` (A1 notation). If omitted, reads entire sheet


### Deployment Notes (gcloud)
Examples for 2nd gen Cloud Functions (adapt as needed):

- **Export to Sheets function**
```bash
gcloud functions deploy gbq_query_output_to_gsheet \
  --gen2 \
  --runtime=python311 \
  --region=us-central1 \
  --entry-point=gbq_query_output_to_gsheet \
  --trigger-http \
  --allow-unauthenticated
```

- **Import from Sheets function**
```bash
gcloud functions deploy load_gsheet_to_bigquery_cloud_function \
  --gen2 \
  --runtime=python311 \
  --region=us-central1 \
  --entry-point=load_gsheet_to_bigquery_cloud_function \
  --trigger-http \
  --allow-unauthenticated
```

- If you rely on an explicit key file (e.g., `gbq_creds.json`), include it in the source upload only for experimentation. For production, prefer:
  - Use the default runtime service account + IAM roles; or
  - Store secrets in Secret Manager and mount/inject at runtime (Cloud Functions/Run support this in 2nd gen)


### Common Issues and Fixes
- **403 on Sheets API**: Share the spreadsheet with the service account email; ensure `https://www.googleapis.com/auth/spreadsheets` scope is used.
- **404 Not Found (Sheet/tab)**: The tab name is case-sensitive; verify `sheet_name` exists.
- **Auth/Key errors**: Ensure the JSON key is valid; if using ADC (default credentials), do not try to load a key file.
- **BigQuery dataset/table not found**: Verify `project_id.dataset.table` exists or permissions allow creation; confirm the `journey` dataset pattern.
- **Schema/Type issues**: When loading from Sheets, headers form column names—normalize headers and rely on autodetect; for dates, convert to ISO strings if needed.
- **Large writes to Sheets**: Prefer clearing and rewriting in a single `values.update` call; batch where possible; avoid cell-by-cell updates.
- **Rate limits**: Add small backoff/retries around Sheets API calls if you expect bursts.
- **ValueInputOption**: Use `RAW` for exact values; `USER_ENTERED` to allow Sheets to parse numbers/dates/formulas.


### Local Development
- Install deps:
```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```
- Run locally with Functions Framework:
```bash
functions-framework --target load_gsheet_to_bigquery_cloud_function --port 8080
```
- Call the function:
```bash
curl "http://localhost:8080?spreadsheet_id=...&sheet_name=Sheet1&journey=test&destination_table=my_table"
```


### Security Best Practices
- Prefer Workload Identity / default service account over embedding key files
- Use least-privilege IAM roles for the runtime principal
- Keep Sheets shared only with intended service accounts; avoid public sharing
- Store secrets in Secret Manager and never commit them to VCS


### Minimal End-to-End Examples

- **BigQuery → Sheet**
```python
# 1) Query BigQuery to rows (headers + values)
# 2) Clear target range in Sheet
# 3) Write values starting from A3
```

- **Sheet → BigQuery**
```python
# 1) Read values (optionally a range) from Sheet
# 2) Create DataFrame, normalize headers
# 3) Load DataFrame to BigQuery with autodetect and WRITE_TRUNCATE
```


### Notes Specific to This Repo
- Datasets follow pattern `by_journey_{journey}` within project `qalearn`
- Export function optionally reads – from `qalearn.by_journey_{journey}.job_search_reporting_settings` – settings that control column ordering, aliases, hidden columns, and `where_clause`
- Example parameters used here:
  - Export: `spreadsheet_id`, `sheet_name` (default `candidates`), `starting_cell` (default `A3`), `journey`, `table_name` (default `candidates_all_fields_flat`)
  - Import: `spreadsheet_id`, `sheet_name`, `journey`, `destination_table`, optional `range`


This document should be copied to the new repository as the foundational README for Google Sheets integrations with Cloud Functions.
