### Deployment Guide (Cloud Functions Gen2)

This guide covers deployment options for both functions:
1. `pg_query_output_to_gsheet` - Export from Postgres to Sheets
2. `gsheet_to_database` - Import from Sheets to Postgres

## Deployment Options

### Option 1: Automated CI/CD (Recommended)
The repository includes a GitHub Actions workflow that automatically deploys and tests functions when changes are pushed to the `main` branch.

**Setup:**
1. Configure GitHub secrets (see [GitHub Secrets Setup](GITHUB_SECRETS_SETUP.md))
2. Push changes to `main` branch
3. Monitor the Actions tab for deployment status

**Benefits:**
- Automatic deployment on code changes
- Built-in testing with the public test sheet
- No manual intervention required
- Consistent deployment process

### Option 2: Manual CLI Deployment
For manual deployment or local development:

#### 1) Set project
```bash
gcloud config set project <YOUR_PROJECT_ID>
```

#### 2) Enable required APIs
```bash
gcloud services enable \
  secretmanager.googleapis.com \
  cloudfunctions.googleapis.com \
  run.googleapis.com \
  artifactregistry.googleapis.com \
  cloudbuild.googleapis.com \
  sheets.googleapis.com
```

#### 3) Provide NEON_DATABASE_URL

- Option A (recommended): Secret Manager
```bash
printf '<NEON_URL>' | gcloud secrets create NEON_DATABASE_URL --data-file=-
```

- Option B (quick test): Local env var
Create a file `env` in repo root with:
```
NEON_DATABASE_URL=postgresql://...sslmode=require
```
Then:
```bash
set -a; . ./env; set +a
```

#### 4) Deploy both functions

**Export function (Postgres → Sheets):**
```bash
gcloud functions deploy pg_query_output_to_gsheet \
  --gen2 --region=us-central1 --runtime=python311 \
  --source=/Users/vova/Documents/GitHub/export-report-to-gsheet/cloud_function \
  --entry-point=pg_query_output_to_gsheet \
  --trigger-http --allow-unauthenticated \
  --set-env-vars=NEON_DATABASE_URL="$NEON_DATABASE_URL"
```

**Import function (Sheets → Postgres):**
```bash
gcloud functions deploy gsheet_to_database \
  --gen2 --region=us-central1 --runtime=python311 \
  --source=/Users/vova/Documents/GitHub/export-report-to-gsheet/cloud_function_gsheet_to_database \
  --entry-point=gsheet_to_database \
  --trigger-http --allow-unauthenticated \
  --set-env-vars=NEON_DATABASE_URL="$NEON_DATABASE_URL"
```

#### 5) Make functions publicly callable (already done with --allow-unauthenticated)

The functions are deployed with public access. If needed, you can also grant explicit public invoker:

```bash
# Export function
gcloud run services add-iam-policy-binding pg-query-output-to-gsheet \
  --region=us-central1 \
  --member=allUsers \
  --role=roles/run.invoker

# Import function  
gcloud run services add-iam-policy-binding gsheet-to-database \
  --region=us-central1 \
  --member=allUsers \
  --role=roles/run.invoker
```

#### 6) Get function URLs
```bash
echo "Export (DB→Sheets):"
gcloud functions describe pg_query_output_to_gsheet \
  --region=us-central1 \
  --format='value(serviceConfig.uri)'

echo "Import (Sheets→DB):"
gcloud functions describe gsheet_to_database \
  --region=us-central1 \
  --format='value(serviceConfig.uri)'
```

#### 8) Test After Deployment

**Automated Testing with Test Sheet:**
```bash
# Test the import function with the public test sheet
curl "https://gsheet-to-database-grz2olvbca-uc.a.run.app?spreadsheet_id=12fFS6Z_9vkba66850fTnmty1VdXcBi_Anyu8Xni6r7w&sheet_name=Test%20Data&id_field=candidate_email&export_fields=candidate_status&target_schema=google_sheet_source&target_table=test_export_data"
```

**Expected Response:**
```json
{
  "status": "ok",
  "inserted_rows": 2,
  "duration_ms": 1200,
  "target_table": "google_sheet_source.test_export_data",
  "missing_fields": [],
  "id_field": "candidate_email",
  "export_fields": ["candidate_status"]
}
```

**Test Sheet**: [https://docs.google.com/spreadsheets/d/12fFS6Z_9vkba66850fTnmty1VdXcBi_Anyu8Xni6r7w/edit](https://docs.google.com/spreadsheets/d/12fFS6Z_9vkba66850fTnmty1VdXcBi_Anyu8Xni6r7w/edit)

**Test Export Function:**
```bash
# Test the export function with the test data
curl "https://pg-query-output-to-gsheet-grz2olvbca-uc.a.run.app?sql=SELECT%20entity_id%2C%20data%2C%20loaded_at_utc%20FROM%20google_sheet_source.test_export_data%20ORDER%20BY%20loaded_at_utc%20DESC&spreadsheet_id=12fFS6Z_9vkba66850fTnmty1VdXcBi_Anyu8Xni6r7w&sheet_name=Test%20Data&starting_cell=F1&include_headers=true"
```

**Expected Export Response:**
```json
{
  "status": "ok",
  "rows": 2,
  "duration_ms": 3705
}
```

#### 9) Common issues

- 403 forbidden: grant public invoker (step 5) or ensure your user has `roles/run.invoker`.
- Sheets write 403: share the spreadsheet with the function's runtime service account.
- Missing NEON_DATABASE_URL: set via secret or env.


