# Cleanup Checklist - Remove Email Fix from This Repository

Since the email extraction fix belongs in a different repository, here's what needs to be cleaned up from this repository:

## 🗑️ Files to Remove/Revert

### Modified Files (Revert Changes)
- [ ] `json_unnesting.py` - Revert "Try 2" enhancement back to `NULL`
- [ ] `json_extraction/strategies/direct_field_strategy.py` - Revert to disabled state
- [ ] `cloud_function/json_unnesting.py` - Revert to original
- [ ] `cloud_function_gsheet_to_database/json_unnesting.py` - Revert to original
- [ ] `cloud_function/strategies/direct_field_strategy.py` - Revert to original
- [ ] `cloud_function_gsheet_to_database/strategies/direct_field_strategy.py` - Revert to original

### New Files (Delete)
- [ ] `json_extraction/strategies/hidden_field_strategy.py`
- [ ] `cloud_function/strategies/hidden_field_strategy.py`
- [ ] `cloud_function_gsheet_to_database/strategies/hidden_field_strategy.py`
- [ ] `deploy_email_fix.py`
- [ ] `DEPLOYMENT_SUMMARY.md`
- [ ] `EMAIL_FIX_COMPLETE.md`

### Backup Directory (Keep for Reference)
- [ ] `email_fix_backup/` - Keep this for reference when implementing in correct repo

### Documentation (Keep)
- [ ] `README_CANDIDATE_EMAIL_FIX_BRANCH.md` - Keep as implementation guide

## 🔄 Git Operations

### Option 1: Reset Branch (Clean Slate)
```bash
# Reset this branch to before email fix changes
git reset --hard <commit_before_email_fix>
git push --force-with-lease origin candidate-email-fix
```

### Option 2: Revert Commits (Preserve History)
```bash
# Revert the email fix commits
git revert <email_fix_commit_hash>
git push origin candidate-email-fix
```

### Option 3: Keep Branch for Reference
- Don't merge this branch to main
- Use it as reference for implementing in correct repository
- Delete branch after successful implementation elsewhere

## ✅ What to Keep

### Implementation Guide
- [ ] `README_CANDIDATE_EMAIL_FIX_BRANCH.md` - Complete implementation guide
- [ ] `email_fix_backup/` - Reference SQL queries and documentation

### Key Learnings
1. **Column Name**: Use `input_json_as_is` not `answers_json`
2. **Strategy**: Check hidden fields FIRST, then fallback
3. **SQL Pattern**: `json_column->'hidden'->>'email'` is the key
4. **Backward Compatibility**: Always use COALESCE for graceful fallback

## 📋 Next Steps

1. [ ] Save `README_CANDIDATE_EMAIL_FIX_BRANCH.md` to safe location
2. [ ] Copy `email_fix_backup/` folder to safe location  
3. [ ] Clean up this repository (revert changes)
4. [ ] Implement solution in correct repository using the guide
5. [ ] Test in correct repository
6. [ ] Delete this branch after successful implementation

## 🎯 Repository Purpose Reminder

This repository (`export-report-to-gsheet`) is for:
- Google Sheets ↔ Database integration
- SQL query execution and results export
- JSON unnesting for general report generation

The email extraction fix belongs in the repository that:
- Processes Typeform responses
- Manages candidate data
- Handles the `source_cloud_functions.typeform_responses` table

---
*Keep this checklist until cleanup is complete*
