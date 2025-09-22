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

# Function to grant role with error handling
grant_role() {
    local role=$1
    local description=$2

    echo "📋 $description"
    if gcloud projects add-iam-policy-binding $PROJECT_ID \
        --member="serviceAccount:${COMPUTE_SA}" \
        --role="$role" \
        --quiet 2>/dev/null; then
        echo "   ✅ Granted $role"
    else
        echo "   ⚠️  Failed to grant $role (may already exist)"
    fi
}

# Grant Cloud Build Service Account role
grant_role "roles/cloudbuild.builds.builder" "Granting Cloud Build permissions to compute service account"

# Grant additional roles needed for Cloud Functions
grant_role "roles/cloudfunctions.developer" "Granting Cloud Functions developer permissions"
grant_role "roles/run.developer" "Granting Cloud Run developer permissions"
grant_role "roles/storage.admin" "Granting Storage admin permissions"
grant_role "roles/artifactregistry.reader" "Granting Artifact Registry read permissions"
grant_role "roles/serviceusage.serviceUsageConsumer" "Granting Service Usage consumer permissions"

# Verify the permissions were granted
echo ""
echo "🔍 Verifying permissions..."
PERMISSIONS=$(gcloud projects get-iam-policy $PROJECT_ID \
    --flatten="bindings[].members" \
    --filter="bindings.members:${COMPUTE_SA}" \
    --format="value(bindings.role)" 2>/dev/null || echo "")

if [[ -n "$PERMISSIONS" ]]; then
    echo "✅ Service account has the following roles:"
    echo "$PERMISSIONS" | sort | uniq
else
    echo "⚠️  Unable to verify permissions (check account has project viewer role)"
fi

echo ""
echo "✅ IAM permissions configuration complete!"
echo ""
echo "🚀 Next steps:"
echo "1. Add the missing GitHub secrets:"
echo "   - GCP_REGION = us-central1"
echo "   - FUNCTION_NAME = pg_query_output_to_gsheet" 
echo "   - ALLOW_UNAUTHENTICATED = true"
echo "2. Wait for any existing deployments to complete"
echo "3. Trigger a new deployment by pushing to main"
