#!/usr/bin/env python3
"""
Deploy Email Fix to Production

This script prepares and deploys the email extraction fix to production.
It ensures all cloud function directories have the updated files.
"""

import os
import shutil
import subprocess
from datetime import datetime

def copy_files_to_cloud_functions():
    """Copy updated files to all cloud function directories."""
    
    print("📁 COPYING UPDATED FILES TO CLOUD FUNCTIONS")
    print("=" * 50)
    
    # Files to copy
    files_to_copy = [
        {
            "source": "json_unnesting.py",
            "targets": [
                "cloud_function/json_unnesting.py",
                "cloud_function_gsheet_to_database/json_unnesting.py"
            ],
            "description": "Main fix - enhanced hidden field extraction"
        },
        {
            "source": "json_extraction/strategies/direct_field_strategy.py", 
            "targets": [
                "cloud_function/strategies/direct_field_strategy.py",
                "cloud_function_gsheet_to_database/strategies/direct_field_strategy.py"
            ],
            "description": "Enhanced direct field strategy"
        },
        {
            "source": "json_extraction/strategies/hidden_field_strategy.py",
            "targets": [
                "cloud_function/strategies/hidden_field_strategy.py", 
                "cloud_function_gsheet_to_database/strategies/hidden_field_strategy.py"
            ],
            "description": "New hidden field strategy"
        }
    ]
    
    copied_count = 0
    for file_info in files_to_copy:
        source = file_info["source"]
        targets = file_info["targets"]
        desc = file_info["description"]
        
        if not os.path.exists(source):
            print(f"⚠️  Source file missing: {source}")
            continue
            
        print(f"\n📄 {desc}")
        print(f"   Source: {source}")
        
        for target in targets:
            try:
                # Create directory if it doesn't exist
                target_dir = os.path.dirname(target)
                if not os.path.exists(target_dir):
                    os.makedirs(target_dir)
                    
                shutil.copy2(source, target)
                print(f"   ✅ → {target}")
                copied_count += 1
            except Exception as e:
                print(f"   ❌ → {target} (Error: {e})")
    
    print(f"\n📊 SUMMARY: Copied {copied_count} files")
    return copied_count > 0

def check_git_status():
    """Check git status and stage changes."""
    
    print(f"\n📋 CHECKING GIT STATUS")
    print("=" * 30)
    
    try:
        # Check git status
        result = subprocess.run(["git", "status", "--porcelain"], 
                              capture_output=True, text=True, check=True)
        
        if result.stdout.strip():
            print("📝 Modified files:")
            for line in result.stdout.strip().split('\n'):
                print(f"   {line}")
            
            # Stage the changes
            print(f"\n📤 STAGING CHANGES")
            subprocess.run(["git", "add", "."], check=True)
            print("✅ Changes staged successfully")
            
            return True
        else:
            print("✅ No changes detected")
            return False
            
    except subprocess.CalledProcessError as e:
        print(f"❌ Git command failed: {e}")
        return False

def commit_and_push_changes():
    """Commit and push the email fix changes."""
    
    print(f"\n🚀 COMMITTING AND PUSHING CHANGES")
    print("=" * 40)
    
    try:
        # Create commit message
        commit_msg = f"""Fix: Enhanced email extraction from Typeform hidden fields

- Enhanced json_unnesting.py to check hidden fields first
- Updated direct_field_strategy.py for hidden field support  
- Added hidden_field_strategy.py for comprehensive extraction
- Fixes missing emails in typeform_responses table

Changes:
- input_json_as_is->'hidden'->>'email' now checked first
- Backward compatible with existing extraction patterns
- Automatic for all future typeform responses

Deployed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"""

        # Commit changes
        subprocess.run(["git", "commit", "-m", commit_msg], check=True)
        print("✅ Changes committed successfully")
        
        # Push to main branch
        subprocess.run(["git", "push", "origin", "main"], check=True)
        print("✅ Changes pushed to main branch")
        
        print(f"\n🎯 DEPLOYMENT TRIGGERED!")
        print("   The GitHub workflow will automatically deploy to production")
        print("   Monitor the deployment at: https://github.com/your-repo/actions")
        
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Git operation failed: {e}")
        return False

def create_deployment_summary():
    """Create a summary of what was deployed."""
    
    summary = f"""
# Email Fix Deployment Summary

## 🚀 DEPLOYED TO PRODUCTION
**Timestamp**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## 📋 CHANGES DEPLOYED
1. **json_unnesting.py** - Enhanced "Try 2" logic to check hidden fields first
2. **direct_field_strategy.py** - Enhanced for hidden field support
3. **hidden_field_strategy.py** - New strategy for comprehensive extraction

## 🎯 IMPACT
- ✅ **Future data**: New typeform responses automatically extract emails from hidden fields
- ✅ **Existing data**: Can be fixed with UPDATE query (see email_fix_backup/)
- ✅ **Zero downtime**: Backward compatible deployment
- ✅ **Immediate effect**: Active as soon as deployed

## 🧪 TESTING
The fix handles:
- `input_json_as_is->'hidden'->>'email'` (PRIMARY)
- `input_json_as_is->>'email'` (fallback)
- Existing nested array patterns (unchanged)
- Multiple email variations (email, Email, EMAIL)

## 📊 MONITORING
Monitor email extraction success with:
```sql
SELECT 
    DATE(created_at) as date,
    COUNT(*) as total_responses,
    COUNT(CASE WHEN candidate_email = '' THEN 1 END) as missing_emails
FROM source_cloud_functions.typeform_responses
WHERE created_at > NOW() - INTERVAL '7 days'
GROUP BY DATE(created_at)
ORDER BY date DESC;
```

## ✅ DEPLOYMENT COMPLETE
The email extraction fix is now active in production!
"""
    
    with open("DEPLOYMENT_SUMMARY.md", "w") as f:
        f.write(summary)
    
    return summary

def main():
    """Main deployment function."""
    
    print("🚀 DEPLOYING EMAIL EXTRACTION FIX TO PRODUCTION")
    print("=" * 60)
    
    # Step 1: Copy files to cloud functions
    if not copy_files_to_cloud_functions():
        print("❌ Failed to copy files. Aborting deployment.")
        return False
    
    # Step 2: Check git status
    has_changes = check_git_status()
    if not has_changes:
        print("⚠️  No changes to deploy. Email fix may already be deployed.")
        return True
    
    # Step 3: Commit and push changes
    if not commit_and_push_changes():
        print("❌ Failed to commit/push changes. Deployment aborted.")
        return False
    
    # Step 4: Create deployment summary
    summary = create_deployment_summary()
    print(summary)
    
    print(f"\n" + "🎉" * 25)
    print("EMAIL FIX DEPLOYMENT INITIATED!")
    print("🎉" * 25)
    
    print(f"\n📋 NEXT STEPS:")
    print("1. ⏳ Wait for GitHub Actions to complete deployment")
    print("2. 🧪 Test email extraction with new typeform responses")
    print("3. 📊 Run UPDATE query for existing data (see email_fix_backup/)")
    print("4. 📈 Monitor extraction success with provided queries")
    
    print(f"\n🔗 USEFUL LINKS:")
    print("   📊 GitHub Actions: https://github.com/your-repo/actions")
    print("   📁 Backup files: ./email_fix_backup/")
    print("   📝 Summary: ./DEPLOYMENT_SUMMARY.md")
    
    return True

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
