#!/bin/bash

# Fix IAM Permissions for Cloud Functions Deployment
# Run this script to grant the necessary permissions

set -euo pipefail

echo "🔧 Fixing IAM Permissions for Cloud Functions Deployment"
echo "======================================================="

# Get current project ID
PROJECT_ID=$(gcloud config get-value project)
if [ -z "$PROJECT_ID" ]; then
    echo "❌ No project set. Run: gcloud config set project YOUR_PROJECT_ID"
    exit 1
fi

echo "📋 Project ID: $PROJECT_ID"

# Get project number
PROJECT_NUMBER=$(gcloud projects describe $PROJECT_ID --format="value(projectNumber)")
echo "📋 Project Number: $PROJECT_NUMBER"

# Define the compute service account
COMPUTE_SA="${PROJECT_NUMBER}-compute@developer.gserviceaccount.com"
echo "📋 Compute Service Account: $COMPUTE_SA"

echo ""
echo "🔑 Granting necessary IAM roles..."

# Grant Cloud Build Service Account role
echo "1. Granting roles/cloudbuild.builds.builder to compute service account..."
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:${COMPUTE_SA}" \
    --role="roles/cloudbuild.builds.builder" \
    --quiet

# Grant additional roles needed for Cloud Functions
echo "2. Granting roles/cloudfunctions.developer to compute service account..."
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:${COMPUTE_SA}" \
    --role="roles/cloudfunctions.developer" \
    --quiet

echo "3. Granting roles/run.developer to compute service account..."
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:${COMPUTE_SA}" \
    --role="roles/run.developer" \
    --quiet

echo "4. Granting roles/storage.admin to compute service account..."
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:${COMPUTE_SA}" \
    --role="roles/storage.admin" \
    --quiet

echo ""
echo "✅ IAM permissions configured successfully!"
echo ""
echo "🚀 Next steps:"
echo "1. Add the missing GitHub secrets:"
echo "   - GCP_REGION = us-central1"
echo "   - FUNCTION_NAME = pg_query_output_to_gsheet" 
echo "   - ALLOW_UNAUTHENTICATED = true"
echo "2. Wait for any existing deployments to complete"
echo "3. Trigger a new deployment by pushing to main"
