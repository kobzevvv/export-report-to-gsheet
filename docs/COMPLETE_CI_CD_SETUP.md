# Complete CI/CD Setup for Google Cloud Functions

This document provides a comprehensive overview of the automated CI/CD pipeline for both Google Cloud Functions in the export-report-to-gsheet project.

## 🎯 Overview

The CI/CD pipeline provides **complete automation** for:
1. **Import Function** (`gsheet_to_database`) - Google Sheets → PostgreSQL
2. **Export Function** (`pg_query_output_to_gsheet`) - PostgreSQL → Google Sheets

## 🔄 Pipeline Flow

### 1. **Automatic Triggering**
- **Push to `main` branch** triggers deployment
- **Smart detection** - only deploys functions that have changed
- **Pull request validation** - tests functions before merging

### 2. **Deployment Process**
- **Authentication** using GitHub secrets
- **Function deployment** with environment variables
- **Health checks** to ensure functions are active

### 3. **Automated Testing**
- **Import test** - Uses public test Google Sheet
- **Export test** - Queries test data from database
- **End-to-end validation** - Ensures both functions work together

## 🗄️ Database URL Management

### ✅ **Problem Solved**
- **No more manual database URL entry**
- **Secure storage** in GitHub secrets
- **Automatic deployment** with correct credentials

### 🔧 **Implementation**
- `NEON_DATABASE_URL` stored in GitHub secrets
- Automatically injected during deployment
- Same database used for both functions and testing

## 📊 Test Data Flow

### **Import → Export Cycle**
1. **Import test** imports data from Google Sheets to `google_sheet_source.test_export_data`
2. **Export test** queries the same table and exports to Google Sheets
3. **Complete validation** of the data pipeline

### **Test Data**
- **Source**: Public Google Sheet with candidate data
- **Target**: `google_sheet_source.test_export_data` table
- **Format**: Fixed 3-column structure (entity_id, data JSON, loaded_at_utc)

## 🚀 Setup Instructions

### 1. **Configure GitHub Secrets**
```bash
# Run the helper script
./scripts/setup-github-secrets.sh
```

Required secrets:
- `GCP_SA_KEY` - Google Cloud service account JSON
- `GCP_PROJECT_ID` - Your Google Cloud project ID
- `NEON_DATABASE_URL` - PostgreSQL connection string
- `GOOGLE_APPLICATION_CREDENTIALS_JSON` - Google Sheets API credentials

### 2. **Service Account Permissions**
- Cloud Functions Admin
- Service Account User
- Storage Admin (if using Cloud Storage)

### 3. **Test Environment**
- **Public test sheet**: https://docs.google.com/spreadsheets/d/12fFS6Z_9vkba66850fTnmty1VdXcBi_Anyu8Xni6r7w/edit
- **Sheet name**: "Test Data"
- **Test data**: 2 rows with candidate information

## 🧪 Test Validation

### **Import Function Test**
```bash
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

### **Export Function Test**
```bash
curl "https://pg-query-output-to-gsheet-grz2olvbca-uc.a.run.app?sql=SELECT%20entity_id%2C%20data%2C%20loaded_at_utc%20FROM%20google_sheet_source.test_export_data%20ORDER%20BY%20loaded_at_utc%20DESC&spreadsheet_id=12fFS6Z_9vkba66850fTnmty1VdXcBi_Anyu8Xni6r7w&sheet_name=Test%20Data&starting_cell=F1&include_headers=true"
```

**Expected Response:**
```json
{
  "status": "ok",
  "rows": 2,
  "duration_ms": 3705
}
```

## 📈 Benefits

### **1. Complete Automation**
- **No manual intervention** required
- **Consistent deployments** every time
- **Automatic testing** with real data

### **2. Quality Assurance**
- **End-to-end validation** of both functions
- **Real data testing** using public test sheet
- **Immediate feedback** on deployment success

### **3. Security & Reliability**
- **Secure credential management** via GitHub secrets
- **No hardcoded URLs** or sensitive data
- **Production-ready testing** environment

### **4. Developer Experience**
- **One-click deployment** via git push
- **Clear success/failure indicators**
- **Detailed logs** for debugging

## 🔍 Monitoring & Debugging

### **GitHub Actions Tab**
- View deployment status
- Check test results
- Review detailed logs

### **Google Cloud Console**
- Monitor function performance
- Check error rates
- View execution logs

### **Database Monitoring**
- Verify data imports
- Check table creation
- Monitor query performance

## 🛠️ Troubleshooting

### **Common Issues**

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

### **Debug Steps**

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

## 🎉 Success Criteria

### **Deployment Success**
- ✅ Functions deployed successfully
- ✅ Environment variables set correctly
- ✅ Functions are active and accessible

### **Test Success**
- ✅ Import function imports data correctly
- ✅ Export function exports data correctly
- ✅ End-to-end data flow validated

### **Quality Assurance**
- ✅ No errors in function logs
- ✅ Expected response formats
- ✅ Performance within acceptable limits

## 📚 Documentation

- **Setup Guide**: `docs/GITHUB_SECRETS_SETUP.md`
- **Deployment Guide**: `docs/DEPLOYMENT.md`
- **CI/CD Details**: `docs/CI_CD_SETUP.md`
- **Helper Script**: `scripts/setup-github-secrets.sh`

## 🚀 Next Steps

1. **Set up GitHub secrets** using the provided guides
2. **Push changes** to trigger the first automated deployment
3. **Monitor the Actions tab** to see the pipeline in action
4. **Enjoy automated deployments** with built-in testing!

The CI/CD pipeline now provides **complete automation** for both functions, eliminating the need for manual database URL entry and ensuring every deployment is thoroughly tested with real data.
