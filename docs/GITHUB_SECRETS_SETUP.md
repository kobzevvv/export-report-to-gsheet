# GitHub Secrets Setup for CI/CD

This document explains how to configure the required GitHub secrets for the automated CI/CD workflow.

## Required Secrets

The following secrets need to be configured in your GitHub repository:

### 1. GCP_SA_KEY
**Purpose**: Service Account key for Google Cloud authentication
**Format**: JSON file content (as string)

**How to get it:**
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Navigate to IAM & Admin > Service Accounts
3. Create a new service account or use existing one
4. Grant the following roles:
   - Cloud Functions Admin
   - Service Account User
   - Storage Admin (if using Cloud Storage)
5. Create a JSON key for the service account
6. Copy the entire JSON content

**How to set in GitHub:**
1. Go to your repository on GitHub
2. Navigate to Settings > Secrets and variables > Actions
3. Click "New repository secret"
4. Name: `GCP_SA_KEY`
5. Value: Paste the entire JSON content

### 2. GCP_PROJECT_ID
**Purpose**: Your Google Cloud Project ID
**Format**: String (e.g., `my-project-123456`)

**How to get it:**
1. In Google Cloud Console, the Project ID is shown in the project selector at the top
2. Or run: `gcloud config get-value project`

**How to set in GitHub:**
1. Go to Settings > Secrets and variables > Actions
2. Click "New repository secret"
3. Name: `GCP_PROJECT_ID`
4. Value: Your project ID

### 3. NEON_DATABASE_URL
**Purpose**: Database connection string for Neon PostgreSQL
**Format**: PostgreSQL connection string

**Example:**
```
postgresql://neondb_owner:password@ep-aged-mouse-ab3hsik6-pooler.eu-west-2.aws.neon.tech/neondb?sslmode=require&channel_binding=require
```

**How to set in GitHub:**
1. Go to Settings > Secrets and variables > Actions
2. Click "New repository secret"
3. Name: `NEON_DATABASE_URL`
4. Value: Your database connection string

### 4. GOOGLE_APPLICATION_CREDENTIALS_JSON
**Purpose**: Google Sheets API credentials for the export function
**Format**: JSON file content (as string)

**How to get it:**
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Navigate to APIs & Services > Credentials
3. Create credentials > Service Account
4. Download the JSON key file
5. Copy the entire JSON content

**How to set in GitHub:**
1. Go to Settings > Secrets and variables > Actions
2. Click "New repository secret"
3. Name: `GOOGLE_APPLICATION_CREDENTIALS_JSON`
4. Value: Paste the entire JSON content

## Security Best Practices

1. **Never commit secrets to code**: All sensitive information should be stored in GitHub secrets
2. **Rotate keys regularly**: Periodically regenerate service account keys
3. **Principle of least privilege**: Only grant necessary permissions to service accounts
4. **Monitor usage**: Regularly check Cloud Console for unusual activity

## Testing the Setup

Once all secrets are configured:

1. Make a small change to either cloud function
2. Push to the `main` branch
3. Check the Actions tab in GitHub to see the workflow running
4. Verify that both deployment and testing steps complete successfully

## Troubleshooting

### Common Issues

1. **Authentication failed**: Check that `GCP_SA_KEY` contains valid JSON
2. **Permission denied**: Ensure service account has required roles
3. **Function deployment failed**: Verify `GCP_PROJECT_ID` is correct
4. **Database connection failed**: Check `NEON_DATABASE_URL` format
5. **Google Sheets API failed**: Verify `GOOGLE_APPLICATION_CREDENTIALS_JSON`

### Debug Steps

1. Check the Actions logs for detailed error messages
2. Verify all secrets are set correctly in GitHub
3. Test the functions manually using the URLs from the deployment logs
4. Check Google Cloud Console for any quota or permission issues
