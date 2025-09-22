#!/usr/bin/env python3
"""
Check the deployment status of your cloud functions.
This helps verify if the functions are deployed and accessible.
"""

import os
import requests
from urllib.parse import urlencode

def check_function_deployment():
    """Check if cloud functions are deployed and accessible"""

    print("🔍 Cloud Function Deployment Status Check")
    print("=" * 50)

    # Try to get function URLs from environment or use defaults
    export_function_url = os.getenv('EXPORT_FUNCTION_URL', 'https://pg-query-output-to-gsheet-grz2olvbca-uc.a.run.app')
    import_function_url = os.getenv('IMPORT_FUNCTION_URL', 'https://gsheet-to-database-grz2olvbca-uc.a.run.app')

    print(f"📊 Export Function URL: {export_function_url}")
    print(f"📊 Import Function URL: {import_function_url}")
    print()

    # Test URLs
    test_urls = [
        (export_function_url, "Export Function (DB→Sheets)"),
        (import_function_url, "Import Function (Sheets→DB)"),
    ]

    for url, name in test_urls:
        print(f"🧪 Testing {name}:")
        print(f"   URL: {url}")

        try:
            # Simple HEAD request to check if function is accessible
            response = requests.head(url, timeout=10)
            print(f"   ✅ Function is accessible (Status: {response.status_code})")

            if response.status_code == 200:
                print("   ✅ Function is responding correctly")
            elif response.status_code == 403:
                print("   ❌ Function is deployed but access forbidden")
                print("   💡 This suggests a permission issue")
            elif response.status_code == 404:
                print("   ❌ Function not found")
                print("   💡 This suggests deployment failed")
            else:
                print(f"   ⚠️  Unexpected status: {response.status_code}")

        except requests.exceptions.Timeout:
            print("   ❌ Function timed out")
            print("   💡 This suggests the function is not responding")
        except requests.exceptions.ConnectionError:
            print("   ❌ Cannot connect to function")
            print("   💡 This suggests the function is not deployed or URL is wrong")
        except Exception as e:
            print(f"   ❌ Error: {e}")

        print()

def check_google_cloud_console():
    """Provide instructions for checking Google Cloud Console"""

    print("🔧 Manual Checks in Google Cloud Console:")
    print("-" * 40)
    print("1. Go to: https://console.cloud.google.com/functions")
    print("2. Check if both functions are listed:")
    print("   - pg_query_output_to_gsheet")
    print("   - gsheet_to_database")
    print("3. Verify their status is 'Active'")
    print("4. Check the logs for any deployment errors")
    print("5. Verify the service accounts have proper permissions")
    print()

def main():
    print("🌐 Cloud Function Status Checker")
    print("=" * 50)

    check_function_deployment()
    check_google_cloud_console()

    print("📝 Troubleshooting Steps:")
    print("=" * 30)
    print("1. Check your GitHub Actions logs for deployment details")
    print("2. Verify the function URLs in Google Cloud Console")
    print("3. Check if the functions are in 'Active' state")
    print("4. Verify IAM permissions for the service account")
    print("5. Check function logs for runtime errors")

if __name__ == "__main__":
    main()
