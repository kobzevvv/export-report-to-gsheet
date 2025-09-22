#!/usr/bin/env python3
"""Debug WHERE clause extraction issue"""

import re

test_query = """SELECT 
candidate_email,
weighted_values,
interview_shared_link,

{{fields_as_columns_from(answers_json, question_title, value_text, 
"Город проживания", 
"Ваше имя")}},

first_answer_datetime

FROM public_marts.candidates
WHERE position_name ILIKE '%додо%'
LIMIT 1"""

print("=== Testing WHERE Clause Extraction ===")

# Test our regex patterns
from_match = re.search(r'FROM\s+([^\s]+)', test_query, re.IGNORECASE)
if from_match:
    table_name = from_match.group(1)
    print(f"✅ Table name extracted: {table_name}")
else:
    print("❌ Could not extract table name")

# This is the regex we're using in our code
where_match = re.search(r'\bWHERE\b(.+)', test_query, re.IGNORECASE | re.DOTALL)
if where_match:
    where_clause = where_match.group(1).strip()
    print(f"✅ WHERE clause extracted: {repr(where_clause)}")
else:
    print("❌ Could not extract WHERE clause")

# Check what happens when we construct the WHERE part
if where_match:
    where_part = f"WHERE {where_clause}"
    print(f"Final WHERE part: {repr(where_part)}")

print("\n=== SELECT Clause Extraction ===")
select_match = re.search(r'SELECT\s+(.*?)\s+FROM', test_query, re.IGNORECASE | re.DOTALL)
if select_match:
    original_select = select_match.group(1).strip()
    print(f"✅ SELECT content: {repr(original_select[:200])}")
    
    # Check if there are any issues with template replacement
    template_pattern = r'\{\{fields_as_columns_from\([^}]+\)\}\}'
    if re.search(template_pattern, original_select):
        print("✅ Template syntax found in SELECT")
        
        # Simulate template replacement
        replaced = re.sub(template_pattern, "REPLACED_CONTENT", original_select)
        print(f"After replacement preview: {repr(replaced[:200])}")
    else:
        print("❌ Template syntax NOT found in SELECT")
else:
    print("❌ Could not extract SELECT clause")

print(f"\n=== Full Query Analysis ===")
print(f"Query length: {len(test_query)}")
print(f"Contains FROM: {'FROM' in test_query}")
print(f"Contains WHERE: {'WHERE' in test_query}")
print(f"Contains LIMIT: {'LIMIT' in test_query}")
