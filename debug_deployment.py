#!/usr/bin/env python3
"""
Debug script to test cloud function deployment issues locally.
This helps identify potential issues before deployment.
"""

import os
import sys

def check_deployment_requirements():
    """Check if all deployment requirements are met"""

    print("🔍 Deployment Requirements Check")
    print("=" * 50)

    issues = []

    # Check if gcloud is installed
    import subprocess
    try:
        result = subprocess.run(['gcloud', '--version'], capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ gcloud CLI is installed")
            print(f"   Version: {result.stdout.strip()}")
        else:
            issues.append("❌ gcloud CLI not found or not working")
    except FileNotFoundError:
        issues.append("❌ gcloud CLI not installed")

    # Check cloud function directories
    cloud_function_dirs = [
        'cloud_function',
        'cloud_function_gsheet_to_database'
    ]

    for dir_name in cloud_function_dirs:
        if os.path.exists(dir_name):
            print(f"✅ {dir_name} directory exists")
            contents = os.listdir(dir_name)
            print(f"   Contents: {', '.join(contents)}")

            # Check for main.py
            if 'main.py' in contents:
                print(f"   ✅ main.py found in {dir_name}")
            else:
                issues.append(f"❌ main.py not found in {dir_name}")

            # Check for json_unnesting.py
            if 'json_unnesting.py' in contents:
                print(f"   ✅ json_unnesting.py found in {dir_name}")
            else:
                issues.append(f"❌ json_unnesting.py not found in {dir_name}")

            # Check for requirements.txt
            if 'requirements.txt' in contents:
                print(f"   ✅ requirements.txt found in {dir_name}")
            else:
                issues.append(f"❌ requirements.txt not found in {dir_name}")
        else:
            issues.append(f"❌ {dir_name} directory not found")

    # Check Python files syntax
    for dir_name in cloud_function_dirs:
        main_py = f"{dir_name}/main.py"
        if os.path.exists(main_py):
            try:
                with open(main_py, 'r') as f:
                    compile(f.read(), main_py, 'exec')
                print(f"✅ {main_py} syntax is valid")
            except SyntaxError as e:
                issues.append(f"❌ {main_py} has syntax error: {e}")

    # Check json_unnesting.py syntax
    json_unnesting_py = 'json_unnesting.py'
    if os.path.exists(json_unnesting_py):
        try:
            with open(json_unnesting_py, 'r') as f:
                compile(f.read(), json_unnesting_py, 'exec')
            print(f"✅ {json_unnesting_py} syntax is valid")
        except SyntaxError as e:
            issues.append(f"❌ {json_unnesting_py} has syntax error: {e}")

    # Check workflow file
    workflow_file = '.github/workflows/deploy-and-test.yml'
    if os.path.exists(workflow_file):
        print(f"✅ {workflow_file} exists")
    else:
        issues.append(f"❌ {workflow_file} not found")

    print("\n" + "=" * 50)

    if issues:
        print("❌ Issues Found:")
        for issue in issues:
            print(f"   {issue}")
        return False
    else:
        print("✅ All requirements met!")
        return True

def main():
    print("🧪 Cloud Function Deployment Debug Tool")
    print("=" * 50)

    success = check_deployment_requirements()

    print("\n" + "=" * 50)
    print("📝 Next Steps:")
    if success:
        print("1. Check your GitHub Actions workflow logs")
        print("2. Verify your GitHub secrets are set correctly")
        print("3. Monitor the deployment in Google Cloud Console")
    else:
        print("1. Fix the issues listed above")
        print("2. Test deployment again")
        print("3. Check GitHub Actions logs for detailed errors")

if __name__ == "__main__":
    main()
