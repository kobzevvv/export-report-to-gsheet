# Typeform Email Extraction Fix

## Problem
Some Typeform responses have empty `candidate_email` fields even though the email data exists in the JSON. This happens because emails are stored in the `hidden` field like:

```json
{
  "hidden": {
    "email": "alex.stav@mail.ru", 
    "first_name": "Александр"
  }
}
```

The current extraction logic doesn't check hidden fields, so these emails are missed.

## Solution
This fix provides:

1. **Enhanced extraction logic** that checks hidden fields first
2. **Backward compatibility** with existing extraction patterns
3. **Safe update queries** to fix existing empty records
4. **Monitoring queries** to track extraction success

## Quick Start

### Step 1: Test Current State
Run the test query to see which records can be fixed:
```bash
# This shows current vs enhanced extraction
psql -f 01_test_email_extraction_*.sql
```

### Step 2: Count Affected Records  
```bash
# See how many records need updating
psql -f 02_count_analysis_*.sql
```

### Step 3: Fix Missing Emails
```bash
# ⚠️ This modifies data - backup first!
psql -f 04_fix_missing_emails_*.sql
```

### Step 4: Verify Results
```bash
# Confirm the fix worked
psql -f 05_verify_results_*.sql
```

## Files Generated

| File | Purpose | Safe to Run |
|------|---------|-------------|
| `01_test_email_extraction_*.sql` | Compare current vs enhanced extraction | ✅ Yes (read-only) |
| `02_count_analysis_*.sql` | Count records needing updates | ✅ Yes (read-only) |
| `03_sample_typeform_data_*.sql` | Inspect typeform JSON structure | ✅ Yes (read-only) |
| `04_fix_missing_emails_*.sql` | **Update missing emails** | ⚠️ **Modifies data!** |
| `05_verify_results_*.sql` | Verify fix results | ✅ Yes (read-only) |

## Enhanced Extraction Logic

The new extraction logic tries these strategies in order:

1. **Hidden fields** (PRIMARY for Typeform): `answers_json->'hidden'->>'email'`
2. **Direct field access**: `answers_json->>'email'`  
3. **Nested list structure** (existing): Pattern matching in arrays
4. **Email pattern matching**: Regex search for email formats
5. **Deep search**: Look anywhere in JSON for email patterns

## Integration

### For Existing Code
Update your JSON extraction logic to check hidden fields first:

```sql
-- OLD (misses hidden emails)
COALESCE(
  -- Try nested list only
  (SELECT item->>'value_text' FROM jsonb_array_elements(...) ...)
)

-- NEW (includes hidden fields)  
COALESCE(
  -- Try hidden fields first
  answers_json->'hidden'->>'email',
  -- Then try existing patterns
  (SELECT item->>'value_text' FROM jsonb_array_elements(...) ...)
)
```

### For New Typeform Processing
Always check hidden fields first in your extraction pipeline. The enhanced SQL provides a complete solution.

## Safety Notes

- ⚠️ **Backup your data** before running UPDATE queries
- The update only affects records with empty `candidate_email`
- Run in a transaction: `BEGIN; UPDATE...; COMMIT;`
- Test queries are read-only and safe to run anytime

## Monitoring

Run the count analysis query periodically to ensure email extraction is working:

```sql
-- Quick health check
SELECT 
  COUNT(*) as total,
  COUNT(CASE WHEN candidate_email = '' THEN 1 END) as missing_emails,
  COUNT(CASE WHEN answers_json->'hidden'->>'email' IS NOT NULL THEN 1 END) as has_hidden_email
FROM source_cloud_functions.typeform_responses
WHERE created_at > NOW() - INTERVAL '7 days';
```

## Scripts

- `fix_typeform_email_extraction.py` - Basic fix script
- `fix_typeform_emails_comprehensive.py` - Complete solution with all queries

Run either script to generate the SQL files:
```bash
python3 fix_typeform_emails_comprehensive.py
```

## Results Expected

After running the fix:
- Empty `candidate_email` fields will be populated from hidden data
- New Typeform responses will extract emails correctly
- Data quality improves for candidate tracking
- No existing good data is modified

---

**Need help?** The generated SQL files include detailed comments and safety checks.
