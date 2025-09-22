# Complete Documentation with Real Examples

This document provides comprehensive examples for both Cloud Functions based on the actual deployed code.

## 🚀 What's New: JSON Unnesting Feature

**NEW:** Both functions now support automatic JSON column flattening using the `{{all_fields_as_columns_from(...)}}` syntax.

- **Export Function**: Unnest JSON data from Postgres to flat columns in Google Sheets
- **Import Function**: Store data as JSON for later unnesting via export
- **Automatic**: No manual JSON parsing or complex queries needed
- **Flexible**: Works with any JSON structure using key-based field mapping

## 🚀 Function URLs (Live)

- **Export (Postgres → Sheets)**: `https://pg-query-output-to-gsheet-grz2olvbca-uc.a.run.app`
- **Import (Sheets → Postgres)**: `https://gsheet-to-database-grz2olvbca-uc.a.run.app`

## 📊 Function 1: Export Postgres Data to Google Sheets

### Overview
Executes SELECT queries against Neon Postgres and writes results to Google Sheets.

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

#### How It Works
1. **Parse**: Identifies `{{...}}` syntax in your SQL query
2. **Transform**: Converts to PostgreSQL CTEs using `jsonb_array_elements`
3. **Execute**: Runs the transformed query with flattened results
4. **Export**: Writes flattened data to Google Sheets

#### Example JSON Input
```sql
-- Table: public_marts.candidates
-- Column: answers_json (JSONB)
-- Value: [{"question_title": "Experience", "value_text": "5 years"}, {"question_title": "Skills", "value_text": "Python, SQL"}]
```

#### Example Query
```sql
SELECT *,
       {{all_fields_as_columns_from(answers_json, question_title, value_text)}}
FROM public_marts.candidates
WHERE position_name ILIKE '%flutter%'
```

#### Result Columns
- `answers_json_question_title_1` → "Experience"
- `answers_json_value_text_1` → "5 years"
- `answers_json_question_title_2` → "Skills"
- `answers_json_value_text_2` → "Python, SQL"

#### Multiple JSON Fields
```sql
SELECT c.id, c.name, c.email
FROM public_marts.candidates c
WHERE c.status = 'active'
{{all_fields_as_columns_from(c.preferences, setting, value)}}
{{all_fields_as_columns_from(c.survey_responses, question, answer)}}
```

**Benefits:**
- ✅ No manual JSON parsing needed
- ✅ Automatic column naming
- ✅ Handles complex nested JSON structures
- ✅ Works with existing queries
- ✅ Backward compatible

### Parameters

**Required:**
- `spreadsheet_id`: Google Sheets spreadsheet ID
- One of: `sql` (inline SELECT) or `sql_cell` (A1 notation to read SQL from sheet)

**Optional:**
- `sheet_name` (default: `Data`)
- `starting_cell` (default: `F2`)
- `timestamp_cell`: write last-run ISO timestamp to this cell
- `status_cell`: write status/row count to this cell
- `row_limit` (default: 50000)
- `include_headers` (default: true)
- `value_input_option` (`RAW` or `USER_ENTERED`, default `RAW`)

### Real Examples

#### Example 1: Simple Export with Inline SQL
```
https://pg-query-output-to-gsheet-grz2olvbca-uc.a.run.app?spreadsheet_id=YOUR_SPREADSHEET_ID&sql=SELECT%20*%20FROM%20users%20WHERE%20active%20=%20true&sheet_name=ActiveUsers&starting_cell=A1
```

**Decoded URL:**
```
https://pg-query-output-to-gsheet-grz2olvbca-uc.a.run.app?
  spreadsheet_id=YOUR_SPREADSHEET_ID&
  sql=SELECT * FROM users WHERE active = true&
  sheet_name=ActiveUsers&
  starting_cell=A1
```

#### Example 2: Export with SQL from Sheet Cell (Recommended)
```
https://pg-query-output-to-gsheet-grz2olvbca-uc.a.run.app?spreadsheet_id=YOUR_SPREADSHEET_ID&sql_cell=Config!B1&sheet_name=Data&starting_cell=A2&timestamp_cell=Config!C1&status_cell=Config!D1
```

#### Example 3: Complex Query with All Options
```
https://pg-query-output-to-gsheet-grz2olvbca-uc.a.run.app?
  spreadsheet_id=YOUR_SPREADSHEET_ID&
  sql=SELECT%20u.id%2C%20u.name%2C%20u.email%2C%20p.title%20FROM%20users%20u%20JOIN%20profiles%20p%20ON%20u.id%20=%20p.user_id%20WHERE%20u.created_at%20%3E%20%272024-01-01%27&
  sheet_name=UserProfiles&
  starting_cell=A1&
  timestamp_cell=Config!C1&
  status_cell=Config!D1&
  row_limit=1000&
  include_headers=true&
  value_input_option=RAW
```

#### Example 4: JSON Unnesting - Export All Candidate Survey Data
```
https://pg-query-output-to-gsheet-grz2olvbca-uc.a.run.app?
  spreadsheet_id=YOUR_SPREADSHEET_ID&
  sql=SELECT%20*%20FROM%20public_marts.candidates%20WHERE%20position_name%20ILIKE%20%27%25flutter%25%27%20%7B%7Ball_fields_as_columns_from(answers_json%2C%20question_title%2C%20value_text)%7D%7D&
  sheet_name=CandidateSurveys&
  starting_cell=A1
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
https://pg-query-output-to-gsheet-grz2olvbca-uc.a.run.app?
  spreadsheet_id=YOUR_SPREADSHEET_ID&
  sql=SELECT%20c.id%2C%20c.name%2C%20c.email%20FROM%20public_marts.candidates%20c%20WHERE%20c.status%20%3D%20%27active%27%20%7B%7Ball_fields_as_columns_from(c.preferences%2C%20setting%2C%20value)%7D%7D%20%7B%7Ball_fields_as_columns_from(c.survey_responses%2C%20question%2C%20answer)%7D%7D&
  sheet_name=CandidateDetails&
  starting_cell=A1&
  include_headers=true
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

#### Example 6: JSON Unnesting with All Options
```
https://pg-query-output-to-gsheet-grz2olvbca-uc.a.run.app?
  spreadsheet_id=YOUR_SPREADSHEET_ID&
  sql=SELECT%20*%20FROM%20public_marts.candidates%20WHERE%20position_name%20ILIKE%20%27%25flutter%25%27%20%7B%7Ball_fields_as_columns_from(answers_json%2C%20question_title%2C%20value_text)%7D%7D&
  sheet_name=CandidateSurveys&
  starting_cell=A1&
  timestamp_cell=Config!C1&
  status_cell=Config!D1&
  row_limit=500&
  include_headers=true&
  value_input_option=RAW
```

### Google Sheets Setup Template

**Config Sheet (A1:D1):**
```
A1: https://pg-query-output-to-gsheet-grz2olvbca-uc.a.run.app
B1: SELECT * FROM users WHERE active = true
C1: (auto-filled timestamp)
D1: (auto-filled status)
```

**JSON Unnesting Config:**
```
A1: https://pg-query-output-to-gsheet-grz2olvbca-uc.a.run.app
B1: SELECT *, {{all_fields_as_columns_from(answers_json, question_title, value_text)}} FROM public_marts.candidates WHERE position_name ILIKE '%flutter%'
C1: (auto-filled timestamp)
D1: (auto-filled status)
```

**HYPERLINK Formula (put in A3):**
```
=HYPERLINK(
  A1
  & "?spreadsheet_id=" & ENCODEURL(REGEXEXTRACT(TO_TEXT(SPREADSHEET_URL()), "/d/([^/]+)"))
  & "&sheet_name=" & ENCODEURL("Data")
  & "&starting_cell=" & ENCODEURL("A2")
  & "&sql_cell=" & ENCODEURL("Config!B1")
  & "&timestamp_cell=" & ENCODEURL("Config!C1")
  & "&status_cell=" & ENCODEURL("Config!D1"),
  "🚀 Export Data"
)
```

### Response Format
```json
{
  "status": "ok",
  "rows": 150,
  "duration_ms": 1240
}
```

## 📥 Function 2: Import Google Sheets Data to Postgres

### Overview
Reads data from Google Sheets and loads it into Neon Postgres using a **fixed 3-column structure**: `entity_id`, `data` (JSONB), `loaded_at_utc`.

### Parameters

**Required:**
- `spreadsheet_id`: Google Sheets spreadsheet ID
- `sheet_name`: Sheet tab name to read from
- `id_field`: Column name to use as entity identifier
- `export_fields`: Comma-separated list of fields to export as JSON data
- `target_schema`: Postgres schema name (auto-created if missing)
- `target_table`: Postgres table name

**Optional:**
- `sheet_range`: A1 notation range (default: `<sheet_name>!A1:Z1000`)

### Real Examples

#### Example 1: Basic Import
```
https://gsheet-to-database-grz2olvbca-uc.a.run.app?spreadsheet_id=YOUR_SPREADSHEET_ID&sheet_name=Data&id_field=candidate_email&export_fields=candidate_status,position_name,notes&target_schema=google_sheets_source&target_table=candidate_updates
```

#### Example 2: Import with Custom Range
```
https://gsheet-to-database-grz2olvbca-uc.a.run.app?
  spreadsheet_id=YOUR_SPREADSHEET_ID&
  sheet_name=Manual%20Updates&
  id_field=user_id&
  export_fields=status,priority,comments&
  target_schema=manual_updates&
  target_table=user_status_changes&
  sheet_range=Manual%20Updates!A1:F100
```

#### Example 3: Live Test (Working Example)
```
https://gsheet-to-database-grz2olvbca-uc.a.run.app?
  spreadsheet_id=12fFS6Z_9vkba66850fTnmty1VdXcBi_Anyu8Xni6r7w&
  sheet_name=Test%20Data&
  id_field=candidate_email&
  export_fields=candidate_status&
  target_schema=google_sheet_source&
  target_table=test_export_data
```

### Google Sheets Setup for Import

**Test Data Structure:**
```
| candidate_email              | candidate_status | position_name        | notes                    |
|------------------------------|------------------|---------------------|--------------------------|
| test_no_comments@gmail.com   | 0               | Flutter Engineer    | Great technical skills   |
| test_with_comments@gmail.com | 1               | Flutter Engineer    | Needs more experience    |
```

**HYPERLINK Formula for Import:**
```
=HYPERLINK(
  "https://gsheet-to-database-grz2olvbca-uc.a.run.app"
  & "?spreadsheet_id=" & ENCODEURL(REGEXEXTRACT(TO_TEXT(SPREADSHEET_URL()), "/d/([^/]+)"))
  & "&sheet_name=" & ENCODEURL("Data")
  & "&id_field=" & ENCODEURL("candidate_email")
  & "&export_fields=" & ENCODEURL("candidate_status,position_name,notes")
  & "&target_schema=" & ENCODEURL("google_sheets_source")
  & "&target_table=" & ENCODEURL("candidate_updates"),
  "📥 Import to Database"
)
```

### Database Table Structure

The function creates tables with this **fixed structure**:
```sql
CREATE TABLE "schema"."table" (
  "entity_id" text NOT NULL,
  "data" jsonb NOT NULL,
  "loaded_at_utc" timestamptz NOT NULL
);
```

### Example Data in Database

**Input (Google Sheets):**
```
| candidate_email              | candidate_status | position_name        |
|------------------------------|------------------|---------------------|
| john@example.com             | 1               | Senior Developer    |
| jane@example.com             | 0               | Junior Developer    |
```

**Output (Postgres):**
```sql
-- Row 1
entity_id: "john@example.com"
data: {"candidate_status": "1", "position_name": "Senior Developer"}
loaded_at_utc: "2024-01-15T10:30:00.123Z"

-- Row 2
entity_id: "jane@example.com"
data: {"candidate_status": "0", "position_name": "Junior Developer"}
loaded_at_utc: "2024-01-15T10:30:00.123Z"
```

### Response Format
```json
{
  "status": "ok",
  "inserted_rows": 25,
  "duration_ms": 1240,
  "target_table": "google_sheets_source.candidate_updates",
  "missing_fields": [],
  "id_field": "candidate_email",
  "export_fields": ["candidate_status", "position_name", "notes"]
}
```

## 🔄 Complete Workflow Example

### Step 1: Export Data from Postgres to Sheets
```
https://pg-query-output-to-gsheet-grz2olvbca-uc.a.run.app?
  spreadsheet_id=YOUR_SPREADSHEET_ID&
  sql=SELECT%20candidate_email%2C%20candidate_status%2C%20position_name%20FROM%20candidates%20WHERE%20status%20=%20%27pending%27&
  sheet_name=Manual%20Review&
  starting_cell=A1&
  include_headers=true
```

### Step 2: Manual Review in Google Sheets
Users can edit the data in the spreadsheet.

### Step 3: Import Updated Data Back to Postgres
```
https://gsheet-to-database-grz2olvbca-uc.a.run.app?
  spreadsheet_id=YOUR_SPREADSHEET_ID&
  sheet_name=Manual%20Review&
  id_field=candidate_email&
  export_fields=candidate_status,position_name&
  target_schema=manual_reviews&
  target_table=updated_candidates
```

## 🛠️ Practical Use Cases

### 1. Candidate Status Updates
**Export pending candidates → Manual review → Import status updates**

### 2. Data Quality Review
**Export flagged records → Manual correction → Import clean data**

### 3. Bulk Data Entry
**Export template → Fill data → Import to database**

### 4. Approval Workflows
**Export pending items → Review/approve → Import decisions**

### 5. Survey Data Analysis (NEW)
**Export candidate survey responses with JSON unnesting:**
```sql
SELECT *,
       {{all_fields_as_columns_from(answers_json, question_title, value_text)}}
FROM public_marts.candidates
WHERE position_name ILIKE '%flutter%'
```
**Result:** Individual columns for each survey question and answer, perfect for analysis dashboards.

### 6. User Preferences Export (NEW)
**Export user preferences and settings with JSON unnesting:**
```sql
SELECT u.id, u.name, u.email
FROM users u
{{all_fields_as_columns_from(u.preferences, setting, value)}}
WHERE u.status = 'active'
```
**Result:** Flattened user preferences as separate columns for reporting.

## 🔧 Troubleshooting

### Common Issues

1. **403 Forbidden on Sheets API**
   - Share the spreadsheet with the runtime service account
   - Check IAM permissions

2. **Empty Results**
   - Verify SQL query works in your database
   - Check `status_cell` for error details
   - Ensure sheet has data below header row

3. **Missing Columns**
   - Check column names match sheet headers (case-insensitive)
   - Verify `export_fields` parameter

4. **URL Too Long**
   - Use `sql_cell` parameter instead of `sql`
   - Store SQL in a cell and reference it

5. **JSON Unnesting Issues**
   - Verify JSON column exists and contains valid JSON arrays
   - Check that `name_key` and `value_key` match actual JSON field names
   - Ensure JSON structure is consistent across rows

### Debug Tips

1. **Test SQL First**: Run your query directly in your database
2. **Check Sheet Access**: Ensure service account has access
3. **Verify Parameters**: Double-check all required parameters
4. **Use Status Cells**: Add `timestamp_cell` and `status_cell` for debugging
5. **Test JSON Unnesting**: Start with a simple JSON unnesting query before adding complexity

## 🔐 Security Notes

- Functions are IAM-protected by default
- No public access tokens needed
- Read-only queries enforced (SELECT only)
- Connection strings stored in Secret Manager
- All data validated before processing

## 📝 Best Practices

1. **Use `sql_cell` for long queries** to avoid URL length limits
2. **Always include status cells** for monitoring
3. **Test with small datasets first**
4. **Use descriptive schema and table names**
5. **Set appropriate row limits** for large exports
6. **Share spreadsheets with service account** before testing

### JSON Unnesting Best Practices

7. **Start simple**: Begin with basic JSON unnesting before complex queries
8. **Validate JSON structure**: Ensure consistent field names across all JSON objects
9. **Use meaningful keys**: Choose `name_key` and `value_key` that clearly describe the data
10. **Test incrementally**: Add JSON unnesting to existing queries one piece at a time
11. **Monitor performance**: JSON unnesting can impact query performance with large datasets
12. **Use multiple fields wisely**: Multiple `{{...}}` syntax is supported but test thoroughly
