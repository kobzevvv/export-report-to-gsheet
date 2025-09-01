# CI/CD Setup for Google Cloud Functions

This document explains the automated CI/CD pipeline for the Google Sheets to Database export system.

## Overview

The CI/CD pipeline automatically:
1. **Deploys** both cloud functions when code changes are pushed
2. **Tests** the deployed functions using the public test sheet
3. **Validates** that the functions work correctly before marking the deployment as successful

## Pipeline Components

### 1. GitHub Actions Workflow
- **File**: `.github/workflows/deploy-and-test.yml`
- **Triggers**: Push to `main` branch or pull requests
- **Scope**: Only runs when cloud function code changes

### 2. Automated Testing
- **Test Sheet**: Public Google Sheet with known test data
- **Test Cases**: 
  - Import function: Tests data import from Google Sheets to PostgreSQL
  - Export function: Tests data export from PostgreSQL to Google Sheets
- **Validation**: Checks for success responses and proper data handling

### 3. Environment Management
- **Secrets**: All sensitive data stored in GitHub secrets
- **Credentials**: Automatic authentication using service accounts
- **Database**: Uses the same Neon PostgreSQL database for testing

## Setup Instructions

### 1. Configure GitHub Secrets

Add the following secrets to your GitHub repository:

```bash
# Run the setup script to gather information
./scripts/setup-github-secrets.sh
```

Required secrets:
- `GCP_SA_KEY`: Google Cloud service account JSON key
- `GCP_PROJECT_ID`: Your Google Cloud project ID
- `NEON_DATABASE_URL`: PostgreSQL connection string
- `GOOGLE_APPLICATION_CREDENTIALS_JSON`: Google Sheets API credentials

### 2. Service Account Permissions

The service account needs these roles:
- Cloud Functions Admin
- Service Account User
- Storage Admin (if using Cloud Storage)

### 3. Test Environment

The pipeline uses a public test Google Sheet:
- **URL**: https://docs.google.com/spreadsheets/d/12fFS6Z_9vkba66850fTnmty1VdXcBi_Anyu8Xni6r7w/edit
- **Sheet Name**: "Test Data"
- **Test Data**: 2 rows with candidate information

## Pipeline Flow

### 1. Code Push
```bash
git push origin main
```

### 2. Automatic Deployment
- Detects changes in cloud function directories
- Deploys only the changed functions
- Sets up environment variables and permissions

### 3. Automated Testing
- Waits for deployment to complete
- Tests import function with test sheet
- Tests export function with sample query
- Validates response format and success indicators

### 4. Success/Failure Reporting
- ✅ **Success**: Function deployed and tested successfully
- ❌ **Failure**: Detailed error messages and logs
- ⚠️ **Warning**: Unexpected response format

## Test Validation

### Import Function Test
```bash
curl "https://gsheet-to-database-grz2olvbca-uc.a.run.app?spreadsheet_id=12fFS6Z_9vkba66850fTnmty1VdXcBi_Anyu8Xni6r7w&sheet_name=Test%20Data&id_field=candidate_email&export_fields=candidate_status&target_schema=google_sheet_source&target_table=test_export_data"
```

**Expected Success Response:**
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

### Export Function Test
```bash
curl "https://pg-query-output-to-gsheet-grz2olvbca-uc.a.run.app?sql=SELECT%20entity_id%2C%20data%2C%20loaded_at_utc%20FROM%20google_sheet_source.test_export_data%20ORDER%20BY%20loaded_at_utc%20DESC&spreadsheet_id=12fFS6Z_9vkba66850fTnmty1VdXcBi_Anyu8Xni6r7w&sheet_name=Test%20Data&starting_cell=F1&include_headers=true"
```

**Expected Success Response:**
```json
{
  "status": "ok",
  "rows": 2,
  "duration_ms": 3705
}
```

## Benefits

### 1. **Automated Quality Assurance**
- Every deployment is automatically tested
- Catches issues before they reach production
- Validates both functions work together

### 2. **Consistent Deployments**
- Same deployment process every time
- No manual intervention required
- Reduces human error

### 3. **Fast Feedback**
- Immediate notification of deployment status
- Detailed logs for debugging
- Clear success/failure indicators

### 4. **Production Safety**
- Tests use real database and Google Sheets
- Validates end-to-end functionality
- Ensures data integrity

## Monitoring

### GitHub Actions Tab
- View deployment status
- Check test results
- Review detailed logs

### Google Cloud Console
- Monitor function performance
- Check error rates
- View execution logs

### Database Monitoring
- Verify data imports
- Check table creation
- Monitor query performance

## Troubleshooting

### Common Issues

1. **Authentication Failed**
   - Check `GCP_SA_KEY` secret format
   - Verify service account permissions
   - Ensure project ID is correct

2. **Function Deployment Failed**
   - Check Google Cloud quotas
   - Verify API enablement
   - Review build logs

3. **Test Failed**
   - Check test sheet accessibility
   - Verify database connection
   - Review function logs

4. **Database Connection Failed**
   - Check `NEON_DATABASE_URL` format
   - Verify database accessibility
   - Check network connectivity

### Debug Steps

1. **Check GitHub Actions Logs**
   - Go to Actions tab in GitHub
   - Click on failed workflow
   - Review step-by-step logs

2. **Test Functions Manually**
   - Use the test commands from this document
   - Verify individual function behavior
   - Check response formats

3. **Verify Secrets**
   - Run the setup script
   - Check secret values in GitHub
   - Test credentials manually

## Best Practices

### 1. **Secret Management**
- Rotate credentials regularly
- Use least-privilege permissions
- Monitor secret usage

### 2. **Testing**
- Keep test data up to date
- Add new test cases for new features
- Monitor test reliability

### 3. **Deployment**
- Deploy during low-traffic periods
- Monitor function performance after deployment
- Have rollback plan ready

### 4. **Documentation**
- Update this document when making changes
- Document new test cases
- Keep troubleshooting guide current
