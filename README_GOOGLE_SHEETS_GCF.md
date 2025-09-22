### Neon Postgres → Google Sheets (Cloud Function)

This repo provides HTTP Cloud Functions for bidirectional data sync between Neon Postgres and Google Sheets:

1. **Export**: `pg_query_output_to_gsheet` - executes SELECT queries against Neon Postgres and writes results to Google Sheets
2. **Import**: `gsheet_to_database` - reads specified columns from Google Sheets and loads them into Neon Postgres

**Import Function**: See `README_GSHEET_TO_DATABASE.md` for the separate `gsheet_to_database` function that imports from Sheets to Postgres.


### Prerequisites
- Google Cloud project with APIs enabled:
  - Cloud Functions API (Gen2)
  - Cloud Run API
  - Artifact Registry API
  - Cloud Build API
  - Google Sheets API
- Runtime service account with:
  - Access to invoke the function (IAM) for your user/group
  - Secret Manager access (to read `NEON_DATABASE_URL` if you use a secret)
- The spreadsheet shared with the runtime service account email (to allow writing)
- A Neon Postgres connection string, stored as env var `NEON_DATABASE_URL` (or Secret Manager)


### Function Overview
- **Live URL**: `https://pg-query-output-to-gsheet-grz2olvbca-uc.a.run.app`
- Path: HTTP trigger (GET supported)
- Entry point: `pg_query_output_to_gsheet`
- Auth: IAM-protected by default (no public token). Your user/group must have Cloud Run Invoker on the function.

Parameters (query string):
- Required
  - `spreadsheet_id`: Spreadsheet ID to write to
  - One of: `sql` (inline SELECT) or `sql_cell` (A1 notation to read SQL from the sheet)
- Optional
  - `sheet_name` (default: `Data`)
  - `starting_cell` (default: `F2`)
  - `timestamp_cell`: write last-run ISO timestamp to this cell (e.g., `Config!C1`)
  - `status_cell`: write status/row count to this cell (e.g., `Config!D1`)
  - `row_limit` (default: 50000)
  - `include_headers` (default: true)
  - `value_input_option` (`RAW` or `USER_ENTERED`, default `RAW`)

### 🔧 JSON Unnesting Feature

**NEW:** Automatically flatten JSON columns into separate columns using the `{{all_fields_as_columns_from(...)}}` syntax.

#### Syntax
```sql
SELECT *, {{all_fields_as_columns_from(json_column, question_title, value_text)}}
FROM your_table
WHERE conditions...
```

#### Parameters
- `json_column`: Name of the JSON/JSONB column containing array data
- `name_key`: JSON field to use as column names (e.g., "question_title")
- `value_key`: JSON field to use as column values (e.g., "value_text")

#### Example
```sql
-- Input JSON column: answers_json
-- [{"question_title": "Experience", "value_text": "5 years"}, {"question_title": "Skills", "value_text": "Python, SQL"}]

SELECT *,
       {{all_fields_as_columns_from(answers_json, question_title, value_text)}}
FROM public_marts.candidates
WHERE position_name ILIKE '%flutter%'
```

**Result:** Creates columns like `answers_json_question_title_1`, `answers_json_value_text_1`, etc. with flattened data.

Behavior:
- Reads SQL (prefer `sql_cell` to keep URLs short)
- Enforces single SELECT, applies `row_limit` if none specified
- Executes query read-only on Neon Postgres
- Clears prior data from `sheet_name!starting_cell` downward and writes headers+rows
- Writes timestamp and status if cells provided


### Local Files
- `cloud_function/main.py` – the function implementation
- `cloud_function/requirements.txt` – function dependencies
- `requirements.txt` – root-level dependencies (dev/local)
- `.github/workflows/deploy.yml` – GitHub Actions deployment
- `env.example` – sample environment variables


### Environment
- `NEON_DATABASE_URL`: Postgres connection string (sslmode=require)
- Optional:
  - `FUNCTION_NAME`: defaults to `pg_query_output_to_gsheet`
  - In CI: `SECRET_NEON_DATABASE_URL` (Secret Manager ref) or `NEON_DATABASE_URL` (direct value)

### Deploy (via GitHub Actions)
- Add GitHub Secrets:
  - `GBQ_CREDS_JSON`: service account JSON with deploy rights
  - Either:
    - `SECRET_NEON_DATABASE_URL`: Secret Manager resource (e.g., `projects/<id>/secrets/NEON_DATABASE_URL`), or
    - `NEON_DATABASE_URL`: direct connection string
  - Optionally: `GCP_PROJECT_ID`, `GCP_REGION` (defaults derived from JSON if omitted), `FUNCTION_NAME`
- Push to `main` or trigger the workflow manually. The action prints the function URL after deploy.


### Google Sheet Setup (Step-by-step)
1) Create tabs: `Config` and `Data`. Share the spreadsheet with the runtime service account.
2) Fill `Config` row 1:
   - A1: `https://pg-query-output-to-gsheet-grz2olvbca-uc.a.run.app`
   - B1: SQL query (single SELECT, no semicolon). Example:
     - `SELECT * FROM public_marts.candidates WHERE position_name ILIKE '%flutter%'`
   - C1: (auto) last sync timestamp
   - D1: (auto) status/row count
3) Add run link in `Config!A3`:
```
=HYPERLINK(
  A1
  & "?spreadsheet_id=" & ENCODEURL(REGEXEXTRACT(TO_TEXT(SPREADSHEET_URL()), "/d/([^/]+)"))
  & "&sheet_name=" & ENCODEURL("Data")
  & "&starting_cell=" & ENCODEURL("A2")
  & "&sql_cell=" & ENCODEURL("Config!B1")
  & "&timestamp_cell=" & ENCODEURL("Config!C1")
  & "&status_cell=" & ENCODEURL("Config!D1"),
  "🚀 Run Export"
)
```4) Click the link to export. If you see 403, grant your identity `roles/run.invoker` on the function.

**Note**: Replace `YOUR_SPREADSHEET_ID` with your actual spreadsheet ID (found in the URL between `/d/` and `/edit`).

CSV template for `Config` row 1 (A1:D1):
```
"https://pg-query-output-to-gsheet-grz2olvbca-uc.a.run.app","SELECT * FROM public_marts.candidates WHERE position_name ILIKE '%flutter%'","",""
```

**JSON Unnesting CSV Template:**
```
"https://pg-query-output-to-gsheet-grz2olvbca-uc.a.run.app","SELECT *, {{all_fields_as_columns_from(answers_json, question_title, value_text)}} FROM public_marts.candidates WHERE position_name ILIKE '%flutter%'","",""
```

### Real Examples

#### Example 1: Simple Export
```
https://pg-query-output-to-gsheet-grz2olvbca-uc.a.run.app?spreadsheet_id=YOUR_SPREADSHEET_ID&sql=SELECT%20*%20FROM%20users%20WHERE%20active%20=%20true&sheet_name=ActiveUsers&starting_cell=A1
```

#### Example 2: Export with SQL from Sheet (Recommended)
```
https://pg-query-output-to-gsheet-grz2olvbca-uc.a.run.app?spreadsheet_id=YOUR_SPREADSHEET_ID&sql_cell=Config!B1&sheet_name=Data&starting_cell=A2&timestamp_cell=Config!C1&status_cell=Config!D1
```

#### Example 3: Complex Query with All Options
```
https://pg-query-output-to-gsheet-grz2olvbca-uc.a.run.app?spreadsheet_id=YOUR_SPREADSHEET_ID&sql=SELECT%20u.id%2C%20u.name%2C%20u.email%2C%20p.title%20FROM%20users%20u%20JOIN%20profiles%20p%20ON%20u.id%20=%20p.user_id%20WHERE%20u.created_at%20%3E%20%272024-01-01%27&sheet_name=UserProfiles&starting_cell=A1&timestamp_cell=Config!C1&status_cell=Config!D1&row_limit=1000&include_headers=true&value_input_option=RAW
```

#### Example 4: JSON Unnesting - Export All Candidate Survey Data
```
https://pg-query-output-to-gsheet-grz2olvbca-uc.a.run.app?spreadsheet_id=YOUR_SPREADSHEET_ID&sql=SELECT%20*%20FROM%20public_marts.candidates%20WHERE%20position_name%20ILIKE%20%27%25flutter%25%27%20%7B%7Ball_fields_as_columns_from(answers_json%2C%20question_title%2C%20value_text)%7D%7D&sheet_name=CandidateSurveys&starting_cell=A1
```

**Decoded SQL:**
```sql
SELECT *
FROM public_marts.candidates
WHERE position_name ILIKE '%flutter%'
{{all_fields_as_columns_from(answers_json, question_title, value_text)}}
```

**Result:** Creates flattened columns like:
- `answers_json_question_title_1` → "What is your experience level?"
- `answers_json_value_text_1` → "5+ years"
- `answers_json_question_title_2` → "Preferred programming languages"
- `answers_json_value_text_2` → "Python, JavaScript, SQL"

#### Example 5: Multiple JSON Fields with Complex Query
```
https://pg-query-output-to-gsheet-grz2olvbca-uc.a.run.app?spreadsheet_id=YOUR_SPREADSHEET_ID&sql=SELECT%20c.id%2C%20c.name%2C%20c.email%20FROM%20public_marts.candidates%20c%20WHERE%20c.status%20%3D%20%27active%27%20%7B%7Ball_fields_as_columns_from(c.preferences%2C%20setting%2C%20value)%7D%7D%20%7B%7Ball_fields_as_columns_from(c.survey_responses%2C%20question%2C%20answer)%7D%7D&sheet_name=CandidateDetails&starting_cell=A1&include_headers=true
```

**Decoded SQL:**
```sql
SELECT c.id, c.name, c.email
FROM public_marts.candidates c
WHERE c.status = 'active'
{{all_fields_as_columns_from(c.preferences, setting, value)}}
{{all_fields_as_columns_from(c.survey_responses, question, answer)}}
```

**Result:** Multiple flattened column sets from different JSON fields.


### Troubleshooting
- 403 on function invoke: your user/group needs `roles/run.invoker` on the function.
- 403 on Sheets API: share the spreadsheet with the function’s runtime service account email.
- Empty output: test the SQL against Neon; check `status_cell` for error details.
- URL too long: store the SQL in `Config!B1` and use `sql_cell` (recommended).


### Security Notes
- Prefer IAM-protected invocation over public access. No token needed.
- Store the Neon connection string in Secret Manager when possible.
- The function performs read-only queries and rejects non-SELECT statements.

