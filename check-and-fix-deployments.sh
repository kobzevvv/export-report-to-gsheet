#!/bin/bash

# Check and Fix Stuck Deployments
# This script helps resolve 409 deployment conflicts

set -euo pipefail

echo "🔍 Checking for Stuck Deployments"
echo "================================="

# Get current project ID
PROJECT_ID=$(gcloud config get-value project)
if [ -z "$PROJECT_ID" ]; then
    echo "❌ No project set. Run: gcloud config set project YOUR_PROJECT_ID"
    exit 1
fi

REGION="us-central1"
FUNCTION_NAME="pg_query_output_to_gsheet"

echo "📋 Project: $PROJECT_ID"
echo "📋 Region: $REGION"
echo "📋 Function: $FUNCTION_NAME"
echo ""

# Check for existing Cloud Builds
echo "1. Checking for active Cloud Builds..."
BUILDS=$(gcloud builds list --region=$REGION --filter="status=(WORKING OR QUEUED OR PENDING)" --format="value(id)" 2>/dev/null || echo "")

if [ -n "$BUILDS" ]; then
    echo "   ⚠️  Found active/pending builds:"
    for BUILD in $BUILDS; do
        BUILD_STATUS=$(gcloud builds describe $BUILD --region=$REGION --format="value(status)" 2>/dev/null || echo "UNKNOWN")
        BUILD_TIME=$(gcloud builds describe $BUILD --region=$REGION --format="value(createTime)" 2>/dev/null || echo "UNKNOWN")
        echo "   - Build ID: $BUILD (Status: $BUILD_STATUS, Created: $BUILD_TIME)"
    done
    echo ""
    echo "   ❓ Cancel these builds? (y/n)"
    read -r response
    if [[ $response == "y" || $response == "Y" ]]; then
        for BUILD in $BUILDS; do
            echo "   🛑 Cancelling build: $BUILD"
            if gcloud builds cancel $BUILD --region=$REGION --quiet; then
                echo "     ✅ Successfully cancelled $BUILD"
            else
                echo "     ⚠️  Failed to cancel $BUILD"
            fi
        done
        echo "   ⏳ Waiting for builds to be cancelled..."
        sleep 30
    fi
else
    echo "   ✅ No active builds found"
fi

echo ""

# Check function status
echo "2. Checking Cloud Function status..."
FUNCTION_EXISTS=$(gcloud functions describe $FUNCTION_NAME --region=$REGION --format="value(name)" 2>/dev/null || echo "")

if [ -n "$FUNCTION_EXISTS" ]; then
    echo "   📋 Function exists: $FUNCTION_NAME"

    # Get detailed function information
    STATE=$(gcloud functions describe $FUNCTION_NAME --region=$REGION --format="value(state)" 2>/dev/null || echo "UNKNOWN")
    UPDATE_TIME=$(gcloud functions describe $FUNCTION_NAME --region=$REGION --format="value(updateTime)" 2>/dev/null || echo "UNKNOWN")
    REVISION=$(gcloud functions describe $FUNCTION_NAME --region=$REGION --format="value(serviceConfig.revision)" 2>/dev/null || echo "UNKNOWN")

    echo "   📋 Current state: $STATE"
    echo "   📋 Last updated: $UPDATE_TIME"
    echo "   📋 Current revision: $REVISION"

    if [ "$STATE" != "ACTIVE" ]; then
        echo "   ⚠️  Function is not in ACTIVE state (current: $STATE)"
        echo "   💡 This might be causing the 409 conflict"
        echo ""
        echo "   ❓ Delete and recreate the function? (y/n)"
        read -r response
        if [[ $response == "y" || $response == "Y" ]]; then
            echo "   🗑️  Deleting function..."
            if gcloud functions delete $FUNCTION_NAME --region=$REGION --quiet; then
                echo "   ✅ Function deleted successfully. Next deployment will recreate it."
                echo "   ⏳ Waiting for deletion to complete..."
                sleep 30
            else
                echo "   ⚠️  Failed to delete function. You may need to delete it manually from the Cloud Console."
            fi
        fi
    else
        echo "   ✅ Function is ACTIVE"
    fi
else
    echo "   📋 Function does not exist yet (this is normal for first deployment)"
fi

echo ""
echo "✅ Deployment conflict check complete!"
echo ""
echo "🚀 Next steps:"
echo "1. Ensure GitHub secrets are set (GCP_REGION, FUNCTION_NAME, ALLOW_UNAUTHENTICATED)"
echo "2. Run ./fix-iam-permissions.sh to fix permissions"
echo "3. Wait 2-3 minutes, then trigger a new deployment"
