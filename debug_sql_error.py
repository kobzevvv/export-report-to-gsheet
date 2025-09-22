#!/usr/bin/env python3
"""Debug the SQL transformation that's causing the function to fail"""

from json_unnesting import JsonUnnestingParser, JsonUnnestingTransformer

# Your exact query that's failing
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

print("=== Debugging SQL Transformation Bug ===")

parser = JsonUnnestingParser()
transformer = JsonUnnestingTransformer()

try:
    parse_result = parser.parse(test_query)
    print("✅ Parsing successful")
    print(f"Unnesting requests: {len(parse_result.get('unnesting_requests', []))}")
except Exception as e:
    print(f"❌ Parsing failed: {e}")
    exit(1)

try:
    transformed_sql = transformer.transform(test_query, parse_result.get("unnesting_requests", []))
    print("✅ Transformation successful")
except Exception as e:
    print(f"❌ Transformation failed: {e}")
    exit(1)

print("\n=== Checking SQL Syntax ===")
print("Length of transformed SQL:", len(transformed_sql))
print("Contains FROM clause:", "FROM public_marts.candidates" in transformed_sql)
print("Contains WHERE clause:", "WHERE position_name ILIKE" in transformed_sql)
print("Contains LIMIT clause:", "LIMIT 1" in transformed_sql)

# Check for potential SQL syntax issues that could cause execution to fail
print("\n=== Potential SQL Issues ===")

# Check SELECT clause structure
select_match = transformed_sql.find("SELECT ")
if select_match >= 0:
    select_section = transformed_sql[select_match:select_match+200]
    print("SELECT section preview:", select_section.replace('\n', ' '))

# Check for comma issues
if ",," in transformed_sql:
    print("❌ Double comma found - could cause SQL syntax error")

if "SELECT ," in transformed_sql:
    print("❌ SELECT with leading comma found")

if ", FROM" in transformed_sql:
    print("❌ Trailing comma before FROM found")

# Check for unbalanced quotes
single_quotes = transformed_sql.count("'")
double_quotes = transformed_sql.count('"')
print(f"Quote balance: {single_quotes} single quotes, {double_quotes} double quotes")

if single_quotes % 2 != 0:
    print("❌ Unbalanced single quotes detected!")

# Look for the specific regex issue in our SELECT parsing
try:
    import re
    select_match = re.search(r'SELECT\s+(.*?)\s+FROM', test_query, re.IGNORECASE | re.DOTALL)
    if select_match:
        original_select = select_match.group(1).strip()
        print(f"\nOriginal SELECT content: {repr(original_select[:100])}")
    else:
        print("❌ Could not extract SELECT clause from original query")
except Exception as e:
    print(f"❌ Regex error: {e}")

print(f"\n=== First 500 chars of transformed SQL ===")
print(transformed_sql[:500])
print("...")
