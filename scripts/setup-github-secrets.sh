#!/bin/bash

# GitHub Secrets Setup Helper Script
# This script helps you gather the information needed to set up GitHub secrets

echo "🔐 GitHub Secrets Setup Helper"
echo "=============================="
echo ""

# Check if gcloud is installed and authenticated
if ! command -v gcloud &> /dev/null; then
    echo "❌ gcloud CLI not found. Please install it first."
    exit 1
fi

echo "📋 Gathering information for GitHub secrets..."
echo ""

# Get GCP Project ID
echo "1. GCP_PROJECT_ID:"
PROJECT_ID=$(gcloud config get-value project 2>/dev/null)
if [ -n "$PROJECT_ID" ]; then
    echo "   ✅ Found: $PROJECT_ID"
else
    echo "   ❌ No project set. Run: gcloud config set project YOUR_PROJECT_ID"
fi
echo ""

# Check for service account key
echo "2. GCP_SA_KEY:"
if [ -f "GBQ_CREDS.JSON" ]; then
    echo "   ✅ Found: GBQ_CREDS.JSON"
    echo "   📝 Copy the entire contents of this file for the GCP_SA_KEY secret"
else
    echo "   ❌ GBQ_CREDS.JSON not found"
    echo "   📝 Create a service account key and save it as GBQ_CREDS.JSON"
fi
echo ""

# Check for database URL
echo "3. NEON_DATABASE_URL:"
if [ -n "$NEON_DATABASE_URL" ]; then
    echo "   ✅ Found in environment"
    echo "   📝 Use this value for the NEON_DATABASE_URL secret"
else
    echo "   ❌ NEON_DATABASE_URL not set in environment"
    echo "   📝 Set your database connection string"
fi
echo ""

# Check for Google credentials
echo "4. GOOGLE_APPLICATION_CREDENTIALS_JSON:"
if [ -n "$GOOGLE_APPLICATION_CREDENTIALS" ] && [ -f "$GOOGLE_APPLICATION_CREDENTIALS" ]; then
    echo "   ✅ Found: $GOOGLE_APPLICATION_CREDENTIALS"
    echo "   📝 Copy the entire contents of this file for the GOOGLE_APPLICATION_CREDENTIALS_JSON secret"
else
    echo "   ❌ Google credentials not found"
    echo "   📝 Create Google Sheets API credentials and save as JSON"
fi
echo ""

echo "📖 Next Steps:"
echo "1. Go to your GitHub repository"
echo "2. Navigate to Settings > Secrets and variables > Actions"
echo "3. Add the following repository secrets:"
echo "   - GCP_PROJECT_ID: $PROJECT_ID"
echo "   - GCP_SA_KEY: [contents of GBQ_CREDS.JSON]"
echo "   - NEON_DATABASE_URL: [your database URL]"
echo "   - GOOGLE_APPLICATION_CREDENTIALS_JSON: [contents of Google credentials JSON]"
echo ""
echo "📚 For detailed instructions, see: docs/GITHUB_SECRETS_SETUP.md"
