# Complete Documentation with Real Examples

This document provides comprehensive examples for both Cloud Functions based on the actual deployed code.

## 🚀 Function URLs (Live)

- **Export (Postgres → Sheets)**: `https://pg-query-output-to-gsheet-grz2olvbca-uc.a.run.app`
- **Import (Sheets → Postgres)**: `https://gsheet-to-database-grz2olvbca-uc.a.run.app`

## 📊 Function 1: Export Postgres Data to Google Sheets

### Overview
Executes SELECT queries against Neon Postgres and writes results to Google Sheets.

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

### Google Sheets Setup Template

**Config Sheet (A1:D1):**
```
A1: https://pg-query-output-to-gsheet-grz2olvbca-uc.a.run.app
B1: SELECT * FROM users WHERE active = true
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

### Debug Tips

1. **Test SQL First**: Run your query directly in your database
2. **Check Sheet Access**: Ensure service account has access
3. **Verify Parameters**: Double-check all required parameters
4. **Use Status Cells**: Add `timestamp_cell` and `status_cell` for debugging

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
