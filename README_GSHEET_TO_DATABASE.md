### Google Sheets → Neon Postgres (Cloud Function)

The `gsheet_to_database` function exports data from Google Sheets to Neon Postgres using a **fixed 3-column structure**: ID, JSON data, and timestamp. This approach eliminates schema brittleness and provides maximum flexibility.

### Function URL
**Live URL**: `https://gsheet-to-database-grz2olvbca-uc.a.run.app`

### Parameters (query string)

**Required:**
- `spreadsheet_id`: Google Sheets spreadsheet ID
- `sheet_name`: Sheet tab name to read from
- `id_field`: Column name to use as entity identifier (e.g., "candidate_email")
- `export_fields`: Comma-separated list of fields to export as JSON data (e.g., "status,position,notes")
- `target_schema`: Postgres schema name (auto-created if missing)
- `target_table`: Postgres table name

**Optional:**
- `sheet_range`: A1 notation range (default: `<sheet_name>!A1:ZZZ1000000`)

### Column Format

**Simple (no renaming):**
```
columns=candidate_email,candidate_status,position_name
```

**With renaming:**
```
columns=candidate_email:email,candidate_status:status,position_name:job_title
```

**Mixed:**
```
columns=candidate_email,candidate_status:status,position_name
```

Format: `original_name:new_name` where `:new_name` is optional.

### Behavior

1. **Header Detection**: Auto-detects header row by matching column names (case-insensitive)
2. **Column Extraction**: Extracts only specified columns, renames if `original:new` format used
3. **Missing Columns**: Skipped with warning in status message
4. **Full Refresh**: Drops and recreates target table on each run
5. **Data Types**: All columns stored as `text`, plus auto-added `loaded_at_utc timestamptz`
6. **Schema Creation**: Auto-creates target schema if it doesn't exist

### Example Usage

**Google Sheets Link (put in cell F1):**
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

**Direct URL Example:**
```
https://gsheet-to-database-grz2olvbca-uc.a.run.app?spreadsheet_id=YOUR_SPREADSHEET_ID&sheet_name=Data&id_field=candidate_email&export_fields=candidate_status,position_name,notes&target_schema=google_sheets_source&target_table=candidate_updates
```

**Live Test URL (Working Example):**
```
https://gsheet-to-database-grz2olvbca-uc.a.run.app?spreadsheet_id=12fFS6Z_9vkba66850fTnmty1VdXcBi_Anyu8Xni6r7w&sheet_name=Test%20Data&id_field=candidate_email&export_fields=candidate_status&target_schema=google_sheet_source&target_table=test_export_data
```

### Response Format

**Success:**
```json
{
  "status": "ok",
  "inserted_rows": 25,
  "duration_ms": 1240,
  "target_table": "google_sheets_source.candidate_updates",
  "missing_columns": ["old_column_name"]
}
```

**Error:**
```json
{
  "error": "Missing required param: target_schema"
}
```

### Target Table Structure

The function creates tables with this structure:
```sql
CREATE TABLE "schema"."table" (
  "column1" text,
  "column2" text,
  -- ... your specified columns as text
  "loaded_at_utc" timestamptz NOT NULL
);
```

### Authentication

- **Public Access**: No authentication required
- **Sheets Access**: The spreadsheet must be shared with the runtime service account
- **Postgres Access**: Uses `NEON_DATABASE_URL` environment variable

### Common Use Cases

1. **Status Updates**: Import candidate status changes from recruiters
2. **Comments/Notes**: Sync reviewer comments back to database
3. **Data Corrections**: Allow manual data fixes via spreadsheet interface
4. **Bulk Updates**: Import large datasets with column mapping

### Troubleshooting

- **403 Forbidden**: Share the spreadsheet with the service account
- **Missing Columns**: Check column names match sheet headers (case-insensitive)
- **Empty Results**: Verify sheet has data below header row
- **SQL Errors**: Check target_schema and target_table are valid SQL identifiers

### Related Functions

- **Export**: Use `pg_query_output_to_gsheet` to export data from Postgres to Sheets
- See `README_GOOGLE_SHEETS_GCF.md` for export function documentation

### 🧪 Live Test Environment

**Test Google Sheet**: [https://docs.google.com/spreadsheets/d/12fFS6Z_9vkba66850fTnmty1VdXcBi_Anyu8Xni6r7w/edit](https://docs.google.com/spreadsheets/d/12fFS6Z_9vkba66850fTnmty1VdXcBi_Anyu8Xni6r7w/edit)

This public test sheet demonstrates the import function with real data:

**Test Data Structure:**
```
| candidate_email        | candidate_status | position        | notes                    |
|------------------------|------------------|-----------------|--------------------------|
| test_no_comments@gmail.com | 0              | Flutter Engineer| Great technical skills   |
| test_with_comments@gmail.com | 1           | Flutter Engineer| Needs more experience    |
```

**Test Formula (Ready to Use):**
```
=HYPERLINK(
  "https://gsheet-to-database-grz2olvbca-uc.a.run.app"
  & "?spreadsheet_id=" & "12fFS6Z_9vkba66850fTnmty1VdXcBi_Anyu8Xni6r7w"
  & "&sheet_name=" & ENCODEURL("Test Data")
  & "&id_field=" & ENCODEURL("candidate_email")
  & "&export_fields=" & ENCODEURL("candidate_status")
  & "&target_schema=" & ENCODEURL("google_sheet_source")
  & "&target_table=" & ENCODEURL("candididates_with_status_manual"),
  "🧪 Test Import"
)
```

**Expected Result:**
```sql
-- Row 1
entity_id: "test_no_comments@gmail.com"
data: {"candidate_status": "0", "position_name": "Flutter Engineer for Gauss"}
loaded_at_utc: "2024-01-15T10:30:00.123Z"

-- Row 2
entity_id: "test_with_comments@gmail.com"
data: {"candidate_status": "1", "position_name": "Flutter Engineer for Gauss"}
loaded_at_utc: "2024-01-15T10:30:00.123Z"
```

**How to Test:**
1. Open the test sheet
2. Copy the test formula above
3. Paste it in any cell
4. Click the generated link
5. Check your database for the new table `google_sheet_source.test_candidates`

**Perfect for:**
- Testing function changes after deployment
- Demonstrating the feature to stakeholders
- Debugging issues with real data
- Developer onboarding and training
